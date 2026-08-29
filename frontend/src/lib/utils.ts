import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

const pkrFormatter = new Intl.NumberFormat("en-PK", {
  style: "currency",
  currency: "PKR",
  maximumFractionDigits: 0,
});

export function formatPKR(value: number | null | undefined): string {
  if (value == null) return "—";
  return pkrFormatter.format(value).replace("PKR", "Rs");
}

export function formatDistance(km: number | null | undefined): string {
  if (km == null) return "—";
  if (km < 1) return `${Math.round(km * 1000)} m`;
  return `${km.toFixed(1)} km`;
}

export function formatDateTime(iso: string): string {
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return "";
  return date.toLocaleString("en-PK", {
    day: "numeric",
    month: "short",
    year: "numeric",
    hour: "numeric",
    minute: "2-digit",
  });
}

export interface ConfidenceStyle {
  label: string;
  barClass: string;
  textClass: string;
}

export function confidenceStyle(confidence: number): ConfidenceStyle {
  if (confidence >= 0.8) {
    return { label: "High", barClass: "bg-indigo-500", textClass: "text-indigo-600 dark:text-indigo-400" };
  }
  if (confidence >= 0.6) {
    return { label: "Medium", barClass: "bg-amber-500", textClass: "text-amber-600 dark:text-amber-400" };
  }
  return { label: "Low", barClass: "bg-rose-500", textClass: "text-rose-600 dark:text-rose-400" };
}

export function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(0)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}
