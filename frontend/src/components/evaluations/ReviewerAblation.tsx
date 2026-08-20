import { Link } from "react-router-dom";
import { AlertTriangle, Info, ShieldCheck, ShieldX } from "lucide-react";
import type { FinalComparison } from "@/types";
import { cn, formatMs, formatPercent, formatUsd, formatNumber } from "@/utils/format";

export function ReviewerAblation({
  ablation,
  multiPass,
  noReviewerPass,
  className,
}: {
  ablation: FinalComparison["reviewer_ablation"];
  multiPass: number;
  noReviewerPass: number;
  className?: string;
}) {
  return (
    <div className={cn("panel overflow-hidden fade-in", className)}>
      <div className="border-b border-white/8 bg-gradient-to-br from-violet-500/12 via-transparent to-sky-500/5 px-5 py-4">
        <h3 className="text-display text-sm font-semibold tracking-wide text-slate-100">
          Reviewer ablation
        </h3>
        <p className="mt-1 text-xs text-slate-400">
          Multi-Agent with Reviewer vs the same architecture without Reviewer
        </p>
      </div>

      <div className="grid gap-4 p-5 sm:grid-cols-3">
        <DeltaStat
          label="With Reviewer"
          value={formatPercent(multiPass, 0)}
          hint="Pass rate"
        />
        <DeltaStat
          label="No Reviewer"
          value={formatPercent(noReviewerPass, 0)}
          hint="Pass rate"
        />
        <DeltaStat
          label="Pass-rate Δ"
          value={`${ablation.pass_rate_delta >= 0 ? "+" : ""}${formatPercent(ablation.pass_rate_delta, 0)}`}
          hint="Observed difference"
          accent={ablation.pass_rate_delta >= 0 ? "good" : "bad"}
        />
      </div>

      <div className="grid gap-3 border-t border-white/8 px-5 py-4 sm:grid-cols-3">
        <MetaChip
          label="Cost Δ"
          value={`${ablation.average_cost_delta_usd >= 0 ? "+" : ""}${formatUsd(ablation.average_cost_delta_usd, 3)}`}
        />
        <MetaChip
          label="Model calls Δ"
          value={`${ablation.average_model_calls_delta >= 0 ? "+" : ""}${formatNumber(ablation.average_model_calls_delta, 1)}`}
        />
        <MetaChip
          label="Latency Δ"
          value={`${ablation.average_latency_delta_ms >= 0 ? "+" : ""}${formatMs(ablation.average_latency_delta_ms)}`}
        />
      </div>

      <div className="grid gap-4 border-t border-white/8 p-5 lg:grid-cols-2">
        <CaseChipList
          title="Reviewer saved cases"
          icon={ShieldCheck}
          tone="good"
          empty="No saved cases in this run."
          ids={ablation.reviewer_saved_cases}
        />
        <CaseChipList
          title="Reviewer hurt cases"
          icon={ShieldX}
          tone="bad"
          empty="No hurt cases in this run."
          ids={ablation.reviewer_hurt_cases}
        />
      </div>

      <div className="flex gap-3 border-t border-white/8 bg-surface-900/50 px-5 py-4 text-xs leading-relaxed text-slate-400">
        <Info className="mt-0.5 h-4 w-4 shrink-0 text-sky-300" />
        <p>
          Methodological note: ablation runs independently execute stochastic
          Investigator and Planner calls. The observed pass-rate difference is
          not a perfectly isolated causal estimate of Reviewer contribution—do
          not attribute the entire delta to Reviewer alone.
        </p>
      </div>
    </div>
  );
}

function DeltaStat({
  label,
  value,
  hint,
  accent,
}: {
  label: string;
  value: string;
  hint: string;
  accent?: "good" | "bad";
}) {
  return (
    <div className="rounded-xl border border-white/8 bg-surface-900/60 p-4">
      <div className="text-[11px] uppercase tracking-[0.14em] text-slate-500">
        {label}
      </div>
      <div
        className={cn(
          "mt-2 text-display text-2xl font-semibold",
          accent === "good"
            ? "text-emerald-300"
            : accent === "bad"
              ? "text-rose-300"
              : "text-slate-50",
        )}
      >
        {value}
      </div>
      <div className="mt-1 text-xs text-slate-500">{hint}</div>
    </div>
  );
}

function MetaChip({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-lg border border-white/8 bg-white/[0.02] px-3 py-2">
      <div className="text-[11px] text-slate-500">{label}</div>
      <div className="mt-0.5 mono text-sm text-slate-200">{value}</div>
    </div>
  );
}

function CaseChipList({
  title,
  icon: Icon,
  tone,
  ids,
  empty,
}: {
  title: string;
  icon: typeof AlertTriangle;
  tone: "good" | "bad";
  ids: string[];
  empty: string;
}) {
  return (
    <div>
      <div className="mb-2 flex items-center gap-2 text-xs font-medium text-slate-300">
        <Icon
          className={cn(
            "h-4 w-4",
            tone === "good" ? "text-emerald-300" : "text-rose-300",
          )}
        />
        {title}
        <span className="mono text-slate-500">({ids.length})</span>
      </div>
      {ids.length === 0 ? (
        <p className="text-xs text-slate-500">{empty}</p>
      ) : (
        <div className="flex flex-wrap gap-1.5">
          {ids.map((evalId) => (
            <Link
              key={evalId}
              to={`/showcase/${evalId}`}
              className={cn(
                "rounded-md border px-2 py-1 mono text-[11px] transition hover:brightness-110",
                tone === "good"
                  ? "border-emerald-500/30 bg-emerald-500/10 text-emerald-200"
                  : "border-rose-500/30 bg-rose-500/10 text-rose-200",
              )}
            >
              {evalId}
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
