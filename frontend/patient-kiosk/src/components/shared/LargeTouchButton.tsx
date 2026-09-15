import React from "react";
import { cn } from "@/lib/utils";
import { Loader2 } from "lucide-react";

interface LargeTouchButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "primary" | "outline" | "ghost" | "danger";
  loading?: boolean;
  children: React.ReactNode;
}

export function LargeTouchButton({
  variant = "primary",
  loading = false,
  children,
  className,
  disabled,
  ...props
}: LargeTouchButtonProps) {
  const base =
    "relative w-full inline-flex items-center justify-center gap-3 rounded-2xl font-bold text-lg transition-all duration-200 touch-manipulation select-none active:scale-[0.98] focus-visible:outline-none focus-visible:ring-4 focus-visible:ring-blue-500/30 overflow-hidden py-5 px-6 disabled:opacity-50 disabled:pointer-events-none";

  const variants = {
    primary:
      "shimmer-bg text-white shadow-lg shadow-blue-600/25 hover:shadow-xl hover:shadow-blue-600/35 hover:brightness-110",
    outline:
      "bg-white text-slate-800 border-2 border-slate-200 hover:border-blue-400 hover:bg-blue-50/50 shadow-sm hover:shadow-md",
    ghost:
      "bg-transparent text-slate-600 hover:bg-slate-100",
    danger:
      "bg-red-600 text-white shadow-lg shadow-red-600/25 hover:bg-red-700",
  };

  return (
    <button
      className={cn(base, variants[variant], className)}
      disabled={disabled || loading}
      {...props}
    >
      {/* Ripple overlay on primary */}
      {variant === "primary" && (
        <span className="absolute inset-0 rounded-2xl bg-white/10 opacity-0 hover:opacity-100 transition-opacity duration-300" />
      )}

      {loading ? (
        <>
          <Loader2 className="w-5 h-5 animate-spin" />
          <span>Please wait…</span>
        </>
      ) : (
        children
      )}
    </button>
  );
}
