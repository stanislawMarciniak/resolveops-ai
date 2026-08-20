import type { CaseStage } from "@/types";
import { STAGE_COLORS, cn } from "@/utils/format";

export function StageBadge({ stage }: { stage: CaseStage | string }) {
  const color =
    STAGE_COLORS[stage as CaseStage] ??
    "bg-slate-500/20 text-slate-300 border-slate-500/30";

  return (
    <span
      className={cn(
        "inline-flex items-center rounded-md border px-2 py-0.5 text-[11px] font-semibold tracking-wide",
        color,
      )}
    >
      {stage}
    </span>
  );
}
