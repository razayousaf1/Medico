import { ImageResponse } from "next/og";

export const size = { width: 32, height: 32 };
export const contentType = "image/png";

export default function Icon() {
  return new ImageResponse(
    (
      <div
        style={{
          width: "100%",
          height: "100%",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          borderRadius: 8,
          background: "linear-gradient(135deg, #4F46E5 0%, #6366F1 100%)",
          color: "#FFFFFF",
          fontFamily: "system-ui, -apple-system, sans-serif",
          fontWeight: 800,
          fontSize: 20,
          letterSpacing: "-0.02em",
          boxShadow: "0 4px 12px rgba(79, 70, 229, 0.35)",
        }}
      >
        M
      </div>
    ),
    size,
  );
}
