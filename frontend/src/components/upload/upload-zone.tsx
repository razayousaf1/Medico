"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { AnimatePresence, motion } from "framer-motion";
import {
  AlertCircle,
  CheckCircle2,
  FileText,
  ImageIcon,
  Loader2,
  RotateCcw,
  ScanLine,
  Search,
  Sparkles,
  UploadCloud,
  X,
} from "lucide-react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { analyzePrescription, ApiError } from "@/lib/api";
import { getUserLocation, saveAnalysis, saveLocation } from "@/lib/store";
import { cn, formatBytes } from "@/lib/utils";

const MAX_SIZE_MB = 10;
const ACCEPTED_TYPES = ["image/jpeg", "image/jpg", "image/png", "image/webp", "application/pdf"];
const ACCEPTED_EXTENSIONS = ".jpg,.jpeg,.png,.webp,.pdf";

interface Stage {
  label: string;
  description: string;
  icon: typeof ScanLine;
}

const STAGES: Stage[] = [
  {
    label: "Reading the prescription",
    description: "PaddleOCR is extracting every line of text",
    icon: ScanLine,
  },
  {
    label: "Understanding with Gemini AI",
    description: "Correcting OCR errors, identifying medicines & dosages",
    icon: Sparkles,
  },
  {
    label: "Checking nearby pharmacies",
    description: "Searching live stock, prices and alternatives",
    icon: Search,
  },
];

interface UploadZoneProps {
  onStarted?: () => void;
}

export function UploadZone({ onStarted }: UploadZoneProps) {
  const router = useRouter();
  const inputRef = useRef<HTMLInputElement>(null);

  const [file, setFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [dragging, setDragging] = useState(false);
  const [analyzing, setAnalyzing] = useState(false);
  const [stageIndex, setStageIndex] = useState(0);
  const [elapsed, setElapsed] = useState(0);
  const [error, setError] = useState<string | null>(null);

  const dragCounter = useRef(0);

  // Cycle through the stage indicators while the request is in flight
  useEffect(() => {
    if (!analyzing) return;
    const timer = setInterval(() => {
      setStageIndex((current) => Math.min(current + 1, STAGES.length - 1));
    }, 9000);
    return () => clearInterval(timer);
  }, [analyzing]);

  useEffect(() => {
    if (!analyzing) return;
    const timer = setInterval(() => setElapsed((s) => s + 1), 1000);
    return () => clearInterval(timer);
  }, [analyzing]);

  useEffect(() => {
    return () => {
      if (previewUrl) URL.revokeObjectURL(previewUrl);
    };
  }, [previewUrl]);

  const validate = useCallback((candidate: File): string | null => {
    const typeOk =
      ACCEPTED_TYPES.includes(candidate.type) ||
      /\.(jpe?g|png|webp|pdf)$/i.test(candidate.name);
    if (!typeOk) return "Please upload a JPG, PNG, WEBP image or a PDF.";
    if (candidate.size > MAX_SIZE_MB * 1024 * 1024) {
      return `File is too large (${formatBytes(candidate.size)}). Maximum is ${MAX_SIZE_MB} MB.`;
    }
    if (candidate.size === 0) return "The selected file is empty.";
    return null;
  }, []);

  const selectFile = useCallback(
    (candidate: File | null | undefined) => {
      if (!candidate) return;
      const validationError = validate(candidate);
      if (validationError) {
        toast.error(validationError);
        return;
      }
      setError(null);
      setFile(candidate);
      if (previewUrl) URL.revokeObjectURL(previewUrl);
      setPreviewUrl(
        candidate.type.startsWith("image/") ? URL.createObjectURL(candidate) : null,
      );
    },
    [previewUrl, validate],
  );

  const handleDrop = useCallback(
    (event: React.DragEvent) => {
      event.preventDefault();
      dragCounter.current = 0;
      setDragging(false);
      selectFile(event.dataTransfer.files?.[0]);
    },
    [selectFile],
  );

  const reset = useCallback(() => {
    setFile(null);
    if (previewUrl) URL.revokeObjectURL(previewUrl);
    setPreviewUrl(null);
    setAnalyzing(false);
    setStageIndex(0);
    setElapsed(0);
    setError(null);
    if (inputRef.current) inputRef.current.value = "";
  }, [previewUrl]);

  const analyze = useCallback(async () => {
    if (!file || analyzing) return;
    setAnalyzing(true);
    setStageIndex(0);
    setElapsed(0);
    setError(null);
    onStarted?.();

    try {
      const [coords] = await Promise.all([
        getUserLocation(),
        new Promise((resolve) => setTimeout(resolve, 600)), // let the stepper appear
      ]);
      if (coords) saveLocation(coords);

      const analysis = await analyzePrescription(file, coords);
      setStageIndex(STAGES.length - 1);
      saveAnalysis(analysis);
      toast.success("Prescription analysed!");
      await new Promise((resolve) => setTimeout(resolve, 700));
      router.push("/dashboard");
    } catch (err) {
      const message =
        err instanceof ApiError || err instanceof Error
          ? err.message
          : "Something went wrong while analysing the prescription.";
      setError(message);
      toast.error(message);
      setAnalyzing(false);
      setStageIndex(0);
    }
  }, [analyzing, file, onStarted, router]);

  const isImage = !!file && file.type.startsWith("image/");

  return (
    <div className="w-full">
      <input
        ref={inputRef}
        type="file"
        accept={ACCEPTED_EXTENSIONS}
        className="hidden"
        onChange={(event) => selectFile(event.target.files?.[0])}
      />

      <AnimatePresence mode="wait">
        {analyzing ? (
          <motion.div
            key="progress"
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0 }}
            className="rounded-2xl border border-indigo-200/70 bg-card p-6 shadow-lg shadow-indigo-500/5 sm:p-8 dark:border-indigo-800/50"
          >
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <span className="relative flex h-11 w-11 items-center justify-center rounded-xl bg-secondary">
                  {isImage && previewUrl ? (
                    // eslint-disable-next-line @next/next/no-img-element
                    <img src={previewUrl} alt="Prescription" className="h-11 w-11 rounded-xl object-cover" />
                  ) : (
                    <FileText className="h-5 w-5 text-indigo-700 dark:text-indigo-300" />
                  )}
                </span>
                <div>
                  <p className="text-sm font-semibold leading-tight">{file?.name}</p>
                  <p className="text-xs text-muted-foreground">
                    {file ? formatBytes(file.size) : ""} · {elapsed}s elapsed
                  </p>
                </div>
              </div>
              <Loader2 className="h-5 w-5 animate-spin text-sky-500" />
            </div>

            <ol className="mt-6 space-y-1">
              {STAGES.map((stage, index) => {
                const state = index < stageIndex ? "done" : index === stageIndex ? "active" : "pending";
                const Icon = stage.icon;
                return (
                  <li key={stage.label} className="flex items-start gap-3 rounded-xl px-3 py-3">
                    <span
                      className={cn(
                        "mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-full border transition-colors",
                        state === "done" && "border-indigo-500 bg-indigo-500 text-white",
                        state === "active" && "border-indigo-400 bg-secondary text-indigo-700 dark:text-indigo-300",
                        state === "pending" && "border-border bg-muted text-muted-foreground",
                      )}
                    >
                      {state === "done" ? (
                        <CheckCircle2 className="h-4 w-4" />
                      ) : state === "active" ? (
                        <Loader2 className="h-4 w-4 animate-spin" />
                      ) : (
                        <Icon className="h-4 w-4" />
                      )}
                    </span>
                    <div>
                      <p
                        className={cn(
                          "text-sm font-semibold",
                          state === "pending" && "text-muted-foreground",
                        )}
                      >
                        {stage.label}
                      </p>
                      {state !== "pending" && (
                        <p className="mt-0.5 text-xs text-muted-foreground">{stage.description}</p>
                      )}
                    </div>
                  </li>
                );
              })}
            </ol>
          </motion.div>
        ) : file ? (
          <motion.div
            key="preview"
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0 }}
            className="rounded-2xl border border-border/80 bg-card p-5 shadow-lg shadow-indigo-500/5 sm:p-6"
          >
            <div className="flex items-start gap-4">
              <div className="relative h-24 w-24 shrink-0 overflow-hidden rounded-xl border border-border bg-muted">
                {previewUrl ? (
                  // eslint-disable-next-line @next/next/no-img-element
                  <img src={previewUrl} alt="Prescription preview" className="h-full w-full object-cover" />
                ) : (
                  <div className="flex h-full w-full flex-col items-center justify-center gap-1 text-muted-foreground">
                    <FileText className="h-7 w-7" />
                    <span className="text-[10px] font-semibold uppercase">PDF</span>
                  </div>
                )}
                <button
                  type="button"
                  onClick={reset}
                  aria-label="Remove file"
                  className="absolute right-1 top-1 rounded-full bg-black/60 p-1 text-white transition-colors hover:bg-black/80"
                >
                  <X className="h-3 w-3" />
                </button>
              </div>
              <div className="min-w-0 flex-1">
                <p className="truncate text-sm font-semibold">{file.name}</p>
                <p className="mt-0.5 text-xs text-muted-foreground">{formatBytes(file.size)}</p>
                {error && (
                  <div className="mt-3 flex items-start gap-2 rounded-lg border border-rose-200 bg-rose-50 p-3 text-xs text-rose-700 dark:border-rose-800/60 dark:bg-rose-950/40 dark:text-rose-300">
                    <AlertCircle className="mt-0.5 h-4 w-4 shrink-0" />
                    <span>{error}</span>
                  </div>
                )}
                <div className="mt-4 flex flex-wrap gap-2.5">
                  <Button onClick={analyze} size="lg" className="flex-1 sm:flex-none">
                    <Sparkles />
                    Analyse prescription
                  </Button>
                  <Button onClick={reset} variant="outline" size="lg">
                    <RotateCcw />
                    Replace
                  </Button>
                </div>
              </div>
            </div>
          </motion.div>
        ) : (
          <motion.div
            key="dropzone"
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0 }}
          >
            <motion.button
              type="button"
              onClick={() => inputRef.current?.click()}
              onDragEnter={(event) => {
                event.preventDefault();
                dragCounter.current += 1;
                setDragging(true);
              }}
              onDragLeave={(event) => {
                event.preventDefault();
                dragCounter.current -= 1;
                if (dragCounter.current === 0) setDragging(false);
              }}
              onDragOver={(event) => event.preventDefault()}
              onDrop={handleDrop}
              animate={dragging ? { scale: 1.015 } : { scale: 1 }}
              className={cn(
                "group relative flex w-full flex-col items-center justify-center gap-4 overflow-hidden rounded-2xl border-2 border-dashed bg-card/70 px-6 py-12 text-center backdrop-blur transition-colors sm:py-14",
                dragging
                  ? "border-indigo-500 bg-indigo-50/70 dark:bg-indigo-950/40"
                  : "border-indigo-300/70 hover:border-indigo-400 hover:bg-indigo-50/40 dark:border-indigo-800/50 dark:hover:border-indigo-700 dark:hover:bg-indigo-950/30",
              )}
            >
              <motion.span
                animate={{ y: dragging ? -4 : [0, -6, 0] }}
                transition={
                  dragging ? { duration: 0.2 } : { duration: 2.4, repeat: Infinity, ease: "easeInOut" }
                }
                className={cn(
                  "flex h-16 w-16 items-center justify-center rounded-2xl text-white shadow-lg",
                  dragging ? "bg-indigo-500 shadow-indigo-500/30" : "bg-gradient-to-br from-indigo-500 to-indigo-700 shadow-indigo-500/25",
                )}
              >
                <UploadCloud className="h-8 w-8" strokeWidth={1.8} />
              </motion.span>
              <div>
                <p className="font-heading text-base font-semibold">
                  {dragging ? "Drop your prescription here" : "Drag & drop your prescription"}
                </p>
                <p className="mt-1 text-sm text-muted-foreground">
                  or <span className="font-semibold text-indigo-600 underline underline-offset-2 dark:text-indigo-400">browse files</span>
                </p>
              </div>
              <div className="flex flex-wrap items-center justify-center gap-2 text-xs text-muted-foreground">
                <span className="inline-flex items-center gap-1 rounded-full border border-border bg-card px-2.5 py-1">
                  <ImageIcon className="h-3 w-3" /> JPG · PNG · WEBP
                </span>
                <span className="inline-flex items-center gap-1 rounded-full border border-border bg-card px-2.5 py-1">
                  <FileText className="h-3 w-3" /> PDF
                </span>
                <span className="inline-flex items-center gap-1 rounded-full border border-border bg-card px-2.5 py-1">
                  Up to {MAX_SIZE_MB} MB
                </span>
              </div>
            </motion.button>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
