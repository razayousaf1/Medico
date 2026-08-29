import * as React from "react";

import { cn } from "@/lib/utils";

const Progress = React.forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement> & { value?: number }
>(({ className, value = 0, ...props }, ref) => (
  <div
    ref={ref}
    role="progressbar"
    aria-valuenow={Math.round(value)}
    aria-valuemin={0}
    aria-valuemax={100}
    className={cn("h-2 w-full overflow-hidden rounded-full bg-muted", className)}
    {...props}
  >
    <div
      className="h-full rounded-full bg-primary transition-all duration-700 ease-out"
      style={{ width: `${Math.min(100, Math.max(0, value * 100))}%` }}
    />
  </div>
));
Progress.displayName = "Progress";

export { Progress };
