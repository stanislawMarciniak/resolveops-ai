import {
  CartesianGrid,
  LabelList,
  ResponsiveContainer,
  Scatter,
  ScatterChart,
  Tooltip,
  XAxis,
  YAxis,
  ZAxis,
} from "recharts";
import { cn, formatPercent, formatUsd } from "@/utils/format";

export type QualityCostPoint = {
  name: string;
  cost: number;
  passRate: number;
  color: string;
};

export function QualityCostScatter({
  points,
  className,
}: {
  points: QualityCostPoint[];
  className?: string;
}) {
  return (
    <div className={cn("panel p-5 fade-in", className)}>
      <div className="flex items-end justify-between gap-3">
        <div>
          <h3 className="text-display text-sm font-semibold tracking-wide text-slate-100">
            Quality vs Cost
          </h3>
          <p className="mt-1 text-xs text-slate-400">
            Pass rate against average cost per case
          </p>
        </div>
      </div>

      <div className="mt-4 h-[280px] w-full">
        <ResponsiveContainer width="100%" height="100%">
          <ScatterChart margin={{ top: 20, right: 24, left: 8, bottom: 12 }}>
            <CartesianGrid stroke="rgba(148,163,184,0.12)" />
            <XAxis
              type="number"
              dataKey="cost"
              name="Cost"
              tick={{ fill: "#94a3b8", fontSize: 12 }}
              axisLine={{ stroke: "rgba(148,163,184,0.2)" }}
              tickLine={false}
              tickFormatter={(v) => formatUsd(Number(v), 3)}
              label={{
                value: "Avg cost (USD)",
                position: "insideBottom",
                offset: -4,
                fill: "#64748b",
                fontSize: 11,
              }}
            />
            <YAxis
              type="number"
              dataKey="passRate"
              name="Pass rate"
              domain={[0, 1]}
              tick={{ fill: "#94a3b8", fontSize: 12 }}
              axisLine={false}
              tickLine={false}
              tickFormatter={(v) => formatPercent(Number(v), 0)}
              width={48}
              label={{
                value: "Pass rate",
                angle: -90,
                position: "insideLeft",
                fill: "#64748b",
                fontSize: 11,
              }}
            />
            <ZAxis range={[120, 120]} />
            <Tooltip
              cursor={{ strokeDasharray: "4 4", stroke: "rgba(148,163,184,0.35)" }}
              contentStyle={{
                background: "#0c1018",
                border: "1px solid rgba(255,255,255,0.1)",
                borderRadius: 10,
                color: "#e2e8f0",
                fontSize: 12,
              }}
              formatter={(value, name) => {
                const n = typeof value === "number" ? value : Number(value);
                if (name === "passRate" || name === "Pass rate") {
                  return [formatPercent(n, 1), "Pass rate"];
                }
                if (name === "cost" || name === "Cost") {
                  return [formatUsd(n, 3), "Avg cost"];
                }
                return [String(value), String(name)];
              }}
              labelFormatter={(_, payload) => {
                const point = payload?.[0]?.payload as QualityCostPoint | undefined;
                return point?.name ?? "";
              }}
            />
            {points.map((point) => (
              <Scatter
                key={point.name}
                name={point.name}
                data={[point]}
                fill={point.color}
              >
                <LabelList
                  dataKey="name"
                  position="top"
                  offset={10}
                  style={{ fill: "#cbd5e1", fontSize: 11 }}
                />
              </Scatter>
            ))}
          </ScatterChart>
        </ResponsiveContainer>
      </div>

      <div className="mt-3 flex flex-wrap gap-3">
        {points.map((point) => (
          <div
            key={point.name}
            className="inline-flex items-center gap-2 text-xs text-slate-400"
          >
            <span
              className="h-2.5 w-2.5 rounded-full"
              style={{ backgroundColor: point.color }}
            />
            <span className="text-slate-300">{point.name}</span>
            <span className="mono text-slate-500">
              {formatPercent(point.passRate, 0)} · {formatUsd(point.cost, 3)}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}
