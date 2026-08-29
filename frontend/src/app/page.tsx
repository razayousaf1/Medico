"use client";

import { motion } from "framer-motion";
import {
  BadgeCheck,
  BrainCircuit,
  Clock,
  FileSearch,
  Languages,
  MapPinned,
  Pill,
  ShieldCheck,
  Sparkles,
} from "lucide-react";

import { Footer } from "@/components/site/footer";
import { HeroBadges, Navbar } from "@/components/site/navbar";
import { UploadZone } from "@/components/upload/upload-zone";

const fadeUp = {
  hidden: { opacity: 0, y: 16 },
  visible: (delay: number) => ({
    opacity: 1,
    y: 0,
    transition: { duration: 0.4, delay, ease: [0.21, 0.47, 0.32, 0.98] as const },
  }),
};

const STEPS = [
  {
    icon: FileSearch,
    title: "Upload the prescription",
    description:
      "Snap a photo or scan — JPG, PNG or PDF. Our PaddleOCR engine reads every line, even messy handwriting.",
  },
  {
    icon: BrainCircuit,
    title: "Gemini AI understands it",
    description:
      "The AI corrects OCR mistakes, identifies each medicine, its generic name, strength and what the abbreviations mean.",
  },
  {
    icon: MapPinned,
    title: "Find it near you",
    description:
      "We check live pharmacy stock and prices on the map, and suggest available alternatives when something is out of stock.",
  },
];

const FEATURES = [
  {
    icon: Sparkles,
    title: "OCR error correction",
    description: "Handwriting and scan artefacts are cleaned up before a single medicine is identified.",
  },
  {
    icon: Languages,
    title: "Abbreviation decoder",
    description: "SOS, BD, TDS, OD, HS, 1-0-1 — every instruction is translated into plain language.",
  },
  {
    icon: BadgeCheck,
    title: "Generic name lookup",
    description: "Brand names are mapped to their active composition so alternatives always match.",
  },
  {
    icon: Pill,
    title: "Alternative suggestions",
    description: "Out of stock? Gemini recommends equivalent brands commonly available in Pakistan.",
  },
  {
    icon: Clock,
    title: "Live stock & prices",
    description: "See stock levels and PKR prices across pharmacies, sorted by distance from you.",
  },
  {
    icon: MapPinned,
    title: "Interactive pharmacy map",
    description: "OpenStreetMap view of every pharmacy that stocks your prescription, one tap away.",
  },
];

export default function LandingPage() {
  return (
    <div className="flex min-h-screen flex-col">
      <Navbar />

      {/* ---------------- Hero ---------------- */}
      <section className="relative overflow-hidden">
        <div className="bg-grid pointer-events-none absolute inset-0 [mask-image:radial-gradient(ellipse_75%_60%_at_50%_0%,black,transparent)]" />
        <div className="glow-indigo pointer-events-none absolute inset-x-0 top-0 h-[480px]" />

        <div className="relative mx-auto grid max-w-6xl gap-12 px-4 pb-16 pt-14 sm:px-6 lg:grid-cols-2 lg:items-center lg:gap-16 lg:pb-24 lg:pt-20">
          <div>
            <motion.div variants={fadeUp} initial="hidden" animate="visible" custom={0}>
              <span className="inline-flex items-center gap-2 rounded-full border border-indigo-200 bg-card px-3.5 py-1.5 text-xs font-semibold text-indigo-700 shadow-sm dark:border-indigo-800/50 dark:text-indigo-300">
                <Sparkles className="h-3.5 w-3.5" />
                AI-powered prescription intelligence
              </span>
            </motion.div>

            <motion.h1
              variants={fadeUp}
              initial="hidden"
              animate="visible"
              custom={0.1}
              className="font-heading mt-6 text-4xl font-extrabold leading-[1.08] tracking-tight sm:text-5xl lg:text-[3.4rem]"
            >
              Understand your prescription.{" "}
              <span className="text-gradient-indigo">Find your medicine.</span> Nearby.
            </motion.h1>

            <motion.p
              variants={fadeUp}
              initial="hidden"
              animate="visible"
              custom={0.2}
              className="mt-5 max-w-xl text-lg leading-relaxed text-muted-foreground"
            >
              Upload a photo of any prescription. Medico reads it with OCR, structures it
              with Gemini AI, explains every abbreviation and checks real-time availability
              and prices at pharmacies around you.
            </motion.p>

            <motion.div
              variants={fadeUp}
              initial="hidden"
              animate="visible"
              custom={0.3}
              className="mt-7"
            >
              <HeroBadges />
            </motion.div>

            <motion.dl
              variants={fadeUp}
              initial="hidden"
              animate="visible"
              custom={0.4}
              className="mt-10 grid max-w-md grid-cols-3 gap-6"
            >
              {[
                { value: "3s", label: "Average analysis" },
                { value: "30+", label: "Medicines tracked" },
                { value: "8", label: "Partner pharmacies" },
              ].map((stat) => (
                <div key={stat.label}>
                  <dt className="font-heading text-2xl font-extrabold tracking-tight text-indigo-600 dark:text-indigo-400">{stat.value}</dt>
                  <dd className="mt-1 text-xs font-medium text-muted-foreground">{stat.label}</dd>
                </div>
              ))}
            </motion.dl>
          </div>

          <motion.div
            id="upload"
            initial={{ opacity: 0, y: 32, scale: 0.98 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            transition={{ duration: 0.5, delay: 0.25, ease: [0.21, 0.47, 0.32, 0.98] }}
            className="scroll-mt-24"
          >
            <UploadZone />
            <p className="mt-4 flex items-center justify-center gap-1.5 text-center text-xs text-muted-foreground">
              <ShieldCheck className="h-3.5 w-3.5 text-indigo-500" />
              Your prescription is processed for this analysis only and never shared.
            </p>
          </motion.div>
        </div>
      </section>

      {/* ---------------- How it works ---------------- */}
      <section id="how-it-works" className="border-t border-border/60 bg-card py-20">
        <div className="mx-auto max-w-6xl px-4 sm:px-6">
          <motion.div
            variants={fadeUp}
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true, margin: "-80px" }}
            custom={0}
            className="mx-auto max-w-2xl text-center"
          >
            <h2 className="font-heading text-3xl font-extrabold tracking-tight sm:text-4xl">
              From a photo to a pharmacy, in three steps
            </h2>
            <p className="mt-4 text-lg text-muted-foreground">
              Everything runs automatically the moment you drop the file.
            </p>
          </motion.div>

          <div className="relative mt-14 grid gap-8 md:grid-cols-3">
            <div className="pointer-events-none absolute left-0 right-0 top-8 hidden border-t-2 border-dashed border-indigo-200/70 md:block dark:border-indigo-800/50" />
            {STEPS.map((step, index) => (
              <motion.div
                key={step.title}
                variants={fadeUp}
                initial="hidden"
                whileInView="visible"
                viewport={{ once: true, margin: "-60px" }}
                custom={index * 0.15}
                className="relative"
              >
                <div className="card-hover relative rounded-2xl border border-border/80 bg-card p-6">
                  <span className="absolute -top-4 left-6 flex h-8 w-8 items-center justify-center rounded-full bg-gradient-to-br from-indigo-500 to-indigo-700 text-sm font-bold font-heading text-white shadow-md shadow-indigo-500/25">
                    {index + 1}
                  </span>
                  <step.icon className="mt-2 h-8 w-8 text-indigo-600 dark:text-indigo-400" strokeWidth={1.8} />
                  <h3 className="font-heading mt-4 text-lg font-bold tracking-tight">{step.title}</h3>
                  <p className="mt-2 text-sm leading-relaxed text-muted-foreground">{step.description}</p>
                </div>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* ---------------- Features ---------------- */}
      <section id="features" className="py-20">
        <div className="mx-auto max-w-6xl px-4 sm:px-6">
          <motion.div
            variants={fadeUp}
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true, margin: "-80px" }}
            custom={0}
            className="mx-auto max-w-2xl text-center"
          >
            <h2 className="font-heading text-3xl font-extrabold tracking-tight sm:text-4xl">
              Everything on the label, decoded
            </h2>
            <p className="mt-4 text-lg text-muted-foreground">
              The details that usually require a call to your pharmacist.
            </p>
          </motion.div>

          <div className="mt-14 grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
            {FEATURES.map((feature, index) => (
              <motion.div
                key={feature.title}
                variants={fadeUp}
                initial="hidden"
                whileInView="visible"
                viewport={{ once: true, margin: "-40px" }}
                custom={(index % 3) * 0.12}
                className="card-hover rounded-2xl border border-border/80 bg-card p-6"
              >
                <span className="flex h-11 w-11 items-center justify-center rounded-xl bg-secondary text-indigo-700 dark:text-indigo-300">
                  <feature.icon className="h-5 w-5" strokeWidth={1.9} />
                </span>
                <h3 className="font-heading mt-4 font-bold tracking-tight">{feature.title}</h3>
                <p className="mt-1.5 text-sm leading-relaxed text-muted-foreground">{feature.description}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* ---------------- Trust / privacy ---------------- */}
      <section id="trust" className="border-t border-border/60 bg-card py-16">
        <div className="mx-auto flex max-w-6xl flex-col items-center gap-4 px-4 text-center sm:px-6">
          <ShieldCheck className="h-10 w-10 text-indigo-500" strokeWidth={1.6} />
          <h2 className="font-heading text-2xl font-extrabold tracking-tight">Privacy first</h2>
          <p className="max-w-2xl text-sm leading-relaxed text-muted-foreground">
            Images are processed to extract the prescription text and are not stored.
            Analysis results live in your browser session only. Medico is an
            information tool — always confirm dosages with a licensed pharmacist.
          </p>
        </div>
      </section>

      <div className="flex-1" />
      <Footer />
    </div>
  );
}
