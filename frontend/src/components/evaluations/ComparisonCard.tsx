import { ArrowRight, Gauge, Timer, Wallet } from "lucide-react";
import { cn, formatPercent } from "@/utils/format";

export function ComparisonCard({
  multiPass,
  singlePass,
  delta,
  className,
}: {
  multiPass: number;
  singlePass: number;
  delta: number;
  className?: string;
}) {
  const multiPct = Math.max(0, Math.min(100, multiPass * 100));
  const singlePct = Math.max(0, Math.min(100, singlePass * 100));
  const deltaPositive = delta >= 0;

  return (
    <div className={cn("panel overflow-hidden fade-in", className)}>
      <div className="border-b border-white/8 bg-gradient-to-br from-violet-500/10 to-transparent px-5 py-4">
        <h3 className="text-display text-sm font-semibold tracking-wide text-slate-100">
          Multi-Agent vs Single-Agent
        </h3>
        <p className="mt-1 text-xs text-slate-400">
          Quality lift from specialized roles and independent review
        </p>
      </div>

      <div className="grid gap-6 p-5 md:grid-cols-[1fr_auto_1fr] md:items-center">
        <VariantColumn
          label="Multi-Agent"
          value={multiPass}
          barPct={multiPct}
          accent="violet"
        />

        <div className="flex flex-col items-center gap-2">
          <div
            className={cn(
              "rounded-xl border px-4 py-3 text-center",
              deltaPositive
                ? "border-emerald-500/30 bg-emerald-500/10"
                : "border-rose-500/30 bg-rose-500/10",
            )}
          >
            <div className="text-[10px] uppercase tracking-[0.14em] text-slate-400">
              Pass-rate delta
            </div>
            <div
              className={cn(
                "mt-1 text-display text-2xl font-semibold",
                deltaPositive ? "text-emerald-300" : "text-rose-300",
              )}
            >
              {deltaPositive ? "+" : ""}
              {formatPercent(delta, 0)}
            </div>
          </div>
          <ArrowRight className="hidden h-4 w-4 text-slate-600 md:block" />
        </div>

        <VariantColumn
          label="Single-Agent"
          value={singlePass}
          barPct={singlePct}
          accent="slate"
        />
      </div>

      <div className="flex flex-wrap gap-2 border-t border-white/8 px-5 py-4">
        <TradeoffChip icon={Gauge} label="Quality↑" tone="good" />
        <TradeoffChip icon={Wallet} label="Cost↑" tone="warn" />
        <TradeoffChip icon={Timer} label="Latency↑" tone="warn" />
        <span className="self-center text-xs text-slate-500">
          Higher accuracy with more model calls and spend
        </span>
      </div>
    </div>
  );
}

function VariantColumn({
  label,
  value,
  barPct,
  accent,
}: {
  label: string;
  value: number;
  barPct: number;
  accent: "violet" | "slate";
}) {
  return (
    <div>
      <div className="text-xs font-medium uppercase tracking-[0.14em] text-slate-400">
        {label}
      </div>
      <div className="mt-2 text-display text-3xl font-semibold text-slate-50">
        {formatPercent(value, 0)}
      </div>
      <div className="mt-3 h-2 overflow-hidden rounded-full bg-white/5">
        <div
          className={cn(
            "h-full rounded-full transition-all",
            accent === "violet"
              ? "bg-gradient-to-r from-violet-500 to-violet-400"
              : "bg-gradient-to-r from-slate-500 to-slate-400",
          )}
          style={{ width: `${barPct}%` }}
        />
      </div>
    </div>
  );
}

function TradeoffChip({
  icon: Icon,
  label,
  tone,
}: {
  icon: typeof Gauge;
  label: string;
  tone: "good" | "warn";
}) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded-md border px-2.5 py-1 text-xs font-medium",
        tone === "good"
          ? "border-emerald-500/30 bg-emerald-500/10 text-emerald-200"
          : "border-amber-500/30 bg-amber-500/10 text-amber-200",
      )}
    >
      <Icon className="h-3.5 w-3.5" />
      {label}
    </span>
  );
}
