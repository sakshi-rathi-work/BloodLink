import React from "react";

export default function Badge({
  children,
  variant = "default",
  size = "md",
  className = "",
}) {
  const variants = {
    default: "bg-slate-100 text-slate-700 border-slate-200",
    emergency: "bg-rose-100 text-rose-800 border-rose-200 font-semibold",
    routine: "bg-slate-100 text-slate-700 border-slate-200",
    pending: "bg-amber-100 text-amber-800 border-amber-200",
    approved: "bg-blue-100 text-blue-800 border-blue-200",
    issued: "bg-emerald-100 text-emerald-800 border-emerald-200",
    rejected: "bg-rose-100 text-rose-700 border-rose-200",
    available: "bg-emerald-100 text-emerald-800 border-emerald-200",
    expired: "bg-rose-100 text-rose-800 border-rose-200",
    regular: "bg-purple-100 text-purple-800 border-purple-200 font-semibold",
    low: "bg-rose-100 text-rose-800 border-rose-200 font-bold",
    warning: "bg-amber-100 text-amber-800 border-amber-200",
    info: "bg-sky-100 text-sky-800 border-sky-200",
  };

  const sizes = {
    sm: "px-2 py-0.5 text-xs",
    md: "px-2.5 py-1 text-xs",
    lg: "px-3 py-1.5 text-sm",
  };

  return (
    <span
      className={`inline-flex items-center font-medium rounded-full border ${
        variants[variant] || variants.default
      } ${sizes[size] || sizes.md} ${className}`}
    >
      {children}
    </span>
  );
}
