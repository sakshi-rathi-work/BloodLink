import React from "react";
import Spinner from "./Spinner";

export default function Button({
  children,
  type = "button",
  variant = "primary",
  size = "md",
  loading = false,
  disabled = false,
  className = "",
  onClick,
  icon: Icon,
  title,
  id,
  ...props
}) {
  const baseStyles =
    "inline-flex items-center justify-center font-medium rounded-xl transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed shadow-sm";

  const variants = {
    primary:
      "bg-blood-600 hover:bg-blood-700 text-white focus:ring-blood-500 shadow-blood-600/20 active:scale-[0.98]",
    secondary:
      "bg-white hover:bg-slate-50 text-slate-700 border border-slate-200 focus:ring-slate-300 shadow-slate-200/50 active:scale-[0.98]",
    danger:
      "bg-rose-600 hover:bg-rose-700 text-white focus:ring-rose-500 shadow-rose-600/20 active:scale-[0.98]",
    outline:
      "border border-blood-600 text-blood-600 hover:bg-blood-50 focus:ring-blood-500 active:scale-[0.98]",
    ghost:
      "text-slate-600 hover:bg-slate-100 hover:text-slate-900 focus:ring-slate-300 shadow-none",
  };

  const sizes = {
    sm: "px-3 py-1.5 text-xs gap-1.5",
    md: "px-4 py-2 text-sm gap-2",
    lg: "px-5 py-2.5 text-base gap-2.5",
  };

  const iconSizes = { sm: 13, md: 15, lg: 17 };

  return (
    <button
      id={id}
      type={type}
      disabled={disabled || loading}
      onClick={onClick}
      title={title}
      className={`${baseStyles} ${variants[variant] || variants.primary} ${
        sizes[size] || sizes.md
      } ${className}`}
      {...props}
    >
      {loading && <Spinner size="sm" className="mr-1 text-current" />}
      {!loading && Icon && <Icon size={iconSizes[size] || 15} aria-hidden="true" />}
      {children}
    </button>
  );
}

