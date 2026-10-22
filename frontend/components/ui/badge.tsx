import * as React from "react";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";

const badgeVariants = cva(
  "inline-flex items-center gap-1.5 rounded-full border px-2.5 py-0.5 text-[11px] font-mono uppercase tracking-wider",
  {
    variants: {
      variant: {
        default: "border-warning/40 bg-warning-surface text-secondary-foreground",
        pass: "border-success/40 bg-success-surface text-accent-foreground",
        fail: "border-danger/40 bg-danger-surface text-danger",
        review: "border-warning/40 bg-warning-surface text-secondary-foreground",
        neutral: "border-border bg-neutral-surface text-muted-foreground",
      },
    },
    defaultVariants: { variant: "default" },
  }
);

export interface BadgeProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof badgeVariants> {}

function Badge({ className, variant, ...props }: BadgeProps) {
  return <div className={cn(badgeVariants({ variant }), className)} {...props} />;
}

export { Badge, badgeVariants };
