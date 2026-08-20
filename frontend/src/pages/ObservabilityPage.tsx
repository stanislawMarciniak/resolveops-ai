import type { ReactNode } from "react";
import { Link } from "react-router-dom";
import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { api } from "@/api/client";
import { useAsync } from "@/hooks/useAsync";
import { Breadcrumbs } from "@/components/layout/Breadcrumbs";
import { MetricCard } from "@/components/ui/MetricCard";
import { PageSkeleton } from "@/components/ui/Skeleton";
import { ErrorPanel } from "@/components/ui/ErrorPanel";
import {
  formatMs,
  formatUsd,
  shortId,
} from "@/utils/format";

export function ObservabilityPage() {
  const report = useAsync(() => api.evaluationVariant("multi_agent"), []);
  const cases = useAsync(() => api.listCases({ limit: 200 }), []);

  if (report.loading || cases.loading) return <PageSkeleton />;

  if (report.error || !report.data) {
    return (
      <ErrorPanel
        title="Observability data unavailable"
        message={report.error ?? "Missing multi_agent report"}
        onRetry={report.reload}
      />
    );
  }

  const evalCases = [...report.data.cases].sort(
    (a, b) => b.estimated_cost_usd - a.estimated_cost_usd,
  );
  const errors = evalCases.filter((item) => item.run_error);
  const summary = report.data.summary;

  const costChart = evalCases.map((item) => ({
    name: item.eval_id,
    cost: Number(item.estimated_cost_usd.toFixed(4)),
    caseId: item.case_id,
  }));

  const latencyChart = evalCases.map((item) => ({
    name: item.eval_id,
    latency: Number((item.llm_latency_ms / 1000).toFixed(2)),
    caseId: item.case_id,
  }));

  const modelChart = evalCases.map((item) => ({
    name: item.eval_id,
    calls: item.model_calls,
    caseId: item.case_id,
  }));

  const tokenChart = evalCases.map((item) => ({
    name: item.eval_id,
    tokens: item.total_tokens,
    caseId: item.case_id,
  }));

  const stageCounts = (cases.data?.items ?? []).reduce<Record<string, number>>(
    (acc, item) => {
      acc[item.stage] = (acc[item.stage] ?? 0) + 1;
      return acc;
    },
    {},
  );

  return (
    <div className="fade-in space-y-6">
      <Breadcrumbs items={[{ label: "Observability" }]} />

      <div>
        <h1 className="text-display text-2xl font-semibold text-slate-50">
          Observability
        </h1>
        <p className="mt-1 text-sm text-slate-400">
          Aggregate metrics from multi-agent evaluation runs and persisted cases.
          OpenTelemetry instrumentation exists on the backend; this page surfaces
          stored run metrics.
        </p>
      </div>

      <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-5">
        <MetricCard label="Avg model calls" value={summary.average_model_calls.toFixed(1)} accent="violet" />
        <MetricCard label="Avg tool calls" value={summary.average_tool_calls.toFixed(1)} accent="blue" />
        <MetricCard label="Avg tokens" value={Math.round(summary.average_tokens).toLocaleString()} accent="slate" />
        <MetricCard label="Avg cost" value={formatUsd(summary.average_cost_usd)} accent="green" />
        <MetricCard label="Avg latency" value={formatMs(summary.average_llm_latency_ms)} accent="amber" />
      </section>

      <section className="grid gap-4 lg:grid-cols-2">
        <ChartPanel title="Cost per case">
          <CaseBarChart data={costChart} dataKey="cost" color="#22c55e" />
        </ChartPanel>
        <ChartPanel title="Latency per case (s)">
          <CaseBarChart data={latencyChart} dataKey="latency" color="#f59e0b" />
        </ChartPanel>
        <ChartPanel title="Model calls per case">
          <CaseBarChart data={modelChart} dataKey="calls" color="#8b5cf6" />
        </ChartPanel>
        <ChartPanel title="Token usage by case">
          <CaseBarChart data={tokenChart} dataKey="tokens" color="#38bdf8" />
        </ChartPanel>
      </section>

      <section className="panel p-5">
        <h2 className="text-display text-lg font-semibold">Case stages (persisted)</h2>
        <div className="mt-3 flex flex-wrap gap-2">
          {Object.entries(stageCounts).map(([stage, count]) => (
            <span
              key={stage}
              className="rounded-lg border border-white/10 bg-white/5 px-3 py-1.5 text-xs text-slate-300"
            >
              {stage}: {count}
            </span>
          ))}
          {!Object.keys(stageCounts).length ? (
            <span className="text-sm text-slate-500">No persisted cases loaded.</span>
          ) : null}
        </div>
      </section>

      <section className="panel p-5">
        <h2 className="text-display text-lg font-semibold">Outliers</h2>
        <div className="mt-3 space-y-2">
          {evalCases.slice(0, 5).map((item) => (
            <Link
              key={item.eval_id}
              to={`/cases/${item.case_id}`}
              className="flex flex-wrap items-center justify-between gap-2 rounded-lg border border-white/8 bg-white/3 px-3 py-2 text-sm hover:bg-violet-500/10"
            >
              <span className="font-medium text-slate-100">{item.eval_id}</span>
              <span className="text-slate-400">
                {formatUsd(item.estimated_cost_usd)} · {item.model_calls} model ·{" "}
                {formatMs(item.llm_latency_ms)}
              </span>
              <span className="mono text-xs text-violet-300">{shortId(item.case_id)}</span>
            </Link>
          ))}
        </div>
        <p className="mt-3 text-xs text-slate-500">
          Tip: BADMAP / high model-call cases often hit LLM-call limits — inspect
          run_error and CaseState metrics.
        </p>
      </section>

      <section className="panel p-5">
        <h2 className="text-display text-lg font-semibold">Errors panel</h2>
        {errors.length ? (
          <ul className="mt-3 space-y-2">
            {errors.map((item) => (
              <li
                key={item.eval_id}
                className="rounded-lg border border-rose-500/30 bg-rose-500/8 px-3 py-2 text-sm"
              >
                <div className="font-medium text-rose-100">{item.eval_id}</div>
                <div className="mt-1 text-rose-200/80">{item.run_error}</div>
                <Link
                  to={`/cases/${item.case_id}`}
                  className="mt-2 inline-block text-xs text-violet-300"
                >
                  Open case
                </Link>
              </li>
            ))}
          </ul>
        ) : (
          <p className="mt-3 text-sm text-slate-400">
            No run_error values in multi-agent evaluation results.
          </p>
        )}
      </section>
    </div>
  );
}

function ChartPanel({
  title,
  children,
}: {
  title: string;
  children: ReactNode;
}) {
  return (
    <div className="panel p-4">
      <div className="mb-3 text-sm font-medium text-slate-200">{title}</div>
      <div className="h-[260px]">{children}</div>
    </div>
  );
}

function CaseBarChart({
  data,
  dataKey,
  color,
}: {
  data: Array<Record<string, string | number>>;
  dataKey: string;
  color: string;
}) {
  return (
    <ResponsiveContainer width="100%" height="100%">
      <BarChart data={data}>
        <CartesianGrid stroke="rgba(148,163,184,0.12)" vertical={false} />
        <XAxis dataKey="name" tick={{ fill: "#94a3b8", fontSize: 10 }} interval={0} angle={-35} textAnchor="end" height={60} />
        <YAxis tick={{ fill: "#94a3b8", fontSize: 11 }} />
        <Tooltip
          contentStyle={{
            background: "#0f172a",
            border: "1px solid rgba(255,255,255,0.1)",
            borderRadius: 8,
          }}
        />
        <Bar dataKey={dataKey} fill={color} radius={[4, 4, 0, 0]} />
      </BarChart>
    </ResponsiveContainer>
  );
}
