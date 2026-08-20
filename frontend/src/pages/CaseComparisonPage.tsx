import type { ReactNode } from "react";
import { Link, useParams } from "react-router-dom";
import {
  Background,
  Controls,
  MarkerType,
  ReactFlow,
  type Edge,
  type Node,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import { useMemo } from "react";
import { api } from "@/api/client";
import { useAsync } from "@/hooks/useAsync";
import { Breadcrumbs } from "@/components/layout/Breadcrumbs";
import { PageSkeleton } from "@/components/ui/Skeleton";
import { ErrorPanel } from "@/components/ui/ErrorPanel";
import { JsonViewer } from "@/components/ui/JsonViewer";
import { StageBadge } from "@/components/ui/StageBadge";
import type { EvalCaseResult, EvalVariant } from "@/types";
import {
  VARIANT_LABELS,
  formatMs,
  formatUsd,
} from "@/utils/format";

const COLUMNS: EvalVariant[] = ["multi_agent", "single_agent", "no_reviewer"];

export function CaseComparisonPage() {
  const { evalId = "" } = useParams();
  const query = useAsync(() => api.evaluationCase(evalId), [evalId]);

  if (query.loading) return <PageSkeleton />;
  if (query.error || !query.data) {
    return (
      <ErrorPanel
        title="Comparison unavailable"
        message={query.error ?? "Missing eval case"}
        onRetry={query.reload}
      />
    );
  }

  const { dataset_case: datasetCase, variants } = query.data;
  const customer = datasetCase?.customer_id ?? evalId.split("-")[0]?.toUpperCase();

  return (
    <div className="fade-in space-y-5">
      <Breadcrumbs
        items={[
          { label: "Showcase", to: "/showcase" },
          { label: evalId },
        ]}
      />

      <div>
        <h1 className="text-display text-2xl font-semibold text-slate-50">
          {customer} · {evalId}
        </h1>
        <p className="mt-2 max-w-3xl text-sm text-slate-400">
          {datasetCase?.description ?? "Variant comparison for this evaluation case."}
        </p>
        {datasetCase?.tags?.length ? (
          <div className="mt-3 flex flex-wrap gap-1">
            {datasetCase.tags.map((tag) => (
              <span
                key={tag}
                className="rounded border border-white/8 bg-white/4 px-1.5 py-0.5 text-[10px] text-slate-400"
              >
                {tag}
              </span>
            ))}
          </div>
        ) : null}
      </div>

      <DivergenceDiagram variants={variants} />

      <div className="grid gap-4 xl:grid-cols-3">
        {COLUMNS.map((variant) => {
          const result = variants[variant];
          return (
            <VariantColumn
              key={variant}
              variant={variant}
              result={result}
            />
          );
        })}
      </div>

      <JsonViewer data={query.data} title="Eval case comparison payload" initiallyOpen={false} />
    </div>
  );
}

function VariantColumn({
  variant,
  result,
}: {
  variant: EvalVariant;
  result?: EvalCaseResult;
}) {
  if (!result) {
    return (
      <div className="panel p-4 text-sm text-slate-500">
        {VARIANT_LABELS[variant]} — no result
      </div>
    );
  }

  return (
    <div
      className={
        result.passed
          ? "panel border-emerald-500/25 p-4"
          : "panel border-rose-500/25 p-4"
      }
    >
      <div className="flex items-center justify-between gap-2">
        <h2 className="text-display font-semibold text-slate-50">
          {VARIANT_LABELS[variant]}
        </h2>
        <span
          className={
            result.passed
              ? "rounded-md bg-emerald-500/20 px-2 py-0.5 text-xs font-semibold text-emerald-200"
              : "rounded-md bg-rose-500/20 px-2 py-0.5 text-xs font-semibold text-rose-200"
          }
        >
          {result.passed ? "PASS" : "FAIL"}
        </span>
      </div>

      <div className="mt-3 space-y-2 text-sm">
        <Row label="Stage" value={<StageBadge stage={result.actual_stage} />} />
        <Row label="Expected" value={result.expected_stage} />
        <Row
          label="Root cause"
          value={
            result.root_cause_correct == null
              ? "—"
              : result.root_cause_correct
                ? "correct"
                : "incorrect"
          }
        />
        <Row
          label="Plan"
          value={
            result.actual_actions.length
              ? result.actual_actions.join(" → ")
              : "—"
          }
        />
        <Row label="Review" value={result.actual_review_verdict ?? "—"} />
        <Row label="Model calls" value={String(result.model_calls)} />
        <Row label="Tool calls" value={String(result.tool_calls)} />
        <Row label="Tokens" value={result.total_tokens.toLocaleString()} />
        <Row label="Latency" value={formatMs(result.llm_latency_ms)} />
        <Row label="Cost" value={formatUsd(result.estimated_cost_usd)} />
        {result.run_error ? (
          <Row label="Error" value={<span className="text-rose-300">{result.run_error}</span>} />
        ) : null}
      </div>

      <Link
        to={`/cases/${result.case_id}`}
        className="mt-4 inline-block text-xs text-violet-300 hover:text-violet-200"
      >
        Open CaseState →
      </Link>
    </div>
  );
}

function Row({ label, value }: { label: string; value: ReactNode }) {
  return (
    <div className="grid grid-cols-[100px_1fr] gap-2">
      <div className="text-xs text-slate-500">{label}</div>
      <div className="text-slate-200">{value}</div>
    </div>
  );
}

function DivergenceDiagram({
  variants,
}: {
  variants: Partial<Record<EvalVariant, EvalCaseResult>>;
}) {
  const { nodes, edges } = useMemo(() => {
    const flowNodes: Node[] = [];
    const flowEdges: Edge[] = [];

    COLUMNS.forEach((variant, col) => {
      const result = variants[variant];
      const x = col * 260;
      const passed = result?.passed;
      const stage = result?.actual_stage ?? "—";
      const review = result?.actual_review_verdict;

      const steps =
        variant === "single_agent"
          ? ["Single Agent", stage, passed ? "PASS" : "FAIL"]
          : variant === "no_reviewer"
            ? ["Investigator", "Planner", stage, passed ? "PASS" : "FAIL"]
            : [
                "Investigator",
                "Planner",
                review ? `Reviewer ${review}` : "Reviewer",
                stage,
                passed ? "PASS" : "FAIL",
              ];

      steps.forEach((label, row) => {
        const id = `${variant}-${row}`;
        flowNodes.push({
          id,
          position: { x, y: row * 70 },
          data: { label },
          style: {
            width: 180,
            borderRadius: 10,
            border: `1px solid ${
              label === "PASS"
                ? "rgba(52,211,153,0.45)"
                : label === "FAIL"
                  ? "rgba(251,113,113,0.45)"
                  : "rgba(148,163,184,0.25)"
            }`,
            background:
              label === "PASS"
                ? "rgba(16,185,129,0.15)"
                : label === "FAIL"
                  ? "rgba(244,63,94,0.12)"
                  : "rgba(15,23,42,0.9)",
            color: "#e2e8f0",
            fontSize: 12,
            padding: 8,
          },
        });
        if (row > 0) {
          flowEdges.push({
            id: `${id}-edge`,
            source: `${variant}-${row - 1}`,
            target: id,
            style: { stroke: "#64748b" },
            markerEnd: { type: MarkerType.ArrowClosed, color: "#64748b" },
          });
        }
      });
    });

    return { nodes: flowNodes, edges: flowEdges };
  }, [variants]);

  return (
    <div className="panel h-[360px] overflow-hidden">
      <div className="border-b border-white/8 px-4 py-2 text-xs uppercase tracking-wider text-slate-500">
        Where behavior diverged
      </div>
      <div className="h-[calc(100%-36px)]">
        <ReactFlow
          nodes={nodes}
          edges={edges}
          fitView
          proOptions={{ hideAttribution: true }}
          nodesDraggable={false}
          nodesConnectable={false}
          minZoom={0.45}
          maxZoom={1.2}
        >
          <Background gap={18} color="#1e293b" />
          <Controls showInteractive={false} className="!bg-surface-850 !border-white/10" />
        </ReactFlow>
      </div>
    </div>
  );
}
