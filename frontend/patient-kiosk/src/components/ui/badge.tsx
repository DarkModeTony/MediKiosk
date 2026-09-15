import * as React from "react";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";

const badgeVariants = cva(
  "inline-flex items-center rounded-full px-3 py-1 text-xs font-semibold transition-colors focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2",
  {
    variants: {
      variant: {
        default:
          "border-transparent bg-primary text-primary-foreground shadow hover:bg-primary/80",
        secondary:
          "border-transparent bg-secondary text-secondary-foreground hover:bg-secondary/80",
        destructive:
          "border-transparent bg-red-100 text-red-700 border border-red-200",
        critical:
          "border-transparent bg-red-600 text-white animate-pulse shadow-sm",
        warning:
          "border-transparent bg-amber-100 text-amber-800 border border-amber-200",
        success:
          "border-transparent bg-emerald-100 text-emerald-800 border border-emerald-200",
        ai:
          "border-transparent bg-indigo-100 text-indigo-700 border border-indigo-200",
        verified:
          "border-transparent bg-teal-100 text-teal-800 border border-teal-200",
        unknown:
          "border-transparent bg-slate-100 text-slate-700 border border-slate-300",
        outline:
          "text-foreground border border-border",
      },
    },
    defaultVariants: {
      variant: "default",
    },
  }
);

export interface BadgeProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof badgeVariants> {}

function Badge({ className, variant, ...props }: BadgeProps) {
  return (
    <div className={cn(badgeVariants({ variant }), className)} {...props} />
  );
}

export { Badge, badgeVariants };
