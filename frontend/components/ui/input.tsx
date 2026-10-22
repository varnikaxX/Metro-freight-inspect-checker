import * as React from "react";
import { cn } from "@/lib/utils";

export interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {}

const Input = React.forwardRef<HTMLInputElement, InputProps>(
  ({ className, type, ...props }, ref) => {
    return (
      <input
        type={type}
        ref={ref}
        className={cn(
          "flex h-12 w-full rounded-xl border border-ink-600/25 bg-surface px-4 py-2 text-sm text-ink-900 placeholder:text-ink-700/45 transition-colors dark:border-paper-50/20 dark:bg-paper-50/[0.06] dark:text-paper-50 dark:placeholder:text-paper-100/55",
          "focus-visible:outline-none focus-visible:border-brass-400 focus-visible:ring-2 focus-visible:ring-brass-400/30",
          "disabled:cursor-not-allowed disabled:opacity-50",
          className
        )}
        {...props}
      />
    );
  }
);
Input.displayName = "Input";

export { Input };
