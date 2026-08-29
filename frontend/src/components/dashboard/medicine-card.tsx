"use client";

import { useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import {
  AlertTriangle,
  CalendarDays,
  ChevronDown,
  Clock,
  Crosshair,
  Info,
  MapPin,
  Phone,
  Pill,
  Repeat,
  Star,
} from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import type { AvailabilityStatus, InventoryMatch, MedicineResult } from "@/lib/types";
import { cn, confidenceStyle, formatDistance, formatPKR } from "@/lib/utils";

const STATUS_CONFIG: Record<AvailabilityStatus, { label: string; variant: "success" | "warning" | "destructive" | "outline"; pulse: string }> = {
  in_stock: { label: "In stock nearby", variant: "success", pulse: "bg-emerald-500" },
  limited: { label: "Low stock nearby", variant: "warning", pulse: "bg-amber-500" },
  out_of_stock: { label: "Out of stock", variant: "destructive", pulse: "bg-rose-400" },
  unknown: { label: "Not in database", variant: "outline", pulse: "bg-slate-400" },
};

function StockDots({ stock }: { stock: number }) {
  const level = stock === 0 ? 0 : stock < 10 ? 1 : 2;
  return (
    <span className="inline-flex items-center gap-1" title={`${stock} in stock`}>
      {[0, 1, 2].map((dot) => (
        <span
          key={dot}
          className={cn(
            "h-1.5 w-1.5 rounded-full",
            dot < level ? (level === 2 ? "bg-emerald-500" : "bg-amber-500") : "bg-border",
          )}
        />
      ))}
    </span>
  );
}

function PharmacyRow({ match }: { match: InventoryMatch }) {
  const pharmacy = match.pharmacy;
  return (
    <li className="flex items-center justify-between gap-3 rounded-xl border border-border/60 bg-background px-3.5 py-2.5">
      <div className="min-w-0">
        <p className="truncate text-sm font-semibold">
          {pharmacy.name}
          {pharmacy.branch ? <span className="font-normal text-muted-foreground"> · {pharmacy.branch}</span> : null}
        </p>
        <p className="mt-0.5 flex flex-wrap items-center gap-x-3 gap-y-0.5 text-xs text-muted-foreground">
          {pharmacy.distance_km != null && (
            <span className="inline-flex items-center gap-1">
              <Crosshair className="h-3 w-3" /> {formatDistance(pharmacy.distance_km)}
            </span>
          )}
          {pharmacy.open_hours && (
            <span className="inline-flex items-center gap-1">
              <Clock className="h-3 w-3" /> {pharmacy.open_hours}
            </span>
          )}
          {match.strength && (
            <span className="inline-flex items-center gap-1">
              <Pill className="h-3 w-3" /> {match.brand} {match.strength}
            </span>
          )}
        </p>
      </div>
      <div className="shrink-0 text-right">
        <p className="text-sm font-bold">{formatPKR(match.price)}</p>
        <div className="mt-1 flex items-center justify-end gap-2">
          <StockDots stock={match.stock} />
          <span
            className={cn(
              "text-[11px] font-semibold",
              match.in_stock ? "text-indigo-600 dark:text-indigo-400" : "text-muted-foreground",
            )}
          >
            {match.in_stock ? `${match.stock} left` : "Out"}
          </span>
        </div>
      </div>
    </li>
  );
}

export function MedicineCard({ medicine, index }: { medicine: MedicineResult; index: number }) {
  const [showAll, setShowAll] = useState(false);
  const status = STATUS_CONFIG[medicine.availability];
  const confidence = confidenceStyle(medicine.confidence);
  const best = medicine.best_match;
  const otherMatches = medicine.matches.filter((m) => m !== best);

  return (
    <motion.article
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.45, delay: index * 0.08 }}
      className="card-hover flex flex-col rounded-2xl border border-border/80 bg-card p-5 sm:p-6"
    >
      {/* ---- Header ---- */}
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <div className="flex flex-wrap items-center gap-2">
            <h3 className="font-heading text-xl font-bold tracking-tight">{medicine.name}</h3>
            {medicine.form && <Badge variant="secondary" className="capitalize">{medicine.form}</Badge>}
          </div>
          {medicine.generic_name && (
            <p className="mt-1 text-sm text-muted-foreground">
              Generic: <span className="font-medium text-foreground/80">{medicine.generic_name}</span>
            </p>
          )}
        </div>
        <span
          className={cn(
            "inline-flex shrink-0 items-center gap-2 rounded-full border px-3 py-1 text-xs font-semibold",
            medicine.availability === "in_stock" &&
              "border-indigo-200 bg-indigo-50 text-indigo-700 dark:border-indigo-800/60 dark:bg-indigo-950/40 dark:text-indigo-300",
            medicine.availability === "limited" &&
              "border-amber-200 bg-amber-50 text-amber-700 dark:border-amber-800/60 dark:bg-amber-950/40 dark:text-amber-300",
            medicine.availability === "out_of_stock" &&
              "border-rose-200 bg-rose-50 text-rose-700 dark:border-rose-800/60 dark:bg-rose-950/40 dark:text-rose-300",
            medicine.availability === "unknown" && "border-border bg-muted text-muted-foreground",
          )}
        >
          <span className="relative flex h-2 w-2">
            <span className={cn("absolute inline-flex h-full w-full animate-ping rounded-full opacity-60", status.pulse)} />
            <span className={cn("relative inline-flex h-2 w-2 rounded-full", status.pulse)} />
          </span>
          {status.label}
        </span>
      </div>

      {/* ---- Details grid ---- */}
      <dl className="mt-5 grid grid-cols-2 gap-x-4 gap-y-3 text-sm sm:grid-cols-4">
        {medicine.strength && (
          <div>
            <dt className="text-xs font-medium uppercase tracking-wide text-muted-foreground">Strength</dt>
            <dd className="mt-0.5 font-semibold">{medicine.strength}</dd>
          </div>
        )}
        {medicine.frequency?.raw && (
          <div>
            <dt className="text-xs font-medium uppercase tracking-wide text-muted-foreground">Frequency</dt>
            <dd className="mt-0.5 font-semibold">{medicine.frequency.raw}</dd>
          </div>
        )}
        {medicine.duration && (
          <div>
            <dt className="text-xs font-medium uppercase tracking-wide text-muted-foreground">Duration</dt>
            <dd className="mt-0.5 font-semibold">{medicine.duration}</dd>
          </div>
        )}
        {medicine.instructions && (
          <div>
            <dt className="text-xs font-medium uppercase tracking-wide text-muted-foreground">Instructions</dt>
            <dd className="mt-0.5 font-semibold">{medicine.instructions}</dd>
          </div>
        )}
      </dl>

      {/* ---- Frequency interpretation ---- */}
      {medicine.frequency?.interpretation && (
        <p className="mt-3 rounded-xl bg-muted/70 px-3.5 py-2.5 text-sm leading-relaxed text-foreground/85">
          {medicine.frequency.interpretation}
        </p>
      )}

      {medicine.frequency?.abbreviation_meanings.length ? (
        <div className="mt-3 flex flex-wrap gap-1.5">
          {medicine.frequency.abbreviation_meanings.map((entry, i) => (
            <span
              key={`${entry.abbreviation}-${i}`}
              title={entry.meaning}
              className="inline-flex cursor-help items-center gap-1.5 rounded-full border border-indigo-200/70 bg-secondary px-2.5 py-1 text-xs font-medium text-indigo-800 dark:border-indigo-800/50 dark:text-indigo-300"
            >
              <Info className="h-3 w-3 shrink-0" />
              <span className="font-bold">{entry.abbreviation}</span>
              {entry.meaning && <span className="opacity-80">— {entry.meaning}</span>}
            </span>
          ))}
        </div>
      ) : null}

      <Separator className="my-5" />

      {/* ---- Best availability ---- */}
      {best ? (
        <div className="rounded-xl border border-indigo-200/60 bg-gradient-to-br from-indigo-50/80 to-sky-50/40 p-4 dark:border-indigo-800/50 dark:from-indigo-950/40 dark:to-sky-950/30">
          <p className="text-xs font-semibold uppercase tracking-wide text-indigo-700/80 dark:text-indigo-300/80">
            Best option near you
          </p>
          <div className="mt-2 flex items-start justify-between gap-3">
            <div className="min-w-0">
              <p className="font-bold leading-snug">
                {best.pharmacy.name}
                {best.pharmacy.branch ? <span className="font-medium text-muted-foreground"> — {best.pharmacy.branch}</span> : null}
              </p>
              <p className="mt-1 flex flex-wrap items-center gap-x-3 gap-y-1 text-xs text-muted-foreground">
                {best.pharmacy.distance_km != null && (
                  <span className="inline-flex items-center gap-1 font-semibold text-indigo-600 dark:text-indigo-400">
                    <MapPin className="h-3 w-3" /> {formatDistance(best.pharmacy.distance_km)} away
                  </span>
                )}
                {best.pharmacy.phone && (
                  <a href={`tel:${best.pharmacy.phone}`} className="inline-flex items-center gap-1 hover:text-foreground">
                    <Phone className="h-3 w-3" /> {best.pharmacy.phone}
                  </a>
                )}
                {best.pharmacy.rating != null && (
                  <span className="inline-flex items-center gap-1">
                    <Star className="h-3 w-3 fill-amber-400 text-amber-400" /> {best.pharmacy.rating.toFixed(1)}
                  </span>
                )}
              </p>
            </div>
            <div className="shrink-0 text-right">
              <p className="font-heading text-lg font-extrabold text-indigo-600 dark:text-indigo-400">{formatPKR(best.price)}</p>
              <p className="text-xs text-muted-foreground">
                {best.brand} {best.strength ?? ""}
              </p>
            </div>
          </div>
        </div>
      ) : (
        <div className="flex items-start gap-2.5 rounded-xl border border-rose-200/70 bg-rose-50/60 px-4 py-3 text-sm text-rose-800 dark:border-rose-800/60 dark:bg-rose-950/40 dark:text-rose-200">
          <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" />
          <span>
            No pharmacy in our database currently lists this medicine. Check the AI-suggested
            alternatives below.
          </span>
        </div>
      )}

      {/* ---- Alternatives ---- */}
      {medicine.alternatives.length > 0 && (
        <div className="mt-4">
          <p className="flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wide text-muted-foreground">
            <Repeat className="h-3.5 w-3.5" /> AI-suggested alternatives
          </p>
          <ul className="mt-2 space-y-1.5">
            {medicine.alternatives.map((alternative) => {
              const altBest = alternative.best_match;
              return (
                <li
                  key={alternative.brand}
                  className="flex items-center justify-between gap-3 rounded-xl border border-border/60 bg-background px-3.5 py-2.5 text-sm"
                >
                  <span className="min-w-0 truncate font-semibold">{alternative.brand}</span>
                  {altBest ? (
                    <span className="flex shrink-0 items-center gap-2 text-xs">
                      <span className="text-muted-foreground">
                        {altBest.pharmacy.name}
                        {altBest.pharmacy.distance_km != null && ` · ${formatDistance(altBest.pharmacy.distance_km)}`}
                      </span>
                      <span className="font-bold text-indigo-600 dark:text-indigo-400">{formatPKR(altBest.price)}</span>
                    </span>
                  ) : (
                    <Badge variant="outline" className="shrink-0">Not found</Badge>
                  )}
                </li>
              );
            })}
          </ul>
        </div>
      )}

      {/* ---- All matches ---- */}
      {otherMatches.length > 0 && (
        <div className="mt-4">
          <button
            type="button"
            onClick={() => setShowAll((value) => !value)}
            className="flex w-full items-center justify-between rounded-lg px-1 py-1 text-sm font-semibold text-indigo-600 transition-colors hover:text-indigo-500 dark:text-indigo-400 dark:hover:text-indigo-300"
          >
            <span>
              {showAll ? "Hide" : "Compare"} {otherMatches.length + (best ? 1 : 0)} pharmac
              {otherMatches.length + (best ? 1 : 0) === 1 ? "y" : "ies"}
            </span>
            <ChevronDown className={cn("h-4 w-4 transition-transform", showAll && "rotate-180")} />
          </button>
          <AnimatePresence initial={false}>
            {showAll && (
              <motion.ul
                initial={{ height: 0, opacity: 0 }}
                animate={{ height: "auto", opacity: 1 }}
                exit={{ height: 0, opacity: 0 }}
                transition={{ duration: 0.25 }}
                className="space-y-1.5 overflow-hidden"
              >
                {best && <PharmacyRow match={best} />}
                {otherMatches.map((match, i) => (
                  <PharmacyRow key={`${match.pharmacy.id}-${match.medicine_id}-${i}`} match={match} />
                ))}
              </motion.ul>
            )}
          </AnimatePresence>
        </div>
      )}

      {/* ---- Confidence footer ---- */}
      <div className="mt-5 flex items-center justify-between gap-3 border-t border-border/60 pt-4">
        <span className="flex items-center gap-1.5 text-xs font-medium text-muted-foreground">
          <CalendarDays className="h-3.5 w-3.5" />
          AI confidence
        </span>
        <span className="flex items-center gap-2.5">
          <span className="h-1.5 w-20 overflow-hidden rounded-full bg-muted">
            <span
              className={cn("block h-full rounded-full transition-all duration-700", confidence.barClass)}
              style={{ width: `${Math.round(medicine.confidence * 100)}%` }}
            />
          </span>
          <span className={cn("text-xs font-bold", confidence.textClass)}>
            {Math.round(medicine.confidence * 100)}%
          </span>
        </span>
      </div>
    </motion.article>
  );
}
