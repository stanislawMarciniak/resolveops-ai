import type { ReactNode } from "react";
import { Link } from "react-router-dom";
import { api } from "@/api/client";
import { useAsync } from "@/hooks/useAsync";
import { Breadcrumbs } from "@/components/layout/Breadcrumbs";
import { PageSkeleton } from "@/components/ui/Skeleton";
import { formatPercent } from "@/utils/format";

export function AboutPage() {
  const overview = useAsync(() => api.evaluationsOverview(), []);
  const comparison = useAsync(() => api.evaluationsComparison(), []);

  if (overview.loading) return <PageSkeleton />;

  const multi = overview.data?.variants.multi_agent;
  const single = overview.data?.variants.single_agent;
  const none = overview.data?.variants.no_reviewer;

  return (
    <div className="fade-in space-y-6">
      <Breadcrumbs items={[{ label: "About Project" }]} />

      <div>
        <h1 className="text-display text-2xl font-semibold text-slate-50">
          About ResolveOps AI
        </h1>
        <p className="mt-2 max-w-3xl text-sm leading-relaxed text-slate-400">
          A production-oriented multi-agent platform for investigating and resolving
          enterprise support cases across CRM, legacy billing, and internal policies.
        </p>
      </div>

      <Section title="Problem">
        Enterprise support tickets often require reconciling inconsistent identifiers,
        unmatched payments, holds, and customer-specific contracts. Naive tool-calling
        agents can mutate production systems unsafely.
      </Section>

      <Section title="Architecture">
        Untrusted enterprise data → READ-only Investigator (MCP) → evidence-backed
        diagnosis → Planner (no tools) → independent Reviewer → human approval →
        deterministic Executor → read-after-write checks → deterministic Verifier.
      </Section>

      <div className="grid gap-4 md:grid-cols-2">
        <Section title="Why multi-agent?">
          Separation of investigation, planning, and critique improves safety and
          makes failures diagnosable. Current multi-agent pass rate:{" "}
          {multi ? formatPercent(multi.pass_rate) : "—"}.
        </Section>
        <Section title="Why deterministic execution?">
          LLMs never perform writes directly. Mutation plans are executed by Python
          application code with explicit verification.
        </Section>
        <Section title="Why MCP?">
          MCP creates a hard tool boundary between agents and CRM/Billing/Policy
          systems, enabling least-privilege READ vs WRITE surfaces.
        </Section>
        <Section title="Why human approval?">
          High-risk remediations require an operator gate before enterprise mutations.
        </Section>
        <Section title="Why Reviewer?">
          An independent critic catches unsafe plans (contract overrides, incomplete
          remediation). Ablation shows large pass-rate gaps, with methodology caveats
          — see Evaluations.
        </Section>
        <Section title="State & observability">
          CaseState is persisted and resumable. OpenTelemetry instruments the FastAPI
          backend; cost/token/latency metrics are stored on each case.
        </Section>
      </div>

      <Section title="Evaluation methodology">
        {overview.data?.total_cases ?? 20} synthetic cases across identifier
        normalization, partial payment, currency mismatch, split payments, stale holds,
        contract overrides, multi-invoice, missing mappings, false claims, and stored
        prompt injection. Variants: Multi-Agent, Single-Agent, No Reviewer.
      </Section>

      <Section title="Results">
        <ul className="list-disc space-y-1 pl-5">
          <li>Multi-Agent: {multi ? formatPercent(multi.pass_rate) : "—"}</li>
          <li>Single-Agent: {single ? formatPercent(single.pass_rate) : "—"}</li>
          <li>No Reviewer: {none ? formatPercent(none.pass_rate) : "—"}</li>
          {comparison.data ? (
            <li>
              Multi vs single pass delta:{" "}
              {formatPercent(comparison.data.multi_vs_single.pass_rate_delta)}
            </li>
          ) : null}
        </ul>
        <Link to="/evaluations" className="mt-3 inline-block text-sm text-violet-300">
          Open evaluation dashboard →
        </Link>
      </Section>

      <section>
        <h2 className="text-display text-lg font-semibold text-slate-50">Limitations</h2>
        <div className="mt-3 grid gap-3 md:grid-cols-2">
          <LimitCard
            title="Multi-invoice reasoning"
            rate={multi?.tag_pass_rates?.["multi-invoice"]}
            status="Known limitation"
          />
          <LimitCard
            title="Stored prompt injection"
            rate={multi?.tag_pass_rates?.["stored-injection"]}
            status="Security evaluation requires improvement"
          />
          <LimitCard
            title="Policy reasoning"
            rate={multi?.tag_pass_rates?.["policy-reasoning"]}
            status="Known limitation"
          />
          <LimitCard
            title="Minimal remediation"
            rate={multi?.tag_pass_rates?.["minimal-remediation"]}
            status="Known limitation"
          />
          <div className="panel border-amber-500/20 p-4">
            <div className="text-sm font-semibold text-slate-100">Latency & cost</div>
            <p className="mt-2 text-sm text-slate-400">
              Multi-agent is significantly slower and more expensive than single-agent
              — an explicit architecture tradeoff (quality ↑, cost ↑, latency ↑).
            </p>
            <div className="mt-2 text-xs uppercase tracking-wider text-amber-300">
              Status: Architecture tradeoff
            </div>
          </div>
        </div>
      </section>

      <Section title="Future work">
        Stronger multi-invoice planning, tighter causal Reviewer ablation, richer
        prompt-injection evals, and deeper live OpenTelemetry dashboards beyond stored
        case metrics.
      </Section>
    </div>
  );
}

function Section({
  title,
  children,
}: {
  title: string;
  children: ReactNode;
}) {
  return (
    <section className="panel p-5">
      <h2 className="text-display text-lg font-semibold text-slate-50">{title}</h2>
      <div className="mt-2 text-sm leading-relaxed text-slate-300">{children}</div>
    </section>
  );
}

function LimitCard({
  title,
  rate,
  status,
}: {
  title: string;
  rate?: number;
  status: string;
}) {
  return (
    <div className="panel border-rose-500/20 p-4">
      <div className="text-sm font-semibold text-slate-100">{title}</div>
      <div className="mt-2 text-display text-2xl font-semibold text-rose-200">
        {rate == null ? "—" : formatPercent(rate)}
      </div>
      <div className="mt-2 text-xs uppercase tracking-wider text-rose-300/90">
        Status: {status}
      </div>
    </div>
  );
}
