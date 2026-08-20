import { useMemo, useState, type CSSProperties } from "react";
import { ArrowDownWideNarrow } from "lucide-react";
import { VARIANT_LABELS, cn, formatPercent } from "@/utils/format";

type TagRates = {
  multi_agent: number;
  single_agent: number;
  no_reviewer: number;
};

type SortMode = "advantage" | "weakest" | "strongest";

const SORT_OPTIONS: Array<{ id: SortMode; label: string }> = [
  { id: "advantage", label: "Biggest multi-agent advantage" },
  { id: "weakest", label: "Weakest category" },
  { id: "strongest", label: "Strongest category" },
];

function average(rates: TagRates): number {
  return (rates.multi_agent + rates.single_agent + rates.no_reviewer) / 3;
}

function heatStyle(value: number): CSSProperties {
  const intensity = Math.max(0, Math.min(1, value));
  const alpha = 0.08 + intensity * 0.42;
  return {
    backgroundColor: `rgba(139, 92, 246, ${alpha})`,
    color: intensity > 0.55 ? "#f5f3ff" : "#cbd5e1",
  };
}

export function TagHeatmap({
  tagComparison,
  className,
}: {
  tagComparison: Record<string, TagRates>;
  className?: string;
}) {
  const [sortMode, setSortMode] = useState<SortMode>("advantage");

  const rows = useMemo(() => {
    const entries = Object.entries(tagComparison).map(([tag, rates]) => ({
      tag,
      rates,
      advantage: rates.multi_agent - rates.single_agent,
      avg: average(rates),
    }));

    entries.sort((a, b) => {
      if (sortMode === "advantage") return b.advantage - a.advantage;
      if (sortMode === "weakest") return a.avg - b.avg;
      return b.avg - a.avg;
    });

    return entries;
  }, [tagComparison, sortMode]);

  return (
    <div className={cn("panel overflow-hidden fade-in", className)}>
      <div className="flex flex-col gap-3 border-b border-white/8 px-5 py-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h3 className="text-display text-sm font-semibold tracking-wide text-slate-100">
            Tag performance heatmap
          </h3>
          <p className="mt-1 text-xs text-slate-400">
            Pass rates by category across architecture variants
          </p>
        </div>
        <label className="inline-flex items-center gap-2 text-xs text-slate-400">
          <ArrowDownWideNarrow className="h-3.5 w-3.5 text-violet-300" />
          <span className="sr-only">Sort by</span>
          <select
            value={sortMode}
            onChange={(e) => setSortMode(e.target.value as SortMode)}
            className="rounded-lg border border-white/10 bg-surface-900 px-2.5 py-1.5 text-xs text-slate-200 outline-none focus:border-violet-500/50"
          >
            {SORT_OPTIONS.map((option) => (
              <option key={option.id} value={option.id}>
                {option.label}
              </option>
            ))}
          </select>
        </label>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full min-w-[560px] border-collapse text-left text-sm">
          <thead>
            <tr className="border-b border-white/8 text-[11px] uppercase tracking-[0.12em] text-slate-500">
              <th className="px-5 py-3 font-medium">Tag</th>
              <th className="px-3 py-3 font-medium">{VARIANT_LABELS.multi_agent}</th>
              <th className="px-3 py-3 font-medium">{VARIANT_LABELS.single_agent}</th>
              <th className="px-3 py-3 font-medium">{VARIANT_LABELS.no_reviewer}</th>
              <th className="px-5 py-3 font-medium">Δ Multi−Single</th>
            </tr>
          </thead>
          <tbody>
            {rows.length === 0 ? (
              <tr>
                <td colSpan={5} className="px-5 py-8 text-center text-sm text-slate-500">
                  No tag comparison data available.
                </td>
              </tr>
            ) : (
              rows.map(({ tag, rates, advantage }) => (
                <tr key={tag} className="border-b border-white/5 last:border-0">
                  <td className="px-5 py-2.5 font-medium text-slate-200">{tag}</td>
                  {(
                    ["multi_agent", "single_agent", "no_reviewer"] as const
                  ).map((key) => (
                    <td key={key} className="px-3 py-2.5">
                      <span
                        className="inline-flex min-w-[4.25rem] justify-center rounded-md px-2 py-1 mono text-xs font-medium"
                        style={heatStyle(rates[key])}
                      >
                        {formatPercent(rates[key], 0)}
                      </span>
                    </td>
                  ))}
                  <td className="px-5 py-2.5 mono text-xs">
                    <span
                      className={cn(
                        advantage > 0
                          ? "text-emerald-300"
                          : advantage < 0
                            ? "text-rose-300"
                            : "text-slate-400",
                      )}
                    >
                      {advantage > 0 ? "+" : ""}
                      {formatPercent(advantage, 0)}
                    </span>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
