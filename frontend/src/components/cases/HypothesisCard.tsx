import { Lightbulb } from "lucide-react";
import type { Hypothesis } from "@/types";
import { cn, formatPercent } from "@/utils/format";

export function HypothesisCard({
  hypothesis,
  className,
}: {
  hypothesis: Hypothesis;
  className?: string;
}) {
  const confidencePct = Math.max(0, Math.min(100, hypothesis.confidence * 100));
  const confidenceTone =
    hypothesis.confidence >= 0.75
      ? "text-emerald-300"
      : hypothesis.confidence >= 0.45
        ? "text-amber-300"
        : "text-rose-300";

  return (
    <div className={cn("panel overflow-hidden fade-in", className)}>
      <div className="flex items-start gap-3 p-4">
        <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg border border-amber-500/30 bg-amber-500/10 text-amber-200">
          <Lightbulb className="h-4 w-4" />
        </div>
        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <span className="mono text-xs font-medium text-violet-300">
              {hypothesis.hypothesis_id}
            </span>
            <span className={cn("mono text-sm font-semibold", confidenceTone)}>
              {formatPercent(hypothesis.confidence, 0)} confidence
            </span>
          </div>

          <div className="mt-2 h-1.5 overflow-hidden rounded-full bg-white/5">
            <div
              className="h-full rounded-full bg-gradient-to-r from-violet-500 to-amber-400"
              style={{ width: `${confidencePct}%` }}
            />
          </div>

          <p className="mt-3 text-sm leading-relaxed text-slate-200">
            {hypothesis.description}
          </p>

          <div className="mt-3">
            <div className="text-[11px] font-medium uppercase tracking-[0.14em] text-slate-500">
              Supporting evidence
            </div>
            {hypothesis.evidence_ids.length === 0 ? (
              <p className="mt-1.5 text-xs text-slate-500">No linked evidence</p>
            ) : (
              <div className="mt-1.5 flex flex-wrap gap-1.5">
                {hypothesis.evidence_ids.map((id) => (
                  <span
                    key={id}
                    className="rounded-md border border-sky-500/25 bg-sky-500/10 px-2 py-0.5 mono text-[11px] text-sky-200"
                  >
                    {id}
                  </span>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
