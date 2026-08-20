import { NavLink, Outlet } from "react-router-dom";
import {
  Activity,
  Boxes,
  FlaskConical,
  GitBranch,
  Info,
  LayoutDashboard,
  Network,
  Search,
  Sparkles,
} from "lucide-react";
import { api } from "@/api/client";
import { useAsync } from "@/hooks/useAsync";
import { ErrorBoundary } from "@/components/ui/ErrorBoundary";
import { cn } from "@/utils/format";

const NAV = [
  { to: "/", label: "Overview", icon: LayoutDashboard, end: true },
  { to: "/cases", label: "Cases", icon: Search },
  { to: "/showcase", label: "Showcase", icon: Sparkles },
  { to: "/evaluations", label: "Evaluations", icon: FlaskConical },
  { to: "/architecture", label: "Architecture", icon: Network },
  { to: "/observability", label: "Observability", icon: Activity },
  { to: "/about", label: "About Project", icon: Info },
];

function StatusDot({ status }: { status: string }) {
  const color =
    status === "ok"
      ? "bg-emerald-400 shadow-[0_0_8px_rgba(52,211,153,0.6)]"
      : status === "degraded"
        ? "bg-amber-400"
        : "bg-rose-400";

  return <span className={cn("inline-block h-2 w-2 rounded-full", color)} />;
}

export function AppShell() {
  const status = useAsync(() => api.systemStatus(), []);
  const health = useAsync(() => api.health(), []);

  const environment =
    status.data?.environment ?? health.data?.environment ?? "unknown";

  return (
    <div className="flex min-h-screen">
      <aside className="sticky top-0 flex h-screen w-64 shrink-0 flex-col border-r border-white/8 bg-surface-900/90 backdrop-blur-md">
        <div className="border-b border-white/8 px-5 py-5">
          <div className="flex items-center gap-2">
            <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-violet-500/20 text-violet-300">
              <Boxes className="h-5 w-5" />
            </div>
            <div>
              <div className="text-display text-sm font-semibold tracking-wide text-slate-50">
                ResolveOps AI
              </div>
              <div className="text-[11px] text-slate-500">Enterprise case resolution</div>
            </div>
          </div>
        </div>

        <nav className="flex-1 space-y-1 overflow-y-auto px-3 py-4">
          {NAV.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.end}
              className={({ isActive }) =>
                cn(
                  "flex items-center gap-2.5 rounded-lg px-3 py-2 text-sm transition",
                  isActive
                    ? "bg-violet-500/15 text-violet-100 shadow-[inset_0_0_0_1px_rgba(139,92,246,0.25)]"
                    : "text-slate-400 hover:bg-white/5 hover:text-slate-200",
                )
              }
            >
              <item.icon className="h-4 w-4 shrink-0" />
              {item.label}
            </NavLink>
          ))}

          <div className="px-3 pt-4">
            <div className="mb-2 text-[10px] font-semibold uppercase tracking-[0.16em] text-slate-600">
              Interview demos
            </div>
            <NavLink
              to="/cases?customer=ACME"
              className="flex items-center gap-2.5 rounded-lg px-3 py-2 text-sm text-slate-400 hover:bg-white/5 hover:text-slate-200"
            >
              <GitBranch className="h-4 w-4" />
              ACME walkthrough
            </NavLink>
          </div>
        </nav>

        <div className="space-y-2 border-t border-white/8 px-4 py-4 text-xs text-slate-400">
          <div className="flex items-center justify-between">
            <span>Backend</span>
            <span className="inline-flex items-center gap-1.5">
              <StatusDot status={health.data?.status === "ok" ? "ok" : health.error ? "down" : "degraded"} />
              {health.data?.status === "ok" ? "online" : health.error ? "offline" : "…"}
            </span>
          </div>
          <div className="flex items-center justify-between">
            <span>MCP</span>
            <span className="inline-flex items-center gap-1.5">
              <StatusDot status={status.data?.mcp.status ?? "degraded"} />
              {status.data?.mcp.status ?? "…"}
            </span>
          </div>
          <div className="rounded-md border border-white/8 bg-white/3 px-2 py-1.5 text-[11px] uppercase tracking-wider text-slate-500">
            env · {environment}
          </div>
        </div>
      </aside>

      <main className="min-w-0 flex-1">
        <div className="mx-auto max-w-[1400px] px-6 py-6 lg:px-8">
          <ErrorBoundary>
            <Outlet />
          </ErrorBoundary>
        </div>
      </main>
    </div>
  );
}
