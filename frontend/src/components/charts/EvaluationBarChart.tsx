import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { cn, formatNumber } from "@/utils/format";

export function EvaluationBarChart({
  title,
  data,
  valueFormatter = (n) => formatNumber(n, 2),
  color = "#8b5cf6",
  className,
}: {
  title: string;
  data: Array<{ name: string; value: number }>;
  valueFormatter?: (n: number) => string;
  color?: string;
  className?: string;
}) {
  return (
    <div className={cn("panel p-5 fade-in", className)}>
      <h3 className="text-display text-sm font-semibold tracking-wide text-slate-100">
        {title}
      </h3>
      <div className="mt-4 h-[280px] w-full">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data} margin={{ top: 8, right: 8, left: 0, bottom: 4 }}>
            <CartesianGrid stroke="rgba(148,163,184,0.12)" vertical={false} />
            <XAxis
              dataKey="name"
              tick={{ fill: "#94a3b8", fontSize: 12 }}
              axisLine={{ stroke: "rgba(148,163,184,0.2)" }}
              tickLine={false}
            />
            <YAxis
              tick={{ fill: "#94a3b8", fontSize: 12 }}
              axisLine={false}
              tickLine={false}
              tickFormatter={valueFormatter}
              width={56}
            />
            <Tooltip
              cursor={{ fill: "rgba(139,92,246,0.08)" }}
              contentStyle={{
                background: "#0c1018",
                border: "1px solid rgba(255,255,255,0.1)",
                borderRadius: 10,
                color: "#e2e8f0",
                fontSize: 12,
              }}
              formatter={(value) => [
                valueFormatter(typeof value === "number" ? value : Number(value)),
                "Value",
              ]}
            />
            <Bar dataKey="value" fill={color} radius={[6, 6, 0, 0]} maxBarSize={56} />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
