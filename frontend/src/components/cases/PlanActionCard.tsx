import { CheckCircle2, ShieldAlert } from "lucide-react";
import type { PlannedAction, RiskLevel } from "@/types";
import { cn } from "@/utils/format";

const RISK_STYLES: Record<RiskLevel, string> = {
  LOW: "border-emerald-500/30 bg-emerald-500/10 text-emerald-200",
  MEDIUM: "border-amber-500/30 bg-amber-500/10 text-amber-200",
  HIGH: "border-rose-500/30 bg-rose-500/10 text-rose-200",
};

export function PlanActionCard({
  action,
  index,
  className,
}: {
  action: PlannedAction;
  index: number;
  className?: string;
}) {
  const argEntries = Object.entries(action.arguments);

  return (
    <div className={cn("panel overflow-hidden fade-in", className)}>
      <div className="flex items-start gap-3 border-b border-white/8 px-4 py-3">
        <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg border border-violet-500/30 bg-violet-500/15 text-display text-sm font-semibold text-violet-200">
          {index + 1}
        </div>
        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-center gap-2">
            <code className="mono text-sm font-medium text-slate-100">
              {action.tool_name}
            </code>
            <span
              className={cn(
                "inline-flex items-center rounded-md border px-2 py-0.5 text-[11px] font-semibold tracking-wide",
                RISK_STYLES[action.risk],
              )}
            >
              {action.risk} risk
            </span>
            <span
              className={cn(
                "inline-flex items-center gap-1 rounded-md border px-2 py-0.5 text-[11px] font-semibold tracking-wide",
                action.requires_approval
                  ? "border-amber-500/30 bg-amber-500/10 text-amber-200"
                  : "border-emerald-500/30 bg-emerald-500/10 text-emerald-200",
              )}
            >
              {action.requires_approval ? (
                <>
                  <ShieldAlert className="h-3 w-3" />
                  Approval required
                </>
              ) : (
                <>
                  <CheckCircle2 className="h-3 w-3" />
                  Auto-executable
                </>
              )}
            </span>
          </div>
          <p className="mt-2 text-sm leading-relaxed text-slate-300">{action.reason}</p>
        </div>
      </div>

      <div className="grid gap-4 p-4 md:grid-cols-2">
        <div>
          <div className="text-[11px] font-medium uppercase tracking-[0.14em] text-slate-500">
            Arguments
          </div>
          {argEntries.length === 0 ? (
            <p className="mt-2 text-xs text-slate-500">No arguments</p>
          ) : (
            <dl className="mt-2 space-y-1.5">
              {argEntries.map(([key, value]) => (
                <div
                  key={key}
                  className="flex gap-2 rounded-md border border-white/6 bg-surface-900/50 px-2.5 py-1.5"
                >
                  <dt className="shrink-0 mono text-[11px] text-slate-500">{key}</dt>
                  <dd className="min-w-0 break-all mono text-[11px] text-slate-200">
                    {formatArg(value)}
                  </dd>
                </div>
              ))}
            </dl>
          )}
        </div>

        <div>
          <div className="text-[11px] font-medium uppercase tracking-[0.14em] text-slate-500">
            Supporting evidence
          </div>
          {action.evidence_ids.length === 0 ? (
            <p className="mt-2 text-xs text-slate-500">No linked evidence</p>
          ) : (
            <div className="mt-2 flex flex-wrap gap-1.5">
              {action.evidence_ids.map((id) => (
                <span
                  key={id}
                  className="rounded-md border border-violet-500/25 bg-violet-500/10 px-2 py-0.5 mono text-[11px] text-violet-200"
                >
                  {id}
                </span>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function formatArg(value: string | number | boolean | null): string {
  if (value === null) return "null";
  if (typeof value === "string") return value;
  return String(value);
}
