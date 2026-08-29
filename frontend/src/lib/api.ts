import type { HealthStatus, PrescriptionAnalysis } from "./types";

const API_URL = (process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000").replace(/\/$/, "");

export class ApiError extends Error {
  status: number;

  constructor(message: string, status: number) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

async function parseError(response: Response): Promise<string> {
  try {
    const body = await response.json();
    if (typeof body?.detail === "string") return body.detail;
  } catch {
    // fall through to the default message
  }
  return `Request failed (${response.status}). Please try again.`;
}

/**
 * Upload a prescription image/PDF and receive the full availability analysis.
 * Coordinates are optional and used to sort pharmacies by distance.
 */
export async function analyzePrescription(
  file: File,
  coords?: { lat: number; lng: number } | null,
  signal?: AbortSignal,
): Promise<PrescriptionAnalysis> {
  const form = new FormData();
  form.append("file", file);

  const params = new URLSearchParams();
  if (coords) {
    params.set("lat", String(coords.lat));
    params.set("lng", String(coords.lng));
  }
  const query = params.toString() ? `?${params.toString()}` : "";

  const response = await fetch(`${API_URL}/api/analyze-prescription${query}`, {
    method: "POST",
    body: form,
    signal,
  });

  if (!response.ok) {
    throw new ApiError(await parseError(response), response.status);
  }
  return (await response.json()) as PrescriptionAnalysis;
}

export async function fetchHealth(): Promise<HealthStatus> {
  const response = await fetch(`${API_URL}/api/health`);
  if (!response.ok) {
    throw new ApiError(await parseError(response), response.status);
  }
  return (await response.json()) as HealthStatus;
}

export const apiUrl = API_URL;
