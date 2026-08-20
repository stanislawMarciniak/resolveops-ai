import { useMemo, useState } from "react";
import { Link, useParams } from "react-router-dom";
import {
  AlertTriangle,
  ArrowDown,
  CheckCircle2,
  Clock3,
  ShieldAlert,
  XCircle,
} from "lucide-react";
import { api } from "@/api/client";
import { useAsync } from "@/hooks/useAsync";
import { Breadcrumbs } from "@/components/layout/Breadcrumbs";
import { CasePipeline } from "@/components/diagrams/CasePipeline";
import { EvidenceCard } from "@/components/cases/EvidenceCard";
import { HypothesisCard } from "@/components/cases/HypothesisCard";
import { PlanActionCard } from "@/components/cases/PlanActionCard";
import { StageBadge } from "@/components/ui/StageBadge";
import { MetricCard } from "@/components/ui/MetricCard";
import { JsonViewer } from "@/components/ui/JsonViewer";
import { CopyButton } from "@/components/ui/CopyButton";
import { PageSkeleton } from "@/components/ui/Skeleton";
import { ErrorPanel } from "@/components/ui/ErrorPanel";
import type { CaseState } from "@/types";
import {
  extractAcmeIdentifiers,
  formatDateTime,
  formatMs,
  formatUsd,
  inferEvidenceGraph,
  isMutationTool,
  isReadTool,
  totalTokens,
} from "@/utils/format";

const TABS = [
  "Overview",
  "Timeline",
  "Evidence",
  "Plan",
  "Review",
  "Execution",
  "Verification",
  "Raw State",
] as const;

type Tab = (typeof TABS)[number];

export function CaseDetailPage() {
  const { caseId = "" } = useParams();
  const [tab, setTab] = useState<Tab>("Overview");
  const [actionError, setActionError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const query = useAsync(() => api.getCase(caseId), [caseId]);

  const onSelectSection = (section: string) => {
    const map: Record<string, Tab> = {
      overview: "Overview",
      evidence: "Evidence",
      plan: "Plan",
      review: "Review",
      execution: "Execution",
      verification: "Verification",
    };
    setTab(map[section] ?? "Overview");
  };

  const runAction = async (kind: "approve" | "reject") => {
    setBusy(true);
    setActionError(null);
    try {
      await api.decideApproval(
        caseId,
        kind === "approve" ? "APPROVED" : "REJECTED",
      );
      query.reload();
    } catch (err) {
      setActionError(err instanceof Error ? err.message : "Action failed");
    } finally {
      setBusy(false);
    }
  };

  if (query.loading) return <PageSkeleton />;
  if (query.error || !query.data) {
    return (
      <ErrorPanel
        title="Case not found"
        message={query.error ?? "Missing case"}
        onRetry={query.reload}
      />
    );
  }

  const state = query.data;

  return (
    <div className="fade-in space-y-5">
      <Breadcrumbs
        items={[
          { label: "Cases", to: "/cases" },
          { label: state.customer_id },
          { label: "Case Explorer" },
        ]}
      />

      <header className="panel sticky top-0 z-20 space-y-4 border-b border-white/10 bg-surface-900/95 p-5 backdrop-blur">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div className="min-w-0">
            <div className="flex flex-wrap items-center gap-2">
              <h1 className="text-display text-2xl font-semibold text-slate-50">
                {state.customer_id}
              </h1>
              <StageBadge stage={state.stage} />
            </div>
            <div className="mt-2 flex flex-wrap items-center gap-2 text-xs text-slate-400">
              <span className="mono text-violet-300">{state.case_id}</span>
              <CopyButton value={state.case_id} />
              <Link
                to={`/showcase/${state.customer_id.toLowerCase()}-01`}
                className="text-slate-400 hover:text-slate-200"
              >
                Compare eval variants →
              </Link>
            </div>
            <p className="mt-3 max-w-3xl text-sm leading-relaxed text-slate-300">
              {state.description}
            </p>
          </div>
        </div>

        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-5">
          <MetricCard label="Cost" value={formatUsd(state.estimated_cost_usd)} accent="slate" />
          <MetricCard label="Model calls" value={state.model_calls} accent="violet" />
          <MetricCard label="Tool calls" value={state.tool_calls} accent="blue" />
          <MetricCard label="Latency" value={formatMs(state.llm_latency_ms)} accent="amber" />
          <MetricCard label="Tokens" value={totalTokens(state)} accent="slate" />
        </div>

        <div className="flex flex-wrap gap-1">
          {TABS.map((item) => (
            <button
              key={item}
              type="button"
              onClick={() => setTab(item)}
              className={
                tab === item
                  ? "rounded-md bg-violet-500/20 px-3 py-1.5 text-xs font-medium text-violet-100"
                  : "rounded-md px-3 py-1.5 text-xs text-slate-400 hover:bg-white/5 hover:text-slate-200"
              }
            >
              {item}
            </button>
          ))}
        </div>
      </header>

      {state.stage === "AWAITING_APPROVAL" ? (
        <ApprovalPanel
          state={state}
          busy={busy}
          error={actionError}
          onApprove={() => void runAction("approve")}
          onReject={() => void runAction("reject")}
        />
      ) : null}

      {tab === "Overview" ? (
        <OverviewTab state={state} onSelect={onSelectSection} />
      ) : null}
      {tab === "Timeline" ? <TimelineTab state={state} /> : null}
      {tab === "Evidence" ? <EvidenceTab state={state} /> : null}
      {tab === "Plan" ? <PlanTab state={state} /> : null}
      {tab === "Review" ? <ReviewTab state={state} /> : null}
      {tab === "Execution" ? <ExecutionTab state={state} /> : null}
      {tab === "Verification" ? <VerificationTab state={state} /> : null}
      {tab === "Raw State" ? <JsonViewer data={state} title="CaseState" /> : null}
    </div>
  );
}

function ApprovalPanel({
  state,
  busy,
  error,
  onApprove,
  onReject,
}: {
  state: CaseState;
  busy: boolean;
  error: string | null;
  onApprove: () => void;
  onReject: () => void;
}) {
  return (
    <div className="panel border-amber-500/30 bg-amber-500/8 p-5">
      <div className="flex items-start gap-3">
        <ShieldAlert className="mt-0.5 h-5 w-5 text-amber-300" />
        <div className="flex-1">
          <h2 className="text-display text-lg font-semibold text-amber-50">
            Human approval required
          </h2>
          <p className="mt-1 text-sm text-amber-100/80">
            Approving will allow deterministic execution of enterprise mutations.
            Rejecting escalates / blocks the plan.
          </p>
          <div className="mt-3 grid gap-2 text-sm text-slate-200 md:grid-cols-2">
            <div>
              <span className="text-slate-400">Risk:</span>{" "}
              {state.resolution_plan?.risk ?? "—"}
            </div>
            <div>
              <span className="text-slate-400">Reviewer:</span>{" "}
              {state.review?.verdict ?? "—"}
            </div>
            <div className="md:col-span-2">
              <span className="text-slate-400">Plan digest:</span>{" "}
              <span className="mono text-xs">{state.approval?.plan_digest}</span>
            </div>
          </div>
          <ul className="mt-3 space-y-1 text-sm text-slate-300">
            {state.resolution_plan?.actions.map((action) => (
              <li key={`${action.tool_name}-${JSON.stringify(action.arguments)}`}>
                → {action.tool_name}{" "}
                <span className="text-slate-500">
                  {JSON.stringify(action.arguments)}
                </span>
              </li>
            ))}
          </ul>
          {error ? (
            <p className="mt-3 text-sm text-rose-300">
              {error} (operator auth may be required)
            </p>
          ) : null}
          <div className="mt-4 flex gap-2">
            <button
              type="button"
              disabled={busy}
              onClick={onApprove}
              className="rounded-lg bg-emerald-600 px-4 py-2 text-sm font-medium text-white hover:bg-emerald-500 disabled:opacity-50"
            >
              Approve
            </button>
            <button
              type="button"
              disabled={busy}
              onClick={onReject}
              className="rounded-lg border border-rose-400/30 bg-rose-500/10 px-4 py-2 text-sm font-medium text-rose-100 hover:bg-rose-500/20 disabled:opacity-50"
            >
              Reject
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

function OverviewTab({
  state,
  onSelect,
}: {
  state: CaseState;
  onSelect: (section: string) => void;
}) {
  const acme = extractAcmeIdentifiers(state);

  return (
    <div className="grid gap-4 xl:grid-cols-[320px_1fr]">
      <CasePipeline caseState={state} onSelect={onSelect} />
      <div className="space-y-4">
        <div className="panel border-violet-500/25 bg-gradient-to-br from-violet-500/15 to-transparent p-5">
          <div className="text-xs font-semibold uppercase tracking-[0.16em] text-violet-300">
            Root Cause
          </div>
          <p className="mt-3 text-sm leading-relaxed text-slate-100">
            {state.root_cause ?? "No root cause recorded for this case."}
          </p>
          <div className="mt-3 flex flex-wrap gap-3 text-xs text-slate-400">
            <span>{state.evidence.length} evidence items</span>
            {state.hypotheses[0] ? (
              <span>
                confidence {(state.hypotheses[0].confidence * 100).toFixed(0)}%
              </span>
            ) : null}
          </div>
        </div>

        {acme ? (
          <div className="panel p-5">
            <div className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">
              ACME identifier relationship
            </div>
            <div className="mt-4 flex flex-wrap items-center gap-2 text-sm">
              <IdChip label="Legacy invoice" value={acme.legacyInvoice} />
              <ArrowDown className="h-4 w-4 rotate-[-90deg] text-slate-500" />
              <IdChip label="Canonical invoice" value={acme.canonicalInvoice} />
              <ArrowDown className="h-4 w-4 rotate-[-90deg] text-slate-500" />
              <IdChip label="Payment reference" value={acme.paymentReference} />
              <ArrowDown className="h-4 w-4 rotate-[-90deg] text-slate-500" />
              <IdChip label="Payment" value={acme.paymentId} />
              <IdChip
                label="Status"
                value={
                  acme.paymentStatus
                    ? `${acme.paymentStatus}${
                        acme.paymentStatus === "RECEIVED" ? " / UNMATCHED" : ""
                      }`
                    : undefined
                }
              />
            </div>
          </div>
        ) : null}

        {state.hypotheses.length ? (
          <div className="space-y-3">
            <h3 className="text-display text-base font-semibold text-slate-100">
              Hypotheses
            </h3>
            {state.hypotheses.map((hypothesis) => (
              <HypothesisCard key={hypothesis.hypothesis_id} hypothesis={hypothesis} />
            ))}
          </div>
        ) : null}
      </div>
    </div>
  );
}

function IdChip({ label, value }: { label: string; value?: string }) {
  if (!value) return null;
  return (
    <div className="rounded-lg border border-white/10 bg-white/5 px-3 py-2">
      <div className="text-[10px] uppercase tracking-wider text-slate-500">{label}</div>
      <div className="mono text-violet-200">{value}</div>
    </div>
  );
}

function TimelineTab({ state }: { state: CaseState }) {
  const steps = useMemo(() => {
    const items: Array<{ title: string; detail?: string; at?: string }> = [
      { title: "Case created", at: state.created_at },
    ];

    if (state.evidence.length) {
      items.push({
        title: "Investigation evidence collected",
        detail: `${state.evidence.length} items`,
      });
    }
    if (state.root_cause) items.push({ title: "Root cause identified" });
    if (state.resolution_plan) {
      items.push({
        title: "Plan generated",
        detail: `${state.resolution_plan.actions.length} actions · risk ${state.resolution_plan.risk}`,
      });
    }
    if (state.review) {
      items.push({
        title: `Reviewer ${state.review.verdict}`,
        detail: state.review.summary,
      });
    }
    if (state.approval) {
      items.push({
        title: `Approval ${state.approval.decision}`,
        at: state.approval.decided_at ?? state.approval.created_at,
      });
    }
    for (const action of state.executed_actions) {
      items.push({
        title: `Executed ${action.tool_name}`,
        detail: action.result_summary ?? action.status,
        at: action.completed_at ?? action.started_at,
      });
    }
    if (state.verification) {
      items.push({
        title: state.verification.success
          ? "Verification passed"
          : "Verification failed",
        detail: state.verification.summary,
      });
    }
    items.push({ title: `Current stage: ${state.stage}`, at: state.updated_at });
    return items;
  }, [state]);

  return (
    <div className="panel p-5">
      <p className="mb-4 text-xs text-slate-500">
        Ordered workflow steps. Exact per-event timestamps shown only when present
        on CaseState.
      </p>
      <ol className="space-y-4">
        {steps.map((step, index) => (
          <li key={`${step.title}-${index}`} className="flex gap-4">
            <div className="flex flex-col items-center">
              <span className="mt-1 h-2.5 w-2.5 rounded-full bg-violet-400" />
              {index < steps.length - 1 ? (
                <span className="mt-1 w-px flex-1 bg-white/10" />
              ) : null}
            </div>
            <div className="pb-2">
              <div className="text-sm font-medium text-slate-100">{step.title}</div>
              {step.detail ? (
                <div className="mt-1 text-sm text-slate-400">{step.detail}</div>
              ) : null}
              {step.at ? (
                <div className="mt-1 inline-flex items-center gap-1 text-xs text-slate-500">
                  <Clock3 className="h-3 w-3" />
                  {formatDateTime(step.at)}
                </div>
              ) : null}
            </div>
          </li>
        ))}
      </ol>
    </div>
  );
}

function EvidenceTab({ state }: { state: CaseState }) {
  const graph = inferEvidenceGraph(state.evidence);

  return (
    <div className="space-y-4">
      {graph.length ? (
        <div className="panel p-4">
          <div className="text-xs font-semibold uppercase tracking-[0.14em] text-slate-500">
            Evidence graph (inferred from fields)
          </div>
          <div className="mt-3 flex flex-wrap items-center gap-2">
            {graph.map((node, index) => (
              <div key={node.id} className="flex items-center gap-2">
                <span className="rounded-md border border-white/10 bg-white/5 px-2.5 py-1 text-xs text-slate-200">
                  {node.label}
                </span>
                {index < graph.length - 1 ? (
                  <span className="text-slate-600">→</span>
                ) : null}
              </div>
            ))}
          </div>
        </div>
      ) : null}

      <div className="grid gap-3 lg:grid-cols-2">
        {state.evidence.map((item) => (
          <EvidenceCard key={item.evidence_id} evidence={item} />
        ))}
      </div>

      {state.hypotheses.length ? (
        <div className="space-y-3">
          <h3 className="text-display text-base font-semibold">Hypotheses</h3>
          {state.hypotheses.map((hypothesis) => (
            <HypothesisCard key={hypothesis.hypothesis_id} hypothesis={hypothesis} />
          ))}
        </div>
      ) : null}
    </div>
  );
}

function PlanTab({ state }: { state: CaseState }) {
  const plan = state.resolution_plan;
  if (!plan) {
    return (
      <div className="panel p-8 text-center text-sm text-slate-400">
        No resolution plan on this case
        {state.stage === "ESCALATED" ? " (escalated before planning completed)." : "."}
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="panel p-5">
        <div className="flex flex-wrap items-center gap-2">
          <h2 className="text-display text-lg font-semibold">Resolution Plan</h2>
          <span className="rounded-md border border-amber-500/30 bg-amber-500/10 px-2 py-0.5 text-xs text-amber-200">
            Risk: {plan.risk}
          </span>
          {plan.requires_approval ? (
            <span className="rounded-md border border-amber-500/30 bg-amber-500/10 px-2 py-0.5 text-xs text-amber-200">
              Human approval required
            </span>
          ) : null}
        </div>
        <p className="mt-3 text-sm leading-relaxed text-slate-300">{plan.explanation}</p>
      </div>

      <div className="space-y-3">
        {plan.actions.map((action, index) => (
          <div key={`${action.tool_name}-${index}`}>
            <PlanActionCard action={action} index={index} />
            {index < plan.actions.length - 1 ? (
              <div className="flex justify-center py-1 text-slate-600">
                <ArrowDown className="h-4 w-4" />
              </div>
            ) : null}
          </div>
        ))}
      </div>
    </div>
  );
}

function ReviewTab({ state }: { state: CaseState }) {
  const review = state.review;
  if (!review) {
    return (
      <div className="panel p-8 text-center text-sm text-slate-400">
        No reviewer output for this case.
      </div>
    );
  }

  const verdictStyle =
    review.verdict === "APPROVE"
      ? "border-emerald-500/30 bg-emerald-500/10 text-emerald-100"
      : review.verdict === "REVISE"
        ? "border-amber-500/30 bg-amber-500/10 text-amber-100"
        : "border-rose-500/30 bg-rose-500/10 text-rose-100";

  return (
    <div className="space-y-4">
      <div className={`panel p-5 ${verdictStyle}`}>
        <div className="text-xs uppercase tracking-[0.16em]">Reviewer verdict</div>
        <div className="mt-2 text-display text-3xl font-semibold">{review.verdict}</div>
        <p className="mt-3 text-sm opacity-90">{review.summary}</p>
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <div className="panel p-4">
          <div className="text-xs uppercase tracking-wider text-slate-500">Issues</div>
          {review.issues.length ? (
            <ul className="mt-2 space-y-2 text-sm text-slate-300">
              {review.issues.map((issue) => (
                <li key={issue} className="flex gap-2">
                  <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0 text-amber-300" />
                  {issue}
                </li>
              ))}
            </ul>
          ) : (
            <p className="mt-2 text-sm text-slate-400">No issues recorded.</p>
          )}
        </div>
        <div className="panel p-4">
          <div className="text-xs uppercase tracking-wider text-slate-500">
            Revision feedback
          </div>
          <p className="mt-2 text-sm text-slate-300">
            {review.revision_feedback ?? "None — clean approval flow."}
          </p>
          <div className="mt-3 text-xs text-slate-500">
            plan_revision_count: {state.plan_revision_count}
          </div>
        </div>
      </div>

      {state.plan_revision_count > 0 ? (
        <div className="panel p-4">
          <div className="text-xs uppercase tracking-wider text-slate-500">
            Self-reflection loop
          </div>
          <p className="mt-2 text-sm text-slate-300">
            Planner produced a revised plan after Reviewer feedback (
            {state.plan_revision_count} revision
            {state.plan_revision_count === 1 ? "" : "s"}). Historical planner v1
            payloads are not retained separately in CaseState — only the final
            plan and revision count are available.
          </p>
        </div>
      ) : (
        <div className="panel border-emerald-500/20 bg-emerald-500/5 p-4 text-sm text-emerald-100/90">
          Clean approval flow — no planner revision required.
        </div>
      )}
    </div>
  );
}

function ExecutionTab({ state }: { state: CaseState }) {
  const planned = state.resolution_plan?.actions ?? [];

  return (
    <div className="space-y-4">
      <div className="panel p-5">
        <h2 className="text-display text-lg font-semibold">Deterministic execution</h2>
        <p className="mt-2 text-sm text-slate-400">
          LLMs propose actions; deterministic application code performs writes and
          verification. Mutation steps are marked distinctly from read-after-write
          checks.
        </p>

        {planned.length ? (
          <div className="mt-4 flex flex-col items-start gap-2">
            {planned.map((action, index) => (
              <div key={`${action.tool_name}-flow-${index}`} className="w-full max-w-lg">
                <div
                  className={
                    isMutationTool(action.tool_name)
                      ? "rounded-lg border border-amber-500/30 bg-amber-500/10 px-3 py-2 text-sm text-amber-100"
                      : "rounded-lg border border-sky-500/30 bg-sky-500/10 px-3 py-2 text-sm text-sky-100"
                  }
                >
                  <div className="font-medium">{action.tool_name}</div>
                  <div className="mono mt-1 text-xs opacity-80">
                    {JSON.stringify(action.arguments)}
                  </div>
                </div>
                {index < planned.length - 1 ? (
                  <div className="flex justify-center py-1 text-slate-600">
                    <ArrowDown className="h-4 w-4" />
                  </div>
                ) : null}
              </div>
            ))}
            {state.customer_id === "ACME" && planned.some((a) => a.tool_name === "match_payment") ? (
              <div className="mt-2 max-w-lg rounded-lg border border-sky-500/20 bg-sky-500/5 px-3 py-2 text-xs text-sky-100/90">
                Expected deterministic sequence after approval: match_payment →
                get_invoice (PAID?) → remove_account_hold → restore CRM account
              </div>
            ) : null}
          </div>
        ) : (
          <p className="mt-4 text-sm text-slate-400">No planned actions to visualize.</p>
        )}
      </div>

      {state.executed_actions.length ? (
        <div className="space-y-3">
          {state.executed_actions.map((action, index) => (
            <div key={`${action.tool_name}-${action.started_at}-${index}`} className="panel p-4">
              <div className="flex flex-wrap items-center gap-2">
                <span className="font-medium text-slate-100">{action.tool_name}</span>
                <span
                  className={
                    action.status === "SUCCESS"
                      ? "text-xs text-emerald-300"
                      : action.status === "FAILED"
                        ? "text-xs text-rose-300"
                        : "text-xs text-amber-300"
                  }
                >
                  {action.status}
                </span>
                {isMutationTool(action.tool_name) ? (
                  <span className="rounded bg-amber-500/15 px-1.5 py-0.5 text-[10px] text-amber-200">
                    mutation
                  </span>
                ) : null}
                {isReadTool(action.tool_name) ? (
                  <span className="rounded bg-sky-500/15 px-1.5 py-0.5 text-[10px] text-sky-200">
                    verification read
                  </span>
                ) : null}
              </div>
              <pre className="mono mt-2 overflow-auto text-xs text-slate-400">
                {JSON.stringify(action.arguments, null, 2)}
              </pre>
              {action.result_summary ? (
                <p className="mt-2 text-sm text-slate-300">{action.result_summary}</p>
              ) : null}
              {action.error ? (
                <p className="mt-2 text-sm text-rose-300">{action.error}</p>
              ) : null}
              <div className="mt-2 text-xs text-slate-500">
                {formatDateTime(action.started_at)}
                {action.completed_at ? ` → ${formatDateTime(action.completed_at)}` : ""}
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="panel p-6 text-sm text-slate-400">
          No ExecutedAction records yet
          {state.stage === "AWAITING_APPROVAL"
            ? " — waiting for human approval before deterministic writes."
            : "."}
        </div>
      )}
    </div>
  );
}

function VerificationTab({ state }: { state: CaseState }) {
  const result = state.verification;

  if (!result) {
    return (
      <div className="panel p-8 text-center text-sm text-slate-400">
        Verification has not run for this case.
        {state.stage === "ESCALATED" ? " Case escalated before execution." : ""}
        {state.stage === "AWAITING_APPROVAL"
          ? " Approve and execute to produce verification checks."
          : ""}
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div
        className={
          result.success
            ? "panel border-emerald-500/30 bg-emerald-500/10 p-6 text-center"
            : "panel border-rose-500/30 bg-rose-500/10 p-6 text-center"
        }
      >
        <div className="text-xs uppercase tracking-[0.18em] text-slate-300">
          Final result
        </div>
        <div className="mt-2 text-display text-4xl font-semibold">
          {result.success ? "RESOLVED" : "FAILED"}
        </div>
        <p className="mt-3 text-sm opacity-90">{result.summary}</p>
      </div>

      <div className="space-y-2">
        {result.checks.map((check) => (
          <div
            key={check.name}
            className="panel flex items-start gap-3 p-4"
          >
            {check.passed ? (
              <CheckCircle2 className="mt-0.5 h-5 w-5 text-emerald-400" />
            ) : (
              <XCircle className="mt-0.5 h-5 w-5 text-rose-400" />
            )}
            <div>
              <div className="font-medium text-slate-100">{check.name}</div>
              <div className="mt-1 text-xs text-slate-400">
                expected <span className="mono text-slate-300">{check.expected}</span>
                {" · "}
                actual <span className="mono text-slate-300">{check.actual}</span>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
