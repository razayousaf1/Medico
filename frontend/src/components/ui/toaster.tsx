"use client";

import { Toaster } from "sonner";

import { useTheme } from "@/lib/use-theme";

export function ThemedToaster() {
  const { theme } = useTheme();
  return <Toaster position="top-center" richColors closeButton theme={theme} />;
}
