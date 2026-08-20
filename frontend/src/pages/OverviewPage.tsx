import { Link } from "react-router-dom";
import {
  ArrowRight,
  Bot,
  Fingerprint,
  GitBranch,
  Lock,
  Radar,
  ShieldCheck,
  Workflow,
} from "lucide-react";
import { api } from "@/api/client";
import { useAsync } from "@/hooks/useAsync";
import { Breadcrumbs } from "@/components/layout/Breadcrumbs";
import { MetricCard } from "@/components/ui/MetricCard";
import { PageSkeleton } from "@/components/ui/Skeleton";
import { ErrorPanel } from "@/components/ui/ErrorPanel";
import { ComparisonCard } from "@/components/evaluations/ComparisonCard";
import { QualityCostScatter } from "@/components/charts/QualityCostScatter";
import {
  formatMs,
  formatNumber,
  formatPercent,
  formatUsd,
} from "@/utils/format";

const BADGES = [
  { icon: Workflow, label: "Multi-agent architecture" },
  { icon: Radar, label: "Read-only Investigator" },
  { icon: ShieldCheck, label: "Human-in-the-loop" },
  { icon: GitBranch, label: "Deterministic Executor" },
  { icon: Lock, label: "MCP tool boundary" },
  { icon: Bot, label: "Policy RAG" },
  { icon: Fingerprint, label: "Prompt injection protection" },
  { icon: Radar, label: "OpenTelemetry" },
];

export function OverviewPage() {
  const overview = useAsync(() => api.evaluationsOverview(), []);
  const comparison = useAsync(() => api.evaluationsComparison(), []);
  const acme = useAsync(() => api.evaluationCase("acme-01"), []);

  if (overview.loading || comparison.loading) return <PageSkeleton />;

  if (overview.error || !overview.data) {
    return (
      <ErrorPanel
        title="Evaluations unavailable"
        message={overview.error ?? "No evaluation overview"}
        onRetry={overview.reload}
      />
    );
  }

  const variants = overview.data.variants;
  const multi = variants.multi_agent;
  const single = variants.single_agent;
  const none = variants.no_reviewer;
  const delta =
    comparison.data?.multi_vs_single.pass_rate_delta ??
    (multi && single ? multi.pass_rate - single.pass_rate : 0);
  const acmeCaseId = acme.data?.variants.multi_agent?.case_id;

  return (
    <div className="fade-in space-y-6">
      <Breadcrumbs items={[{ label: "Overview" }]} />

      <section className="panel relative overflow-hidden p-6 md:p-8">
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_top_right,rgba(124,58,237,0.22),transparent_45%)]" />
        <div className="relative max-w-3xl">
          <div className="text-xs font-semibold uppercase tracking-[0.2em] text-violet-300">
            ResolveOps AI
          </div>
          <h1 className="mt-3 text-display text-3xl font-semibold tracking-tight text-slate-50 md:text-4xl">
            Multi-Agent Enterprise Case Resolution
          </h1>
          <p className="mt-4 max-w-2xl text-sm leading-relaxed text-slate-300 md:text-base">
            ResolveOps investigates CRM and legacy billing systems, consults
            policies, proposes safe remediation, performs independent review,
            requires human approval, and executes mutations deterministically.
          </p>

          <div className="mt-6 flex flex-wrap gap-2">
            {BADGES.map((badge) => (
              <span
                key={badge.label}
                className="inline-flex items-center gap-1.5 rounded-full border border-white/10 bg-white/5 px-3 py-1 text-xs text-slate-300"
              >
                <badge.icon className="h-3.5 w-3.5 text-violet-300" />
                {badge.label}
              </span>
            ))}
          </div>

          <div className="mt-6 flex flex-wrap gap-3">
            <Link
              to="/evaluations"
              className="inline-flex items-center gap-2 rounded-lg bg-violet-600 px-4 py-2 text-sm font-medium text-white hover:bg-violet-500"
            >
              View evaluations <ArrowRight className="h-4 w-4" />
            </Link>
            <Link
              to={acmeCaseId ? `/cases/${acmeCaseId}` : "/cases?customer=ACME"}
              className="inline-flex items-center gap-2 rounded-lg border border-white/10 bg-white/5 px-4 py-2 text-sm text-slate-200 hover:bg-white/10"
            >
              Open ACME case
            </Link>
            <Link
              to="/architecture"
              className="inline-flex items-center gap-2 rounded-lg border border-white/10 bg-white/5 px-4 py-2 text-sm text-slate-200 hover:bg-white/10"
            >
              Architecture
            </Link>
          </div>
        </div>
      </section>

      <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <MetricCard
          label="Multi-agent pass rate"
          value={multi ? formatPercent(multi.pass_rate) : "—"}
          hint={multi ? `${multi.passed_cases}/${multi.total_cases} cases` : undefined}
          accent="violet"
        />
        <MetricCard
          label="Single-agent pass rate"
          value={single ? formatPercent(single.pass_rate) : "—"}
          hint={single ? `${single.passed_cases}/${single.total_cases} cases` : undefined}
          accent="blue"
        />
        <MetricCard
          label="No-reviewer pass rate"
          value={none ? formatPercent(none.pass_rate) : "—"}
          hint="Reviewer ablation"
          accent="amber"
        />
        <MetricCard
          label="Eval case count"
          value={overview.data.total_cases}
          hint={`${overview.data.dataset_name} v${overview.data.dataset_version}`}
          accent="slate"
        />
      </section>

      <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <MetricCard
          label="Avg cost / case"
          value={multi ? formatUsd(multi.average_cost_usd) : "—"}
          hint="Multi-agent"
          accent="slate"
        />
        <MetricCard
          label="Avg model calls"
          value={multi ? formatNumber(multi.average_model_calls) : "—"}
          accent="slate"
        />
        <MetricCard
          label="Avg tool calls"
          value={multi ? formatNumber(multi.average_tool_calls) : "—"}
          accent="slate"
        />
        <MetricCard
          label="Avg LLM latency"
          value={multi ? formatMs(multi.average_llm_latency_ms) : "—"}
          accent="slate"
        />
      </section>

      {multi && single ? (
        <section className="grid gap-4 lg:grid-cols-2">
          <ComparisonCard
            multiPass={multi.pass_rate}
            singlePass={single.pass_rate}
            delta={delta}
          />
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
        </section>
      ) : null}

      <section className="panel p-5">
        <h2 className="text-display text-lg font-semibold text-slate-50">
          Product narrative
        </h2>
        <div className="mt-4 grid gap-3 md:grid-cols-2">
          <div className="rounded-xl border border-rose-500/20 bg-rose-500/5 p-4">
            <div className="text-xs font-semibold uppercase tracking-wider text-rose-300">
              Traditional autonomous agent
            </div>
            <p className="mt-2 text-sm text-slate-300">
              LLM → tools → enterprise mutation
            </p>
          </div>
          <div className="rounded-xl border border-emerald-500/20 bg-emerald-500/5 p-4">
            <div className="text-xs font-semibold uppercase tracking-wider text-emerald-300">
              ResolveOps
            </div>
            <p className="mt-2 text-sm leading-relaxed text-slate-300">
              Untrusted data → READ-only Investigator → Planner → Reviewer →
              human approval → deterministic Executor → verification
            </p>
          </div>
        </div>
      </section>
    </div>
  );
}
