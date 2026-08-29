import type { Metadata, Viewport } from "next";
import { Inter, Poppins } from "next/font/google";

import { ThemedToaster } from "@/components/ui/toaster";

import "./globals.css";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-inter",
  display: "swap",
});

const poppins = Poppins({
  subsets: ["latin"],
  weight: ["600", "700", "800"],
  variable: "--font-poppins",
  display: "swap",
});

export const metadata: Metadata = {
  title: {
    default: "Medico — Prescription Intelligence & Medicine Availability",
    template: "%s · Medico",
  },
  description:
    "Upload a prescription and instantly understand it — AI reads the handwriting, explains the abbreviations and checks live availability at pharmacies near you.",
  keywords: ["prescription", "OCR", "medicine availability", "pharmacy", "Pakistan", "AI"],
};

export const viewport: Viewport = {
  themeColor: [
    { media: "(prefers-color-scheme: light)", color: "#F8FAFC" },
    { media: "(prefers-color-scheme: dark)", color: "#0F172A" },
  ],
  width: "device-width",
  initialScale: 1,
};

const THEME_BOOT = `(function(){try{var t=localStorage.getItem("medico:theme");if(t==="dark"){document.documentElement.classList.add("dark");document.documentElement.dataset.theme="dark";}}catch(e){}})();`;

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html
      lang="en"
      className={`${inter.variable} ${poppins.variable}`}
      data-scroll-behavior="smooth"
      suppressHydrationWarning
    >
      <head>
        <script dangerouslySetInnerHTML={{ __html: THEME_BOOT }} />
      </head>
      <body className="min-h-screen font-sans antialiased">
        {children}
        <ThemedToaster />
      </body>
    </html>
  );
}
