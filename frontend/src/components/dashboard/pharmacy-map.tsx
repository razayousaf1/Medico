"use client";

import { useEffect, useMemo, useState } from "react";
import { motion } from "framer-motion";
import { Crosshair, Layers, MapPin, Navigation, Store } from "lucide-react";
import L from "leaflet";
import "leaflet/dist/leaflet.css";
import { CircleMarker, MapContainer, Marker, Popup, TileLayer, useMap } from "react-leaflet";

import { Badge } from "@/components/ui/badge";
import type { MapPharmacy } from "@/lib/types";
import { cn, formatDistance, formatPKR } from "@/lib/utils";

const LAHORE: [number, number] = [31.5497, 74.3436];

function createPin(innerSvg: string, low = false) {
  return L.divIcon({
    className: "medico-marker",
    html: `<div class="medico-marker__pin ${low ? "medico-marker__pin--low" : ""}">${innerSvg}</div>`,
    iconSize: [34, 34],
    iconAnchor: [17, 17],
    popupAnchor: [0, -18],
  });
}

const pharmacyIcon = createPin(
  '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M18 6 6 18"/><path d="m6 6 12 12"/></svg>',
);
const lowStockIcon = createPin(
  '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M10.29 3.86 1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><path d="M12 9v4"/><path d="M12 17h.01"/></svg>',
  true,
);
const userIcon = L.divIcon({
  className: "medico-marker",
  html: `<div class="medico-marker__pin medico-marker__pin--user"><svg xmlns="http://www.w3.org/2000/svg" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><circle cx="12" cy="12" r="2"/></svg></div>`,
  iconSize: [34, 34],
  iconAnchor: [17, 17],
});

function FitBounds({ points }: { points: [number, number][] }) {
  const map = useMap();
  useEffect(() => {
    if (points.length === 0) return;
    if (points.length === 1) {
      map.setView(points[0], 13, { animate: true });
      return;
    }
    map.fitBounds(L.latLngBounds(points).pad(0.18), { animate: true });
  }, [map, points]);
  return null;
}

export interface PharmacyMapProps {
  pharmacies: MapPharmacy[];
  userLocation: { lat: number; lng: number } | null;
}

export function PharmacyMap({ pharmacies, userLocation: rawLocation }: PharmacyMapProps) {
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const userLocation =
    rawLocation && typeof rawLocation.lat === "number" && typeof rawLocation.lng === "number"
      ? rawLocation
      : null;

  const points = useMemo<[number, number][]>(() => {
    const list: [number, number][] = pharmacies.map((p) => [p.pharmacy.lat, p.pharmacy.lng]);
    if (userLocation) list.push([userLocation.lat, userLocation.lng]);
    return list;
  }, [pharmacies, userLocation]);

  if (pharmacies.length === 0) {
    return (
      <div className="flex h-[380px] flex-col items-center justify-center gap-3 rounded-2xl border border-border/80 bg-muted/40 text-center">
        <MapPin className="h-8 w-8 text-muted-foreground" strokeWidth={1.6} />
        <div>
          <p className="font-semibold">No pharmacies to show</p>
          <p className="mt-1 text-sm text-muted-foreground">
            None of the medicines on this prescription were found in the pharmacy database.
          </p>
        </div>
      </div>
    );
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, delay: 0.15 }}
      className="overflow-hidden rounded-2xl border border-border/80 bg-card shadow-lg shadow-indigo-500/5"
    >
      <div className="flex flex-wrap items-center justify-between gap-2 border-b border-border/70 px-4 py-3">
        <div className="flex items-center gap-2">
          <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-secondary text-indigo-700 dark:text-indigo-300">
            <Navigation className="h-4 w-4" />
          </span>
          <div>
            <h2 className="font-heading text-sm font-bold tracking-tight">Nearby pharmacies</h2>
            <p className="text-xs text-muted-foreground">
              {pharmacies.length} with your medicines in stock · OpenStreetMap
            </p>
          </div>
        </div>
        <div className="flex items-center gap-3 text-xs text-muted-foreground">
          <span className="inline-flex items-center gap-1.5">
            <span className="h-2.5 w-2.5 rounded-full bg-indigo-600 dark:bg-indigo-400" /> In stock
          </span>
          <span className="inline-flex items-center gap-1.5">
            <span className="h-2.5 w-2.5 rounded-full bg-amber-500" /> Low stock
          </span>
          {userLocation && (
            <span className="inline-flex items-center gap-1.5">
              <span className="h-2.5 w-2.5 rounded-full bg-blue-600" /> You
            </span>
          )}
        </div>
      </div>

      <MapContainer
        center={userLocation ? [userLocation.lat, userLocation.lng] : LAHORE}
        zoom={12}
        scrollWheelZoom
        className="h-[380px] w-full sm:h-[420px]"
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        <FitBounds points={points} />

        {userLocation && (
          <>
            <Marker position={[userLocation.lat, userLocation.lng]} icon={userIcon}>
              <Popup>
                <div className="text-sm font-semibold">Your location</div>
              </Popup>
            </Marker>
            <CircleMarker
              center={[userLocation.lat, userLocation.lng]}
              radius={64}
              pathOptions={{ color: "#2563eb", weight: 1, fillColor: "#2563eb", fillOpacity: 0.06 }}
            />
          </>
        )}

        {pharmacies.map((entry) => {
          const { pharmacy, medicines } = entry;
          const hasStock = medicines.some((m) => m.in_stock);
          const selected = selectedId === pharmacy.id;
          return (
            <Marker
              key={pharmacy.id}
              position={[pharmacy.lat, pharmacy.lng]}
              icon={hasStock ? pharmacyIcon : lowStockIcon}
              eventHandlers={{ popupopen: () => setSelectedId(pharmacy.id) }}
              zIndexOffset={selected ? 1000 : 0}
            >
              <Popup>
                <div className="min-w-[210px]">
                  <p className="text-sm font-bold leading-snug">
                    {pharmacy.name}
                    {pharmacy.branch ? <span className="font-medium text-muted-foreground"> — {pharmacy.branch}</span> : null}
                  </p>
                  <p className="mt-0.5 text-xs text-muted-foreground">{pharmacy.address}</p>
                  <div className="mt-1.5 flex flex-wrap items-center gap-x-2.5 gap-y-1 text-xs text-muted-foreground">
                    {pharmacy.distance_km != null && (
                      <span className="font-semibold text-indigo-600 dark:text-indigo-400">
                        {formatDistance(pharmacy.distance_km)} away
                      </span>
                    )}
                    {pharmacy.open_hours && <span>{pharmacy.open_hours}</span>}
                    {pharmacy.phone && <span>{pharmacy.phone}</span>}
                  </div>
                  <ul className="mt-2 space-y-1">
                    {medicines.slice(0, 6).map((medicine, index) => (
                      <li
                        key={`${medicine.brand}-${medicine.strength ?? ""}-${index}`}
                        className={cn(
                          "flex items-center justify-between gap-2 rounded-md px-2 py-1 text-xs",
                          medicine.in_stock ? "bg-indigo-50 dark:bg-indigo-950/40" : "bg-muted",
                        )}
                      >
                        <span className="font-medium">
                          {medicine.brand}
                          {medicine.strength ? ` ${medicine.strength}` : ""}
                        </span>
                        <span className={cn("font-semibold", medicine.in_stock ? "text-indigo-600 dark:text-indigo-400" : "text-muted-foreground")}>
                          {medicine.in_stock ? formatPKR(medicine.price) : "Out"}
                        </span>
                      </li>
                    ))}
                    {medicines.length > 6 && (
                      <li className="px-2 text-xs text-muted-foreground">+{medicines.length - 6} more</li>
                    )}
                  </ul>
                </div>
              </Popup>
            </Marker>
          );
        })}
      </MapContainer>

      <div className="flex items-center justify-between gap-2 border-t border-border/70 bg-muted/30 px-4 py-2.5 text-xs text-muted-foreground">
        <span className="inline-flex items-center gap-1.5">
          <Layers className="h-3.5 w-3.5" /> Click a pin for stock &amp; prices
        </span>
        <Badge variant="outline" className="gap-1">
          <Crosshair className="h-3 w-3" />
          {pharmacies.length} pharmacies
        </Badge>
      </div>
    </motion.div>
  );
}
