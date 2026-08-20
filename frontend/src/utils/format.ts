import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";
import type { CaseStage, CaseState, Evidence } from "@/types";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatPercent(value: number, digits = 0): string {
  return `${(value * 100).toFixed(digits)}%`;
}

export function formatUsd(value: number, digits = 3): string {
  return `$${value.toFixed(digits)}`;
}

export function formatMs(value: number): string {
  if (value >= 1000) return `${(value / 1000).toFixed(1)}s`;
  return `${Math.round(value)}ms`;
}

export function formatNumber(value: number, digits = 1): string {
  if (Number.isInteger(value)) return String(value);
  return value.toFixed(digits);
}

export function formatDateTime(value: string | null | undefined): string {
  if (!value) return "—";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleString(undefined, {
    year: "numeric",
    month: "short",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  });
}

export function shortId(id: string, size = 8): string {
  if (id.length <= size + 2) return id;
  return `${id.slice(0, size)}…`;
}

export function copyToClipboard(text: string): Promise<void> {
  return navigator.clipboard.writeText(text);
}

export const STAGE_ORDER: CaseStage[] = [
  "NEW",
  "INVESTIGATING",
  "PLANNING",
  "REVIEW",
  "AWAITING_APPROVAL",
  "EXECUTING",
  "VERIFYING",
  "RESOLVED",
  "ESCALATED",
  "FAILED",
];

export const STAGE_COLORS: Record<CaseStage, string> = {
  NEW: "bg-slate-500/20 text-slate-300 border-slate-500/30",
  INVESTIGATING: "bg-violet-500/20 text-violet-300 border-violet-500/30",
  PLANNING: "bg-indigo-500/20 text-indigo-300 border-indigo-500/30",
  REVIEW: "bg-purple-500/20 text-purple-300 border-purple-500/30",
  AWAITING_APPROVAL: "bg-amber-500/20 text-amber-300 border-amber-500/30",
  EXECUTING: "bg-orange-500/20 text-orange-300 border-orange-500/30",
  VERIFYING: "bg-sky-500/20 text-sky-300 border-sky-500/30",
  RESOLVED: "bg-emerald-500/20 text-emerald-300 border-emerald-500/30",
  ESCALATED: "bg-amber-500/25 text-amber-200 border-amber-500/40",
  FAILED: "bg-rose-500/20 text-rose-300 border-rose-500/30",
};

export const SOURCE_COLORS: Record<string, string> = {
  CRM: "border-sky-500/40 bg-sky-500/10 text-sky-200",
  BILLING: "border-amber-500/40 bg-amber-500/10 text-amber-200",
  POLICY: "border-violet-500/40 bg-violet-500/10 text-violet-200",
  USER: "border-slate-500/40 bg-slate-500/10 text-slate-200",
};

export const VARIANT_LABELS: Record<string, string> = {
  multi_agent: "Multi-Agent",
  single_agent: "Single Agent",
  no_reviewer: "No Reviewer",
};

export function totalTokens(caseState: Pick<
  CaseState,
  "input_tokens" | "tool_input_tokens" | "output_tokens" | "thinking_tokens"
>): number {
  return (
    caseState.input_tokens +
    caseState.tool_input_tokens +
    caseState.output_tokens +
    caseState.thinking_tokens
  );
}

export function isMutationTool(toolName: string): boolean {
  return [
    "match_payment",
    "remove_account_hold",
    "restore_crm_account",
    "set_account_status",
  ].some((name) => toolName.includes(name));
}

export function isReadTool(toolName: string): boolean {
  return (
    toolName.startsWith("get_") ||
    toolName.startsWith("search_") ||
    toolName.startsWith("list_") ||
    toolName.includes("retrieve")
  );
}

export interface PipelineNodeStatus {
  id: string;
  label: string;
  status: "completed" | "active" | "skipped" | "failed" | "pending" | "escalated";
  detail: string;
  section: string;
}

export function buildPipeline(caseState: CaseState): PipelineNodeStatus[] {
  const stage = caseState.stage;
  const escalated = stage === "ESCALATED";
  const failed = stage === "FAILED";

  const investigatorDone =
    caseState.evidence.length > 0 ||
    Boolean(caseState.root_cause) ||
    [
      "PLANNING",
      "REVIEW",
      "AWAITING_APPROVAL",
      "EXECUTING",
      "VERIFYING",
      "RESOLVED",
      "ESCALATED",
      "FAILED",
    ].includes(stage);

  const plannerDone = Boolean(caseState.resolution_plan);
  const reviewerDone = Boolean(caseState.review);
  const approvalDone =
    caseState.approval?.decision === "APPROVED" ||
    caseState.approval?.decision === "REJECTED";
  const executorDone = caseState.executed_actions.length > 0;
  const verifyDone = Boolean(caseState.verification);

  const nodes: PipelineNodeStatus[] = [
    {
      id: "case",
      label: "Case",
      status: "completed",
      detail: caseState.customer_id,
      section: "overview",
    },
    {
      id: "investigator",
      label: "Investigator",
      status: investigatorDone
        ? caseState.root_cause
          ? "completed"
          : escalated && !plannerDone
            ? "escalated"
            : "completed"
        : stage === "INVESTIGATING"
          ? "active"
          : stage === "NEW"
            ? "pending"
            : failed
              ? "failed"
              : "pending",
      detail: caseState.root_cause
        ? "Root cause found"
        : caseState.evidence.length
          ? `${caseState.evidence.length} evidence items`
          : stage === "INVESTIGATING"
            ? "Investigating…"
            : "Not started",
      section: "evidence",
    },
    {
      id: "planner",
      label: "Planner",
      status: plannerDone
        ? "completed"
        : escalated && investigatorDone && !plannerDone
          ? "escalated"
          : stage === "PLANNING"
            ? "active"
            : "pending",
      detail: plannerDone
        ? `${caseState.resolution_plan!.actions.length} action${
            caseState.resolution_plan!.actions.length === 1 ? "" : "s"
          } proposed`
        : escalated && !plannerDone
          ? "Unsafe / insufficient evidence"
          : stage === "PLANNING"
            ? "Planning…"
            : "Not started",
      section: "plan",
    },
    {
      id: "reviewer",
      label: "Reviewer",
      status: reviewerDone
        ? caseState.review?.verdict === "ESCALATE"
          ? "escalated"
          : caseState.review?.verdict === "REVISE"
            ? "active"
            : "completed"
        : escalated && !reviewerDone
          ? "skipped"
          : stage === "REVIEW"
            ? "active"
            : plannerDone
              ? "pending"
              : "skipped",
      detail: reviewerDone
        ? caseState.review!.verdict
        : escalated && !reviewerDone
          ? "Skipped"
          : stage === "REVIEW"
            ? "Reviewing…"
            : plannerDone
              ? "Waiting"
              : "—",
      section: "review",
    },
    {
      id: "approval",
      label: "Human Approval",
      status: approvalDone
        ? caseState.approval?.decision === "APPROVED"
          ? "completed"
          : "failed"
        : stage === "AWAITING_APPROVAL"
          ? "active"
          : escalated || (!plannerDone && escalated)
            ? "skipped"
            : "pending",
      detail: approvalDone
        ? caseState.approval!.decision
        : stage === "AWAITING_APPROVAL"
          ? "Awaiting operator"
          : escalated
            ? "Skipped"
            : "Not started",
      section: "overview",
    },
    {
      id: "executor",
      label: "Executor",
      status: executorDone
        ? caseState.executed_actions.some((a) => a.status === "FAILED")
          ? "failed"
          : "completed"
        : stage === "EXECUTING"
          ? "active"
          : escalated
            ? "skipped"
            : "pending",
      detail: executorDone
        ? `${caseState.executed_actions.length} actions executed`
        : stage === "EXECUTING"
          ? "Executing…"
          : escalated
            ? "Skipped"
            : "Not started",
      section: "execution",
    },
    {
      id: "verification",
      label: "Verification",
      status: verifyDone
        ? caseState.verification!.success
          ? "completed"
          : "failed"
        : stage === "VERIFYING"
          ? "active"
          : stage === "RESOLVED"
            ? "completed"
            : escalated
              ? "skipped"
              : "pending",
      detail: verifyDone
        ? caseState.verification!.success
          ? "Checks passed"
          : "Checks failed"
        : stage === "RESOLVED"
          ? "RESOLVED"
          : escalated
            ? "ESCALATED"
            : failed
              ? "FAILED"
              : "Not started",
      section: "verification",
    },
  ];

  return nodes;
}

export function inferEvidenceGraph(evidence: Evidence[]): Array<{
  id: string;
  label: string;
  source?: string;
}> {
  const nodes: Array<{ id: string; label: string; source?: string }> = [];
  const seen = new Set<string>();

  const push = (id: string, label: string, source?: string) => {
    if (seen.has(id)) return;
    seen.add(id);
    nodes.push({ id, label, source });
  };

  for (const item of evidence) {
    const d = item.details;
    if (typeof d.customer_id === "string") {
      push(`customer:${d.customer_id}`, `Customer ${d.customer_id}`, item.source);
    }
    if (typeof d.account_id === "string") {
      push(`account:${d.account_id}`, `Account ${d.account_id}`, item.source);
    }
    if (typeof d.invoice_id === "string") {
      push(`invoice:${d.invoice_id}`, `Invoice ${d.invoice_id}`, item.source);
    }
    if (typeof d.source_invoice_id === "string") {
      push(
        `legacy:${d.source_invoice_id}`,
        `Legacy ${d.source_invoice_id}`,
        item.source,
      );
    }
    if (typeof d.payment_id === "string") {
      push(`payment:${d.payment_id}`, `Payment ${d.payment_id}`, item.source);
    }
    if (typeof d.hold_code === "string") {
      push(`hold:${d.hold_code}`, `Hold ${d.hold_code}`, item.source);
    }
    if (typeof d.document_id === "string") {
      push(`policy:${d.document_id}`, `Policy ${d.document_id}`, item.source);
    }
  }

  return nodes;
}

export function extractAcmeIdentifiers(caseState: CaseState): {
  legacyInvoice?: string;
  canonicalInvoice?: string;
  paymentReference?: string;
  paymentId?: string;
  paymentStatus?: string;
} | null {
  if (caseState.customer_id !== "ACME") return null;

  let legacyInvoice: string | undefined;
  let canonicalInvoice: string | undefined;
  let paymentReference: string | undefined;
  let paymentId: string | undefined;
  let paymentStatus: string | undefined;

  for (const item of caseState.evidence) {
    const d = item.details;
    if (typeof d.source_invoice_id === "string") legacyInvoice = d.source_invoice_id;
    if (typeof d.invoice_id === "string") canonicalInvoice = d.invoice_id;
    if (typeof d.invoice_reference === "string") paymentReference = d.invoice_reference;
    if (typeof d.payment_id === "string") paymentId = d.payment_id;
    if (typeof d.status === "string" && d.payment_id) paymentStatus = d.status;
  }

  if (!legacyInvoice && !canonicalInvoice && !paymentId) return null;

  return {
    legacyInvoice,
    canonicalInvoice,
    paymentReference,
    paymentId,
    paymentStatus,
  };
}
