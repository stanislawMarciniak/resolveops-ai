import type { ReactNode } from "react";
import { cn } from "@/utils/format";

export function MetricCard({
  label,
  value,
  hint,
  accent = "violet",
  className,
}: {
  label: string;
  value: ReactNode;
  hint?: string;
  accent?: "violet" | "green" | "amber" | "red" | "blue" | "slate";
  className?: string;
}) {
  const accents = {
    violet: "from-violet-500/15 to-transparent border-violet-500/20",
    green: "from-emerald-500/15 to-transparent border-emerald-500/20",
    amber: "from-amber-500/15 to-transparent border-amber-500/20",
    red: "from-rose-500/15 to-transparent border-rose-500/20",
    blue: "from-sky-500/15 to-transparent border-sky-500/20",
    slate: "from-slate-500/10 to-transparent border-white/8",
  };

  return (
    <div
      className={cn(
        "panel relative overflow-hidden bg-gradient-to-br p-4",
        accents[accent],
        className,
      )}
    >
      <div className="text-xs font-medium uppercase tracking-[0.14em] text-slate-400">
        {label}
      </div>
      <div className="mt-2 text-display text-2xl font-semibold text-slate-50">
        {value}
      </div>
      {hint ? <div className="mt-1 text-xs text-slate-400">{hint}</div> : null}
    </div>
  );
}
