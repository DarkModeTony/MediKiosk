import React from "react";
import { Activity, Heart } from "lucide-react";
import { cn } from "@/lib/utils";

interface BrandEmblemProps {
  size?: "sm" | "md" | "lg" | "xl";
  className?: string;
}

const sizes = {
  sm: { outer: "w-10 h-10", icon: "w-5 h-5", dot: "w-2 h-2 bottom-0 right-0" },
  md: { outer: "w-14 h-14", icon: "w-7 h-7", dot: "w-2.5 h-2.5 bottom-0 right-0" },
  lg: { outer: "w-20 h-20", icon: "w-10 h-10", dot: "w-3 h-3 bottom-0.5 right-0.5" },
  xl: { outer: "w-28 h-28", icon: "w-14 h-14", dot: "w-4 h-4 bottom-1 right-1" },
};

export function BrandEmblem({ size = "md", className }: BrandEmblemProps) {
  const s = sizes[size];
  return (
    <div className={cn("relative inline-flex items-center justify-center", s.outer, className)}>
      {/* Outer glow ring */}
      <div className="absolute inset-0 rounded-3xl bg-gradient-to-br from-blue-500/20 to-teal-500/20 blur-sm" />

      {/* Main icon container */}
      <div className="relative w-full h-full rounded-3xl bg-gradient-to-br from-blue-600 to-teal-500 flex items-center justify-center shadow-lg shadow-blue-600/30">
        {/* Decorative heart beat line */}
        <Activity className={cn("text-white drop-shadow-sm", s.icon)} />

        {/* Small heart accent */}
        <div className={cn("absolute rounded-full bg-emerald-400 border-2 border-white flex items-center justify-center shadow-sm", s.dot)}>
          <Heart className="text-white fill-white" style={{ width: "55%", height: "55%" }} />
        </div>
      </div>
    </div>
  );
}
