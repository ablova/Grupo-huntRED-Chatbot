import { cn } from "@/lib/utils"

interface LoadingSpinnerProps extends React.HTMLAttributes<HTMLDivElement> {
  className?: string;
}

export function LoadingSpinner({ className, ...props }: LoadingSpinnerProps) {
  return (
    <div
      className={cn(
        "animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600",
        className
      )}
      {...props}
    />
  );
}
