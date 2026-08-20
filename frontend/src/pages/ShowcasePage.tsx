import { Link } from "react-router-dom";
import { api } from "@/api/client";
import { useAsync } from "@/hooks/useAsync";
import { Breadcrumbs } from "@/components/layout/Breadcrumbs";
import { PageSkeleton } from "@/components/ui/Skeleton";
import { ErrorPanel, EmptyState } from "@/components/ui/ErrorPanel";
import { VARIANT_LABELS, formatPercent } from "@/utils/format";

const PRIORITY = ["ACME", "ATLAS", "VEGA", "POLARIS", "LYRA"];

export function ShowcasePage() {
  const scenarios = useAsync(() => api.showcaseScenarios(), []);

  if (scenarios.loading) return <PageSkeleton />;
  if (scenarios.error || !scenarios.data) {
    return (
      <ErrorPanel
        title="Showcase unavailable"
        message={scenarios.error ?? "No scenarios"}
        onRetry={scenarios.reload}
      />
    );
  }

  if (!scenarios.data.length) {
    return <EmptyState title="No scenarios" description="Dataset is empty." />;
  }

  const sorted = [...scenarios.data].sort((a, b) => {
    const ai = PRIORITY.indexOf(a.scenario);
    const bi = PRIORITY.indexOf(b.scenario);
    if (ai === -1 && bi === -1) return a.scenario.localeCompare(b.scenario);
    if (ai === -1) return 1;
    if (bi === -1) return -1;
    return ai - bi;
  });

  return (
    <div className="fade-in space-y-5">
      <Breadcrumbs items={[{ label: "Showcase" }]} />

      <div>
        <h1 className="text-display text-2xl font-semibold text-slate-50">
          Dataset case showcase
        </h1>
        <p className="mt-1 max-w-3xl text-sm text-slate-400">
          Explore evaluation scenarios grouped by customer. Priority demos: ACME,
          ATLAS, VEGA, POLARIS, LYRA.
        </p>
      </div>

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        {sorted.map((scenario) => {
          const multi = scenario.results.multi_agent;
          const single = scenario.results.single_agent;
          const none = scenario.results.no_reviewer;
          const primaryEval = scenario.eval_ids[0];
          const featured = PRIORITY.includes(scenario.scenario);

          return (
            <Link
              key={scenario.scenario}
              to={`/showcase/${primaryEval}`}
              className={
                featured
                  ? "panel block p-5 transition hover:border-violet-500/40 hover:bg-violet-500/5"
                  : "panel block p-5 transition hover:border-white/20"
              }
            >
              <div className="flex items-start justify-between gap-2">
                <h2 className="text-display text-xl font-semibold text-slate-50">
                  {scenario.scenario}
                </h2>
                {featured ? (
                  <span className="rounded-md bg-violet-500/20 px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wider text-violet-200">
                    Featured
                  </span>
                ) : null}
              </div>
              <p className="mt-2 text-sm leading-relaxed text-slate-400">
                {scenario.description}
              </p>
              {scenario.expected_safe_behavior ? (
                <p className="mt-3 text-xs text-slate-500">
                  Expected: {scenario.expected_safe_behavior}
                </p>
              ) : null}

              <div className="mt-4 grid grid-cols-3 gap-2 text-center text-xs">
                <ResultChip
                  label="Multi"
                  passRate={multi?.pass_rate}
                  passed={multi?.passed_cases}
                  total={multi?.total_cases}
                />
                <ResultChip
                  label="Single"
                  passRate={single?.pass_rate}
                  passed={single?.passed_cases}
                  total={single?.total_cases}
                />
                <ResultChip
                  label="No Rev"
                  passRate={none?.pass_rate}
                  passed={none?.passed_cases}
                  total={none?.total_cases}
                />
              </div>

              <div className="mt-3 flex flex-wrap gap-1">
                {scenario.tags.slice(0, 4).map((tag) => (
                  <span
                    key={tag}
                    className="rounded border border-white/8 bg-white/4 px-1.5 py-0.5 text-[10px] text-slate-400"
                  >
                    {tag}
                  </span>
                ))}
              </div>

              {scenario.scenario === "ATLAS" &&
              multi &&
              none &&
              multi.pass_rate > none.pass_rate ? (
                <p className="mt-3 text-xs text-amber-200/90">
                  Why? Reviewer / policy handling prevented unsafe mutation in
                  no-reviewer runs.
                </p>
              ) : null}
            </Link>
          );
        })}
      </div>

      <p className="text-xs text-slate-500">
        Labels: {Object.values(VARIANT_LABELS).join(" · ")}
      </p>
    </div>
  );
}

function ResultChip({
  label,
  passRate,
  passed,
  total,
}: {
  label: string;
  passRate?: number;
  passed?: number;
  total?: number;
}) {
  const ok = passRate != null && passRate >= 0.99;
  const mid = passRate != null && passRate > 0 && passRate < 0.99;
  return (
    <div
      className={
        ok
          ? "rounded-lg border border-emerald-500/30 bg-emerald-500/10 px-2 py-2"
          : mid
            ? "rounded-lg border border-amber-500/30 bg-amber-500/10 px-2 py-2"
            : "rounded-lg border border-rose-500/30 bg-rose-500/10 px-2 py-2"
      }
    >
      <div className="text-slate-400">{label}</div>
      <div className="mt-1 font-semibold text-slate-100">
        {passRate == null ? "—" : passRate >= 0.99 ? "PASS" : formatPercent(passRate)}
      </div>
      {passed != null && total != null ? (
        <div className="text-[10px] text-slate-500">
          {passed}/{total}
        </div>
      ) : null}
    </div>
  );
}
