"use client";
import { cn } from "@/lib/utils";
import { CheckCircle, Clock, AlertCircle, Loader2 } from "lucide-react";

const STATUS_CONFIG: Record<string, { label: string; className: string; icon: any }> = {
  indexed: { label: "Indexed", className: "bg-emerald-500/10 text-emerald-600 dark:text-emerald-400", icon: CheckCircle },
  processing: { label: "Processing", className: "bg-amber-500/10 text-amber-600 dark:text-amber-400", icon: Loader2 },
  pending: { label: "Pending", className: "bg-blue-500/10 text-blue-600 dark:text-blue-400", icon: Clock },
  failed: { label: "Failed", className: "bg-red-500/10 text-red-600 dark:text-red-400", icon: AlertCircle },
};

export function StatusBadge({ status }: { status: string }) {
  const config = STATUS_CONFIG[status] || STATUS_CONFIG.pending;
  const Icon = config.icon;

  return (
    <span className={cn("inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium", config.className)}>
      <Icon className={cn("w-3 h-3", status === "processing" && "animate-spin")} />
      {config.label}
    </span>
  );
}
