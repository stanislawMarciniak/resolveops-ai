import { useState } from "react";
import { ChevronDown, ChevronRight } from "lucide-react";
import { CopyButton } from "@/components/ui/CopyButton";
import { cn } from "@/utils/format";

export function JsonViewer({
  data,
  title = "JSON",
  initiallyOpen = true,
  className,
}: {
  data: unknown;
  title?: string;
  initiallyOpen?: boolean;
  className?: string;
}) {
  const [open, setOpen] = useState(initiallyOpen);
  const text = JSON.stringify(data, null, 2);

  return (
    <div className={cn("panel overflow-hidden", className)}>
      <div className="flex items-center justify-between border-b border-white/8 px-4 py-3">
        <button
          type="button"
          className="inline-flex items-center gap-2 text-sm font-medium text-slate-200"
          onClick={() => setOpen((value) => !value)}
        >
          {open ? <ChevronDown className="h-4 w-4" /> : <ChevronRight className="h-4 w-4" />}
          {title}
        </button>
        <CopyButton value={text} label="Copy" />
      </div>
      {open ? (
        <pre className="max-h-[560px] overflow-auto p-4 text-xs leading-relaxed text-slate-300 mono">
          {text}
        </pre>
      ) : null}
    </div>
  );
}
