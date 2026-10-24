import React from "react";
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
} from "recharts";

export default function StockBarChart({ data = [] }) {
  if (!data || data.length === 0) {
    return (
      <div className="flex h-64 items-center justify-center text-sm text-slate-400 bg-slate-50 rounded-xl border border-dashed border-slate-200">
        No stock data available
      </div>
    );
  }

  const chartData = data.map((item) => ({
    bloodGroup: item.blood_group,
    availableUnits: item.available_units,
    safeMinimum: item.safe_minimum,
    isLow: item.is_low,
  }));

  const maxVal = Math.max(...chartData.map((d) => Math.max(d.availableUnits, d.safeMinimum)), 10);

  return (
    <div className="h-72 w-full">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={chartData} margin={{ top: 10, right: 20, left: -10, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
          <XAxis
            dataKey="bloodGroup"
            tick={{ fontSize: 12, fill: "#475569", fontWeight: 600 }}
          />
          <YAxis
            domain={[0, Math.ceil(maxVal * 1.15)]}
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
            formatter={(value, name) => [
              `${value} units`,
              name === "availableUnits" ? "Available Units" : "Safe Minimum",
            ]}
            labelFormatter={(label) => `Blood Group: ${label}`}
          />
          <Legend
            verticalAlign="top"
            height={36}
            wrapperStyle={{ fontSize: "12px", color: "#475569" }}
            payload={[
              { value: "Sufficient Stock", type: "rect", color: "#0284c7" },
              { value: "Low Stock (< Safe Min)", type: "rect", color: "#ef4444" },
            ]}
          />
          <Bar dataKey="availableUnits" name="Stock Units" radius={[6, 6, 0, 0]}>
            {chartData.map((entry, index) => (
              <Cell
                key={`cell-${index}`}
                fill={entry.isLow ? "#ef4444" : "#0284c7"}
              />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
