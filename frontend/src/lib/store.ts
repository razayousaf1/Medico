import type { PrescriptionAnalysis, UserLocation } from "./types";

const ANALYSIS_KEY = "medico:analysis";
const LOCATION_KEY = "medico:location";

/** Persist the latest analysis so /dashboard can render after navigation. */
export function saveAnalysis(analysis: PrescriptionAnalysis): void {
  try {
    sessionStorage.setItem(ANALYSIS_KEY, JSON.stringify(analysis));
  } catch {
    // Storage full / unavailable — the app still works within the page session.
  }
}

export function loadAnalysis(): PrescriptionAnalysis | null {
  try {
    const raw = sessionStorage.getItem(ANALYSIS_KEY);
    if (!raw) return null;
    const parsed = JSON.parse(raw) as PrescriptionAnalysis;
    return Array.isArray(parsed.medicines) ? parsed : null;
  } catch {
    return null;
  }
}

export function clearAnalysis(): void {
  try {
    sessionStorage.removeItem(ANALYSIS_KEY);
  } catch {
    // ignore
  }
}

export function saveLocation(location: UserLocation): void {
  try {
    sessionStorage.setItem(LOCATION_KEY, JSON.stringify(location));
  } catch {
    // ignore
  }
}

export function loadLocation(): UserLocation | null {
  try {
    const raw = sessionStorage.getItem(LOCATION_KEY);
    return raw ? (JSON.parse(raw) as UserLocation) : null;
  } catch {
    return null;
  }
}

/** Best-effort browser geolocation with a timeout, falling back to Lahore centre. */
export function getUserLocation(timeoutMs = 6000): Promise<UserLocation | null> {
  if (typeof navigator === "undefined" || !navigator.geolocation) {
    return Promise.resolve(null);
  }
  return new Promise((resolve) => {
    let settled = false;
    const timer = setTimeout(() => {
      if (!settled) {
        settled = true;
        resolve(null);
      }
    }, timeoutMs);

    navigator.geolocation.getCurrentPosition(
      (position) => {
        if (settled) return;
        settled = true;
        clearTimeout(timer);
        resolve({
          lat: position.coords.latitude,
          lng: position.coords.longitude,
        });
      },
      () => {
        if (settled) return;
        settled = true;
        clearTimeout(timer);
        resolve(null);
      },
      { enableHighAccuracy: false, timeout: timeoutMs, maximumAge: 300_000 },
    );
  });
}
