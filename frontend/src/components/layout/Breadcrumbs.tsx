import { Link, useLocation } from "react-router-dom";
import { ChevronRight } from "lucide-react";
import { cn } from "@/utils/format";

export function Breadcrumbs({
  items,
}: {
  items: Array<{ label: string; to?: string }>;
}) {
  const location = useLocation();

  return (
    <nav className="mb-4 flex flex-wrap items-center gap-1 text-xs text-slate-400">
      {items.map((item, index) => {
        const last = index === items.length - 1;
        return (
          <span key={`${item.label}-${index}`} className="inline-flex items-center gap-1">
            {index > 0 ? <ChevronRight className="h-3 w-3 text-slate-600" /> : null}
            {item.to && !last ? (
              <Link
                to={item.to}
                className={cn(
                  "rounded px-1 py-0.5 hover:text-slate-200",
                  location.pathname === item.to && "text-slate-200",
                )}
              >
                {item.label}
              </Link>
            ) : (
              <span className={cn(last && "text-slate-200")}>{item.label}</span>
            )}
          </span>
        );
      })}
    </nav>
  );
}
