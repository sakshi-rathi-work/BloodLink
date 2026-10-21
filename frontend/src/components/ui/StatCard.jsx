import React from "react";

export default function StatCard({
  title,
  value,
  subtitle,
  icon: Icon,
  variant = "default",
  className = "",
  trend,
}) {
  const variants = {
    default: "border-slate-200/80 bg-white",
    blood: "border-blood-200/80 bg-blood-50/40 text-blood-900",
    warning: "border-amber-200/80 bg-amber-50/40 text-amber-900",
    success: "border-emerald-200/80 bg-emerald-50/40 text-emerald-900",
    danger: "border-rose-200/80 bg-rose-50/40 text-rose-900",
  };

  const iconVariants = {
    default: "bg-slate-100 text-slate-700",
    blood: "bg-blood-100 text-blood-700",
    warning: "bg-amber-100 text-amber-700",
    success: "bg-emerald-100 text-emerald-700",
    danger: "bg-rose-100 text-rose-700",
  };

  return (
    <div
      className={`p-5 rounded-2xl border shadow-sm transition-all duration-200 hover:shadow-md ${
        variants[variant] || variants.default
      } ${className}`}
    >
      <div className="flex items-center justify-between mb-3">
        <span className="text-xs font-bold text-slate-500 uppercase tracking-wider">
          {title}
        </span>
        {Icon && (
          <div
            className={`w-10 h-10 rounded-xl flex items-center justify-center flex-shrink-0 ${
              iconVariants[variant] || iconVariants.default
            }`}
          >
            <Icon className="w-5 h-5" />
          </div>
        )}
      </div>

      <div className="flex items-baseline gap-2">
        <span className="text-3xl font-extrabold text-slate-900 tracking-tight">
          {value}
        </span>
        {trend && (
          <span
            className={`text-xs font-semibold ${
              trend > 0 ? "text-emerald-600" : "text-rose-600"
            }`}
          >
            {trend > 0 ? `+${trend}%` : `${trend}%`}
          </span>
        )}
      </div>

      {subtitle && <p className="mt-1 text-xs text-slate-500">{subtitle}</p>}
    </div>
  );
}
