import { useState } from "react";
import { ChevronDown, ChevronRight, Database } from "lucide-react";
import type { Evidence } from "@/types";
import { SOURCE_COLORS, cn } from "@/utils/format";

export function EvidenceCard({
  evidence,
  className,
}: {
  evidence: Evidence;
  className?: string;
}) {
  const [open, setOpen] = useState(false);
  const sourceClass =
    SOURCE_COLORS[evidence.source] ??
    "border-slate-500/40 bg-slate-500/10 text-slate-200";
  const detailEntries = Object.entries(evidence.details);

  return (
    <div className={cn("panel overflow-hidden fade-in", className)}>
      <div className="flex items-start gap-3 p-4">
        <div
          className={cn(
            "mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-lg border",
            sourceClass,
          )}
        >
          <Database className="h-4 w-4" />
        </div>
        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-center gap-2">
            <span className="mono text-xs text-violet-300">{evidence.evidence_id}</span>
            <span
              className={cn(
                "inline-flex items-center rounded-md border px-2 py-0.5 text-[11px] font-semibold tracking-wide",
                sourceClass,
              )}
            >
              {evidence.source}
            </span>
          </div>
          <p className="mt-2 text-sm leading-relaxed text-slate-200">
            {evidence.description}
          </p>
        </div>
      </div>

      <div className="border-t border-white/8">
        <button
          type="button"
          onClick={() => setOpen((value) => !value)}
          className="flex w-full items-center gap-2 px-4 py-2.5 text-left text-xs font-medium text-slate-400 transition hover:bg-white/[0.03] hover:text-slate-200"
        >
          {open ? (
            <ChevronDown className="h-3.5 w-3.5" />
          ) : (
            <ChevronRight className="h-3.5 w-3.5" />
          )}
          Details
          <span className="mono text-slate-600">
            ({detailEntries.length} field{detailEntries.length === 1 ? "" : "s"})
          </span>
        </button>
        {open ? (
          <pre className="max-h-72 overflow-auto border-t border-white/6 bg-surface-900/70 px-4 py-3 text-xs leading-relaxed text-slate-300 mono">
            {JSON.stringify(evidence.details, null, 2)}
          </pre>
        ) : null}
      </div>
    </div>
  );
}
