"use client";

import { motion } from "framer-motion";
import { CheckCircle2, Clock, Pill, Wallet } from "lucide-react";

import type { PrescriptionAnalysis } from "@/lib/types";
import { formatDistance, formatPKR } from "@/lib/utils";

export function StatsRow({ analysis }: { analysis: PrescriptionAnalysis }) {
  const { medicines } = analysis;
  const availableCount = medicines.filter((m) => m.available).length;

  const nearest = medicines
    .map((m) => m.best_match?.pharmacy.distance_km ?? null)
    .filter((d): d is number => d != null)
    .sort((a, b) => a - b)[0];

  const total = medicines.reduce(
    (sum, m) => sum + (m.best_match?.price ?? 0),
    0,
  );

  const stats = [
    {
      icon: Pill,
      label: "Medicines identified",
      value: String(medicines.length),
      hint: `${availableCount} available nearby`,
    },
    {
      icon: CheckCircle2,
      label: "Availability",
      value: medicines.length ? `${Math.round((availableCount / medicines.length) * 100)}%` : "—",
      hint: "of your prescription",
    },
    {
      icon: Clock,
      label: "Nearest pharmacy",
      value: nearest != null ? formatDistance(nearest) : "—",
      hint: nearest != null ? "from your location" : "enable location for distances",
    },
    {
      icon: Wallet,
      label: "Estimated total",
      value: total > 0 ? formatPKR(total) : "—",
      hint: "best price per medicine",
    },
  ];

  return (
    <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
      {stats.map((stat, index) => (
        <motion.div
          key={stat.label}
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4, delay: 0.1 + index * 0.07 }}
          className="card-hover rounded-2xl border border-border/80 bg-card p-4 sm:p-5"
        >
          <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-secondary text-indigo-700 dark:text-indigo-300">
            <stat.icon className="h-4 w-4" strokeWidth={2} />
          </span>
          <p className="font-heading mt-3 text-2xl font-extrabold tracking-tight">{stat.value}</p>
          <p className="text-xs font-semibold text-foreground/70">{stat.label}</p>
          <p className="mt-0.5 text-xs text-muted-foreground">{stat.hint}</p>
        </motion.div>
      ))}
    </div>
  );
}
