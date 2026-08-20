import { AlertTriangle, Inbox, WifiOff } from "lucide-react";
import type { ReactNode } from "react";

export function EmptyState({
  title,
  description,
  action,
}: {
  title: string;
  description?: string;
  action?: ReactNode;
}) {
  return (
    <div className="panel flex flex-col items-center justify-center gap-3 px-6 py-16 text-center">
      <Inbox className="h-8 w-8 text-slate-500" />
      <div className="text-display text-lg font-semibold text-slate-100">{title}</div>
      {description ? <p className="max-w-md text-sm text-slate-400">{description}</p> : null}
      {action}
    </div>
  );
}

export function ErrorPanel({
  title = "Something went wrong",
  message,
  onRetry,
}: {
  title?: string;
  message: string;
  onRetry?: () => void;
}) {
  const offline = /failed to fetch|network|unavailable/i.test(message);

  return (
    <div className="panel border-rose-500/30 bg-rose-500/5 px-5 py-6">
      <div className="flex items-start gap-3">
        {offline ? (
          <WifiOff className="mt-0.5 h-5 w-5 text-rose-300" />
        ) : (
          <AlertTriangle className="mt-0.5 h-5 w-5 text-rose-300" />
        )}
        <div className="min-w-0 flex-1">
          <div className="text-sm font-semibold text-rose-100">{title}</div>
          <p className="mt-1 text-sm text-rose-200/80">{message}</p>
          {onRetry ? (
            <button
              type="button"
              onClick={onRetry}
              className="mt-3 rounded-md border border-rose-400/30 bg-rose-500/10 px-3 py-1.5 text-xs font-medium text-rose-100 hover:bg-rose-500/20"
            >
              Retry
            </button>
          ) : null}
        </div>
      </div>
    </div>
  );
}
