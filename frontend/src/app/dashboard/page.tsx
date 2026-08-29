"use client";

import { useEffect, useMemo, useState } from "react";
import dynamic from "next/dynamic";
import Link from "next/link";
import { motion } from "framer-motion";
import { Activity, ArrowLeft, Pill, RefreshCw } from "lucide-react";

import { MedicineCard } from "@/components/dashboard/medicine-card";
import { StatsRow } from "@/components/dashboard/stats-row";
import { SummaryCard } from "@/components/dashboard/summary-card";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { ThemeToggle } from "@/components/ui/theme-toggle";
import { clearAnalysis, loadAnalysis, loadLocation } from "@/lib/store";
import type { PrescriptionAnalysis } from "@/lib/types";

// Leaflet touches `window` at import time — load the map client-side only.
const PharmacyMap = dynamic(
  () => import("@/components/dashboard/pharmacy-map").then((mod) => mod.PharmacyMap),
  {
    ssr: false,
    loading: () => <div className="h-[420px] animate-pulse rounded-2xl bg-muted" />,
  },
);

export default function DashboardPage() {
  const [analysis, setAnalysis] = useState<PrescriptionAnalysis | null>(null);
  const [ready, setReady] = useState(false);
  const userLocation = useMemo(() => loadLocation(), []);

  useEffect(() => {
    setAnalysis(loadAnalysis());
    setReady(true);
  }, []);

  if (!ready) {
    return (
      <div className="mx-auto max-w-6xl space-y-6 px-4 py-10 sm:px-6">
        <Skeleton className="h-8 w-52" />
        <Skeleton className="h-52 w-full rounded-2xl" />
        <Skeleton className="h-32 w-full rounded-2xl" />
        <Skeleton className="h-96 w-full rounded-2xl" />
      </div>
    );
  }

  if (!analysis) {
    return (
      <div className="flex min-h-screen flex-col items-center justify-center gap-5 px-4 text-center">
        <span className="flex h-14 w-14 items-center justify-center rounded-2xl bg-secondary text-indigo-700 dark:text-indigo-300">
          <Pill className="h-7 w-7" strokeWidth={1.6} />
        </span>
        <div>
          <h1 className="font-heading text-xl font-bold tracking-tight">No analysis yet</h1>
          <p className="mt-2 max-w-sm text-sm text-muted-foreground">
            Upload a prescription on the home page first — the results dashboard will
            appear here.
          </p>
        </div>
        <Button asChild>
          <Link href="/">
            <ArrowLeft />
            Back to upload
          </Link>
        </Button>
      </div>
    );
  }

  const available = analysis.medicines.filter((m) => m.available).length;

  return (
    <div className="min-h-screen">
      {/* ---- Dashboard header ---- */}
      <header className="sticky top-0 z-50 border-b border-border/60 bg-background/85 backdrop-blur-xl">
        <div className="mx-auto flex h-16 max-w-6xl items-center justify-between gap-3 px-4 sm:px-6">
          <div className="flex min-w-0 items-center gap-3">
            <Link href="/" className="flex shrink-0 items-center gap-2.5">
              <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-br from-indigo-500 to-indigo-700 text-white shadow-md shadow-indigo-500/25">
                <Activity className="h-5 w-5" strokeWidth={2.5} />
              </span>
              <span className="font-heading hidden text-lg font-bold tracking-tight sm:block">Medico</span>
            </Link>
            <span className="hidden h-6 w-px bg-border sm:block" />
            <div className="min-w-0">
              <p className="truncate text-sm font-semibold">Prescription analysis</p>
              <p className="text-xs text-muted-foreground">
                ID {analysis.id} · {available}/{analysis.medicines.length} medicines available
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <ThemeToggle />
            <Button
              variant="ghost"
              size="sm"
              onClick={() => {
                clearAnalysis();
                window.location.href = "/";
              }}
            >
              <RefreshCw />
              <span className="hidden sm:inline">New analysis</span>
            </Button>
            <Button asChild size="sm">
              <Link href="/">Upload another</Link>
            </Button>
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-6xl space-y-8 px-4 py-8 sm:px-6 lg:py-10">
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ duration: 0.3 }}>
          <SummaryCard analysis={analysis} />
        </motion.div>

        <StatsRow analysis={analysis} />

        <section aria-label="Medicines">
          <div className="mb-4 flex items-center justify-between">
            <h2 className="font-heading text-xl font-extrabold tracking-tight">Medicines &amp; availability</h2>
            <p className="text-xs text-muted-foreground">Sorted by availability &amp; distance</p>
          </div>
          <div className="grid gap-5 md:grid-cols-2">
            {analysis.medicines.map((medicine, index) => (
              <MedicineCard key={`${medicine.name}-${index}`} medicine={medicine} index={index} />
            ))}
          </div>
        </section>

        <section aria-label="Pharmacy map">
          <PharmacyMap pharmacies={analysis.pharmacies} userLocation={userLocation ?? analysis.user_location} />
        </section>

        <p className="pb-4 text-center text-xs text-muted-foreground">
          Stock data {analysis.demo_mode ? "from the built-in demo dataset" : "from Firestore"} ·
          Medico is an information tool, not medical advice — confirm dosages with your pharmacist.
        </p>
      </main>
    </div>
  );
}
