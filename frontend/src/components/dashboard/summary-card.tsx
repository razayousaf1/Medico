"use client";

import { motion } from "framer-motion";
import { AlertTriangle, CalendarClock, FileText, ScanLine, Sparkles, Stethoscope, User } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { cn, confidenceStyle, formatDateTime } from "@/lib/utils";
import type { PrescriptionAnalysis } from "@/lib/types";

export function SummaryCard({ analysis }: { analysis: PrescriptionAnalysis }) {
  const confidence = confidenceStyle(analysis.overall_confidence);

  const meta = [
    analysis.patient_name && { icon: User, label: analysis.patient_name },
    analysis.doctor_name && { icon: Stethoscope, label: analysis.doctor_name },
    analysis.prescribed_date && { icon: CalendarClock, label: analysis.prescribed_date },
  ].filter(Boolean) as { icon: typeof User; label: string }[];

  return (
    <motion.section
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
      className="relative overflow-hidden rounded-2xl border border-indigo-200/60 bg-card p-6 shadow-lg shadow-indigo-500/5 sm:p-8 dark:border-indigo-800/50"
    >
      <div className="pointer-events-none absolute inset-x-0 top-0 h-1 bg-gradient-to-r from-indigo-500 via-sky-400 to-indigo-500" />
      <div className="glow-indigo pointer-events-none absolute inset-0 opacity-60" />

      <div className="relative flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <span className="flex h-11 w-11 items-center justify-center rounded-xl bg-gradient-to-br from-indigo-500 to-indigo-700 text-white shadow-md shadow-indigo-500/25">
            <Sparkles className="h-5 w-5" />
          </span>
          <div>
            <h2 className="font-heading text-lg font-bold tracking-tight">AI Summary</h2>
            <p className="text-xs text-muted-foreground">
              Analysed {formatDateTime(analysis.created_at)} · {(analysis.processing_ms / 1000).toFixed(1)}s
              {analysis.demo_mode && " · demo data"}
            </p>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <span className="text-xs font-semibold text-muted-foreground">Overall confidence</span>
          <span className={cn("font-heading text-lg font-extrabold", confidence.textClass)}>
            {Math.round(analysis.overall_confidence * 100)}%
          </span>
        </div>
      </div>

      <p className="relative mt-5 text-base leading-relaxed text-foreground/90 sm:text-lg">
        {analysis.summary || "No summary was generated for this prescription."}
      </p>

      <div className="relative mt-4 flex items-center gap-3">
        <Progress value={analysis.overall_confidence} className="max-w-xs" />
        <Badge variant={analysis.overall_confidence >= 0.8 ? "success" : "warning"} className="shrink-0">
          {confidence.label} confidence
        </Badge>
      </div>

      {meta.length > 0 && (
        <div className="relative mt-5 flex flex-wrap gap-2">
          {meta.map(({ icon: Icon, label }) => (
            <span
              key={label}
              className="inline-flex items-center gap-1.5 rounded-full border border-border bg-background px-3 py-1 text-xs font-medium text-muted-foreground"
            >
              <Icon className="h-3.5 w-3.5" /> {label}
            </span>
          ))}
        </div>
      )}

      {analysis.warnings.length > 0 && (
        <ul className="relative mt-5 space-y-2">
          {analysis.warnings.map((warning, index) => (
            <li
              key={index}
              className="flex items-start gap-2.5 rounded-xl border border-amber-200/80 bg-amber-50/70 px-4 py-3 text-sm text-amber-900 dark:border-amber-800/60 dark:bg-amber-950/40 dark:text-amber-200"
            >
              <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" />
              <span>{warning}</span>
            </li>
          ))}
        </ul>
      )}

      {analysis.ocr_text && (
        <details className="relative mt-5 rounded-xl border border-border/70 bg-background/70 px-4 py-3">
          <summary className="flex cursor-pointer list-none items-center gap-2 text-sm font-semibold text-muted-foreground transition-colors hover:text-foreground">
            <FileText className="h-4 w-4" />
            View extracted text (OCR)
            <span className="ml-auto flex items-center gap-1 text-xs font-normal">
              <ScanLine className="h-3.5 w-3.5" />
              {analysis.ocr_confidence != null
                ? `${Math.round(analysis.ocr_confidence * 100)}% OCR confidence`
                : "raw text"}
            </span>
          </summary>
          <pre className="mt-3 max-h-48 overflow-auto whitespace-pre-wrap rounded-lg bg-muted p-3 text-xs leading-relaxed text-foreground/80">
            {analysis.ocr_text}
          </pre>
        </details>
      )}
    </motion.section>
  );
}
