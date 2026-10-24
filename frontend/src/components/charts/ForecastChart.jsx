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
  ReferenceLine,
} from "recharts";

export default function ForecastChart({ forecast = [], safeMinimum = 10, bloodGroup = "" }) {
  if (!forecast || forecast.length === 0) {
    return (
      <div className="flex h-64 items-center justify-center text-sm text-slate-400 bg-slate-50 rounded-xl border border-dashed border-slate-200">
        No forecast data available for {bloodGroup}
      </div>
    );
  }

  const chartData = forecast.map((item) => ({
    date: item.date,
    stock: item.predicted_stock,
    isBelow: item.is_below_minimum,
  }));

  const minStock = Math.min(...chartData.map((d) => d.stock), safeMinimum);
  const maxStock = Math.max(...chartData.map((d) => d.stock), safeMinimum);
  const yDomain = [Math.max(0, Math.floor(minStock - 2)), Math.ceil(maxStock + 4)];

  return (
    <div className="h-72 w-full">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={chartData} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
          <XAxis
            dataKey="date"
            tick={{ fontSize: 11, fill: "#64748b" }}
            tickFormatter={(val) => {
              const parts = val.split("-");
              return `${parts[1]}/${parts[2]}`;
            }}
          />
          <YAxis
            domain={yDomain}
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
            formatter={(value) => [`${value} units`, "Predicted Stock"]}
            labelFormatter={(label) => `Date: ${label}`}
          />
          <Legend
            verticalAlign="top"
            height={36}
            wrapperStyle={{ fontSize: "12px", color: "#475569" }}
          />
          <ReferenceLine
            y={safeMinimum}
            label={{
              value: `Safe Min (${safeMinimum})`,
              fill: "#ef4444",
              fontSize: 11,
              position: "insideTopRight",
            }}
            stroke="#ef4444"
            strokeDasharray="4 4"
          />
          <Line
            type="monotone"
            dataKey="stock"
            name="Predicted Available Units"
            stroke="#2563eb"
            strokeWidth={2.5}
            dot={{ r: 3, fill: "#2563eb" }}
            activeDot={{ r: 6, fill: "#1d4ed8" }}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
