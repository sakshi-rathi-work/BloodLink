import React from "react";
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
} from "recharts";

export default function TrendsLineChart({ data = [], granularity = "day" }) {
  if (!data || data.length === 0) {
    return (
      <div className="flex h-64 items-center justify-center text-sm text-slate-400 bg-slate-50 rounded-xl border border-dashed border-slate-200">
        No trend data available for this range
      </div>
    );
  }

  const formatTick = (val) => {
    if (!val) return "";
    const parts = val.split("-");
    if (granularity === "month") {
      const months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
      const mIdx = parseInt(parts[1], 10) - 1;
      return `${months[mIdx]} '${parts[0].slice(2)}`;
    }
    return `${parts[1]}/${parts[2]}`;
  };

  return (
    <div className="h-72 w-full">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={data} margin={{ top: 10, right: 20, left: -10, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
          <XAxis
            dataKey="period_start"
            tick={{ fontSize: 11, fill: "#64748b" }}
            tickFormatter={formatTick}
          />
          <YAxis
            tick={{ fontSize: 11, fill: "#64748b" }}
            allowDecimals={false}
          />
          <Tooltip
            contentStyle={{
              backgroundColor: "#ffffff",
              borderColor: "#e2e8f0",
              borderRadius: "0.75rem",
              boxShadow: "0 10px 15px -3px rgba(0, 0, 0, 0.1)",
              fontSize: "12px",
            }}
            formatter={(val, name) => [`${val} units`, name === "donations" ? "Donations (Inflow)" : "Issues (Outflow)"]}
            labelFormatter={(label) => `Period: ${label}`}
          />
          <Legend
            verticalAlign="top"
            height={36}
            wrapperStyle={{ fontSize: "12px", color: "#475569" }}
          />
          <Line
            type="monotone"
            dataKey="donations"
            name="Donations (Inflow)"
            stroke="#10b981"
            strokeWidth={2.5}
            dot={{ r: 2.5, fill: "#10b981" }}
            activeDot={{ r: 5, fill: "#059669" }}
          />
          <Line
            type="monotone"
            dataKey="issues"
            name="Issues (Outflow)"
            stroke="#dc2626"
            strokeWidth={2.5}
            dot={{ r: 2.5, fill: "#dc2626" }}
            activeDot={{ r: 5, fill: "#b91c1c" }}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
