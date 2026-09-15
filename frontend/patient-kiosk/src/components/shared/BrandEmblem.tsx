import React from "react";
import Image from "next/image";
import { cn } from "@/lib/utils";

interface BrandEmblemProps {
  size?: "sm" | "md" | "lg" | "xl";
  className?: string;
}

const sizes = {
  sm: { outer: "w-10 h-10", img: 20, p: "p-2" },
  md: { outer: "w-14 h-14", img: 32, p: "p-3" },
  lg: { outer: "w-20 h-20", img: 48, p: "p-4" },
  xl: { outer: "w-28 h-28", img: 72, p: "p-5" },
};

export function BrandEmblem({ size = "md", className }: BrandEmblemProps) {
  const s = sizes[size];
  return (
    <div className={cn("relative inline-flex items-center justify-center", s.outer, className)}>
      {/* Outer glow ring */}
      <div className="absolute inset-0 rounded-3xl bg-gradient-to-br from-blue-500/20 to-teal-500/20 blur-sm" />

      {/* Main icon container */}
      <div className={cn("relative w-full h-full rounded-3xl bg-gradient-to-br from-blue-600 to-teal-500 flex items-center justify-center shadow-lg shadow-blue-600/30", s.p)}>
        <Image
          src="/logo-white.png"
          alt="MediPlatform Emblem"
          width={s.img}
          height={s.img}
          className="w-full h-full object-contain drop-shadow-sm"
        />
      </div>
    </div>
  );
}
