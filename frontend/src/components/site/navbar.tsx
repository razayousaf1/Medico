"use client";

import Link from "next/link";
import { motion } from "framer-motion";
import { Activity, ArrowRight, MapPin, ShieldCheck, Sparkles } from "lucide-react";

import { Button } from "@/components/ui/button";
import { ThemeToggle } from "@/components/ui/theme-toggle";

export function Navbar() {
  return (
    <motion.header
      initial={{ y: -24, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      transition={{ duration: 0.5, ease: "easeOut" }}
      className="sticky top-0 z-50 border-b border-border/60 bg-background/80 backdrop-blur-xl"
    >
      <div className="mx-auto flex h-16 max-w-6xl items-center justify-between px-4 sm:px-6">
        <Link href="/" className="flex items-center gap-2.5">
          <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-br from-indigo-500 to-indigo-700 text-white shadow-md shadow-indigo-500/25">
            <Activity className="h-5 w-5" strokeWidth={2.5} />
          </span>
          <span className="font-heading text-lg font-bold tracking-tight">Medico</span>
        </Link>

        <nav className="hidden items-center gap-8 text-sm font-medium text-muted-foreground md:flex">
          <a href="#how-it-works" className="transition-colors hover:text-foreground">How it works</a>
          <a href="#features" className="transition-colors hover:text-foreground">Features</a>
          <a href="#trust" className="transition-colors hover:text-foreground">Privacy</a>
        </nav>

        <div className="flex items-center gap-2">
          <ThemeToggle />
          <a
            href="#upload"
            className="hidden text-sm font-semibold text-indigo-600 transition-colors hover:text-indigo-500 dark:text-indigo-300 sm:block"
          >
            Sign in
          </a>
          <Button asChild size="sm">
            <a href="#upload">
              Upload prescription
              <ArrowRight />
            </a>
          </Button>
        </div>
      </div>
    </motion.header>
  );
}

export function HeroBadges() {
  const items = [
    { icon: Sparkles, label: "AI by Gemini" },
    { icon: ShieldCheck, label: "OCR by PaddleOCR" },
    { icon: MapPin, label: "Live pharmacy data" },
  ];
  return (
    <div className="flex flex-wrap items-center gap-2">
      {items.map(({ icon: Icon, label }) => (
        <span
          key={label}
          className="inline-flex items-center gap-1.5 rounded-full border border-indigo-200/70 bg-card px-3 py-1 text-xs font-medium text-indigo-700 shadow-sm dark:border-indigo-800/50 dark:text-indigo-300"
        >
          <Icon className="h-3.5 w-3.5" />
          {label}
        </span>
      ))}
    </div>
  );
}
