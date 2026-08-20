import { Link } from "react-router-dom";
import { api } from "@/api/client";
import { useAsync } from "@/hooks/useAsync";
import { Breadcrumbs } from "@/components/layout/Breadcrumbs";
import { MetricCard } from "@/components/ui/MetricCard";
import { PageSkeleton } from "@/components/ui/Skeleton";
import { ErrorPanel } from "@/components/ui/ErrorPanel";
import { EvaluationBarChart } from "@/components/charts/EvaluationBarChart";
import { QualityCostScatter } from "@/components/charts/QualityCostScatter";
import { TagHeatmap } from "@/components/evaluations/TagHeatmap";
import { ReviewerAblation } from "@/components/evaluations/ReviewerAblation";
import { ComparisonCard } from "@/components/evaluations/ComparisonCard";
import {
  VARIANT_LABELS,
  formatMs,
  formatNumber,
  formatPercent,
  formatUsd,
} from "@/utils/format";

export function EvaluationsPage() {
  const overview = useAsync(() => api.evaluationsOverview(), []);
  const comparison = useAsync(() => api.evaluationsComparison(), []);

  if (overview.loading || comparison.loading) return <PageSkeleton />;

  if (overview.error || !overview.data) {
    return (
      <ErrorPanel
        title="Evaluations unavailable"
        message={overview.error ?? "Missing overview"}
        onRetry={overview.reload}
      />
    );
  }

  if (comparison.error || !comparison.data) {
    return (
      <ErrorPanel
        title="Comparison unavailable"
        message={comparison.error ?? "Missing final_comparison.json"}
        onRetry={comparison.reload}
      />
    );
  }

  const multi = overview.data.variants.multi_agent;
  const single = overview.data.variants.single_agent;
  const none = overview.data.variants.no_reviewer;
  const cmp = comparison.data;

  const passData = [
    multi && { name: VARIANT_LABELS.multi_agent, value: multi.pass_rate * 100 },
    single && { name: VARIANT_LABELS.single_agent, value: single.pass_rate * 100 },
    none && { name: VARIANT_LABELS.no_reviewer, value: none.pass_rate * 100 },
  ].filter(Boolean) as Array<{ name: string; value: number }>;

  const costData = [
    multi && { name: VARIANT_LABELS.multi_agent, value: multi.average_cost_usd },
    single && { name: VARIANT_LABELS.single_agent, value: single.average_cost_usd },
    none && { name: VARIANT_LABELS.no_reviewer, value: none.average_cost_usd },
  ].filter(Boolean) as Array<{ name: string; value: number }>;

  const modelData = [
    multi && { name: VARIANT_LABELS.multi_agent, value: multi.average_model_calls },
    single && { name: VARIANT_LABELS.single_agent, value: single.average_model_calls },
    none && { name: VARIANT_LABELS.no_reviewer, value: none.average_model_calls },
  ].filter(Boolean) as Array<{ name: string; value: number }>;

  const toolData = [
    multi && { name: VARIANT_LABELS.multi_agent, value: multi.average_tool_calls },
    single && { name: VARIANT_LABELS.single_agent, value: single.average_tool_calls },
    none && { name: VARIANT_LABELS.no_reviewer, value: none.average_tool_calls },
  ].filter(Boolean) as Array<{ name: string; value: number }>;

  const latencyData = [
    multi && {
      name: VARIANT_LABELS.multi_agent,
      value: multi.average_llm_latency_ms / 1000,
    },
    single && {
      name: VARIANT_LABELS.single_agent,
      value: single.average_llm_latency_ms / 1000,
    },
    none && {
      name: VARIANT_LABELS.no_reviewer,
      value: none.average_llm_latency_ms / 1000,
    },
  ].filter(Boolean) as Array<{ name: string; value: number }>;

  const tokenData = [
    multi && { name: VARIANT_LABELS.multi_agent, value: multi.average_tokens },
    single && { name: VARIANT_LABELS.single_agent, value: single.average_tokens },
    none && { name: VARIANT_LABELS.no_reviewer, value: none.average_tokens },
  ].filter(Boolean) as Array<{ name: string; value: number }>;

  return (
    <div className="fade-in space-y-6">
      <Breadcrumbs items={[{ label: "Evaluations" }]} />

      <div>
        <h1 className="text-display text-2xl font-semibold text-slate-50">
          Evaluation dashboard
        </h1>
        <p className="mt-1 text-sm text-slate-400">
          Live values from{" "}
          <span className="mono text-slate-300">data/evals/results/*.json</span> via
          read-only API · {overview.data.dataset_name} v
          {overview.data.dataset_version}
        </p>
      </div>

      <section className="grid gap-4 md:grid-cols-3">
        <MetricCard
          label="Multi-Agent"
          value={multi ? formatPercent(multi.pass_rate) : "—"}
          hint={multi ? `${multi.passed_cases}/${multi.total_cases}` : undefined}
          accent="violet"
        />
        <MetricCard
          label="Single Agent"
          value={single ? formatPercent(single.pass_rate) : "—"}
          hint={single ? `${single.passed_cases}/${single.total_cases}` : undefined}
          accent="blue"
        />
        <MetricCard
          label="No Reviewer"
          value={none ? formatPercent(none.pass_rate) : "—"}
          hint={none ? `${none.passed_cases}/${none.total_cases}` : undefined}
          accent="amber"
        />
      </section>

      {multi && single ? (
        <ComparisonCard
          multiPass={multi.pass_rate}
          singlePass={single.pass_rate}
          delta={cmp.multi_vs_single.pass_rate_delta}
        />
      ) : null}

      <section className="grid gap-4 lg:grid-cols-2">
        <EvaluationBarChart
          title="Pass rate"
          data={passData}
          valueFormatter={(n) => `${n.toFixed(0)}%`}
          color="#8b5cf6"
        />
        <EvaluationBarChart
          title="Average cost (USD)"
          data={costData}
          valueFormatter={(n) => formatUsd(n)}
          color="#22c55e"
        />
        <EvaluationBarChart
          title="Average model calls"
          data={modelData}
          valueFormatter={(n) => formatNumber(n)}
          color="#60a5fa"
        />
        <EvaluationBarChart
          title="Average tool calls"
          data={toolData}
          valueFormatter={(n) => formatNumber(n)}
          color="#a78bfa"
        />
        <EvaluationBarChart
          title="Average LLM latency (s)"
          data={latencyData}
          valueFormatter={(n) => `${n.toFixed(1)}s`}
          color="#f59e0b"
        />
        <EvaluationBarChart
          title="Average tokens"
          data={tokenData}
          valueFormatter={(n) => Math.round(n).toLocaleString()}
          color="#38bdf8"
        />
      </section>

      <QualityCostScatter
        points={[
          multi && {
            name: "Multi-Agent",
            cost: multi.average_cost_usd,
            passRate: multi.pass_rate,
            color: "#8b5cf6",
          },
          single && {
            name: "Single Agent",
            cost: single.average_cost_usd,
            passRate: single.pass_rate,
            color: "#3b82f6",
          },
          none && {
            name: "No Reviewer",
            cost: none.average_cost_usd,
            passRate: none.pass_rate,
            color: "#f59e0b",
          },
        ].filter(Boolean) as Array<{
          name: string;
          cost: number;
          passRate: number;
          color: string;
        }>}
      />

      <TagHeatmap tagComparison={cmp.tag_comparison} />

      {multi && none ? (
        <ReviewerAblation
          ablation={cmp.reviewer_ablation}
          multiPass={multi.pass_rate}
          noReviewerPass={none.pass_rate}
        />
      ) : null}

      <section className="panel p-5">
        <h2 className="text-display text-lg font-semibold">Multi vs single deltas</h2>
        <div className="mt-3 grid gap-3 sm:grid-cols-2 lg:grid-cols-4 text-sm">
          <Delta
            label="Pass rate"
            value={`+${formatPercent(cmp.multi_vs_single.pass_rate_delta)}`}
          />
          <Delta
            label="Cost / case"
            value={formatUsd(cmp.multi_vs_single.average_cost_delta_usd)}
          />
          <Delta
            label="Model calls"
            value={`+${formatNumber(cmp.multi_vs_single.average_model_calls_delta)}`}
          />
          <Delta
            label="Latency"
            value={`+${formatMs(cmp.multi_vs_single.average_latency_delta_ms)}`}
          />
        </div>
        <div className="mt-4 text-sm text-slate-400">
          Multi-only passes:{" "}
          {cmp.multi_vs_single.multi_agent_only_passes.map((id) => (
            <Link
              key={id}
              to={`/showcase/${id}`}
              className="mr-2 text-violet-300 hover:text-violet-200"
            >
              {id}
            </Link>
          ))}
        </div>
      </section>
    </div>
  );
}

function Delta({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-lg border border-white/8 bg-white/3 px-3 py-2">
      <div className="text-xs text-slate-500">{label}</div>
      <div className="mt-1 font-medium text-slate-100">{value}</div>
    </div>
  );
}
