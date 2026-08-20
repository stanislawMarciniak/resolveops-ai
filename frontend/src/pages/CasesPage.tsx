import { useMemo, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { Search } from "lucide-react";
import { api } from "@/api/client";
import { useAsync } from "@/hooks/useAsync";
import { Breadcrumbs } from "@/components/layout/Breadcrumbs";
import { StageBadge } from "@/components/ui/StageBadge";
import { PageSkeleton } from "@/components/ui/Skeleton";
import { ErrorPanel, EmptyState } from "@/components/ui/ErrorPanel";
import type { CaseStage, CaseState } from "@/types";
import {
  STAGE_ORDER,
  formatDateTime,
  formatUsd,
  shortId,
} from "@/utils/format";

export function CasesPage() {
  const [params, setParams] = useSearchParams();
  const customerFilter = params.get("customer") ?? "";
  const stageFilter = params.get("stage") ?? "";
  const [search, setSearch] = useState("");
  const [resolvedOnly, setResolvedOnly] = useState(false);
  const [hasPlan, setHasPlan] = useState(false);
  const [hasReview, setHasReview] = useState(false);
  const [approvalRequired, setApprovalRequired] = useState(false);

  const cases = useAsync(
    () =>
      api.listCases({
        customer_id: customerFilter || undefined,
        stage: stageFilter || undefined,
        limit: 200,
      }),
    [customerFilter, stageFilter],
  );

  const filtered = useMemo(() => {
    let items = cases.data?.items ?? [];

    if (search.trim()) {
      const q = search.trim().toLowerCase();
      items = items.filter(
        (item) =>
          item.case_id.toLowerCase().includes(q) ||
          item.customer_id.toLowerCase().includes(q) ||
          item.description.toLowerCase().includes(q),
      );
    }

    if (resolvedOnly) {
      items = items.filter((item) =>
        ["RESOLVED", "ESCALATED", "FAILED"].includes(item.stage),
      );
    }

    if (hasPlan) items = items.filter((item) => Boolean(item.resolution_plan));
    if (hasReview) items = items.filter((item) => Boolean(item.review));
    if (approvalRequired) {
      items = items.filter(
        (item) =>
          item.stage === "AWAITING_APPROVAL" ||
          item.resolution_plan?.requires_approval,
      );
    }

    return items;
  }, [cases.data, search, resolvedOnly, hasPlan, hasReview, approvalRequired]);

  const customers = useMemo(() => {
    const set = new Set((cases.data?.items ?? []).map((c) => c.customer_id));
    if (customerFilter) set.add(customerFilter);
    return Array.from(set).sort();
  }, [cases.data, customerFilter]);

  if (cases.loading) return <PageSkeleton />;
  if (cases.error) {
    return (
      <ErrorPanel
        title="Could not load cases"
        message={cases.error}
        onRetry={cases.reload}
      />
    );
  }

  return (
    <div className="fade-in space-y-5">
      <Breadcrumbs items={[{ label: "Cases" }]} />

      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="text-display text-2xl font-semibold text-slate-50">
            Cases
          </h1>
          <p className="mt-1 text-sm text-slate-400">
            {cases.data?.total ?? 0} persisted CaseState records · showing{" "}
            {filtered.length}
          </p>
        </div>
      </div>

      <div className="panel grid gap-3 p-4 md:grid-cols-2 xl:grid-cols-4">
        <label className="block text-xs text-slate-400">
          Search
          <div className="relative mt-1">
            <Search className="pointer-events-none absolute left-2.5 top-2.5 h-4 w-4 text-slate-500" />
            <input
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="ID, customer, description"
              className="w-full rounded-lg border border-white/10 bg-surface-900 py-2 pl-8 pr-3 text-sm text-slate-100 outline-none focus:border-violet-500/50"
            />
          </div>
        </label>

        <label className="block text-xs text-slate-400">
          Customer
          <select
            value={customerFilter}
            onChange={(e) => {
              const next = new URLSearchParams(params);
              if (e.target.value) next.set("customer", e.target.value);
              else next.delete("customer");
              setParams(next);
            }}
            className="mt-1 w-full rounded-lg border border-white/10 bg-surface-900 px-3 py-2 text-sm text-slate-100"
          >
            <option value="">All</option>
            {customers.map((customer) => (
              <option key={customer} value={customer}>
                {customer}
              </option>
            ))}
          </select>
        </label>

        <label className="block text-xs text-slate-400">
          Stage
          <select
            value={stageFilter}
            onChange={(e) => {
              const next = new URLSearchParams(params);
              if (e.target.value) next.set("stage", e.target.value);
              else next.delete("stage");
              setParams(next);
            }}
            className="mt-1 w-full rounded-lg border border-white/10 bg-surface-900 px-3 py-2 text-sm text-slate-100"
          >
            <option value="">All</option>
            {STAGE_ORDER.map((stage) => (
              <option key={stage} value={stage}>
                {stage}
              </option>
            ))}
          </select>
        </label>

        <div className="flex flex-wrap items-center gap-3 pt-5 text-xs text-slate-300">
          <Toggle label="Terminal" checked={resolvedOnly} onChange={setResolvedOnly} />
          <Toggle label="Has plan" checked={hasPlan} onChange={setHasPlan} />
          <Toggle label="Has review" checked={hasReview} onChange={setHasReview} />
          <Toggle
            label="Approval"
            checked={approvalRequired}
            onChange={setApprovalRequired}
          />
        </div>
      </div>

      {filtered.length === 0 ? (
        <EmptyState
          title="No cases match"
          description="Adjust filters or run evaluations to persist CaseState rows."
        />
      ) : (
        <div className="panel overflow-hidden">
          <div className="overflow-x-auto">
            <table className="min-w-full text-left text-sm">
              <thead className="border-b border-white/8 bg-white/3 text-xs uppercase tracking-wider text-slate-500">
                <tr>
                  <th className="px-4 py-3 font-medium">Case</th>
                  <th className="px-4 py-3 font-medium">Customer</th>
                  <th className="px-4 py-3 font-medium">Description</th>
                  <th className="px-4 py-3 font-medium">Stage</th>
                  <th className="px-4 py-3 font-medium">Updated</th>
                  <th className="px-4 py-3 font-medium">Calls</th>
                  <th className="px-4 py-3 font-medium">Cost</th>
                </tr>
              </thead>
              <tbody>
                {filtered.map((item) => (
                  <CaseRow key={item.case_id} item={item} />
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}

function Toggle({
  label,
  checked,
  onChange,
}: {
  label: string;
  checked: boolean;
  onChange: (value: boolean) => void;
}) {
  return (
    <label className="inline-flex cursor-pointer items-center gap-1.5">
      <input
        type="checkbox"
        checked={checked}
        onChange={(e) => onChange(e.target.checked)}
        className="rounded border-white/20 bg-surface-900 text-violet-500"
      />
      {label}
    </label>
  );
}

function CaseRow({ item }: { item: CaseState }) {
  return (
    <tr className="border-b border-white/5 transition hover:bg-violet-500/5">
      <td className="px-4 py-3">
        <Link
          to={`/cases/${item.case_id}`}
          className="mono text-xs text-violet-300 hover:text-violet-200"
        >
          {shortId(item.case_id, 10)}
        </Link>
      </td>
      <td className="px-4 py-3 font-medium text-slate-100">{item.customer_id}</td>
      <td className="max-w-md px-4 py-3 text-slate-400">
        <span className="line-clamp-2">{item.description}</span>
      </td>
      <td className="px-4 py-3">
        <StageBadge stage={item.stage as CaseStage} />
      </td>
      <td className="px-4 py-3 text-xs text-slate-400">
        {formatDateTime(item.updated_at)}
      </td>
      <td className="px-4 py-3 text-xs text-slate-300">
        m{item.model_calls} / t{item.tool_calls}
      </td>
      <td className="px-4 py-3 text-xs text-slate-300">
        {formatUsd(item.estimated_cost_usd)}
      </td>
    </tr>
  );
}
