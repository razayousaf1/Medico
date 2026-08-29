import { ImageResponse } from "next/og";

export const size = { width: 180, height: 180 };
export const contentType = "image/png";

export default function AppleIcon() {
  return new ImageResponse(
    (
      <div
        style={{
          width: "100%",
          height: "100%",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          borderRadius: 40,
          background: "linear-gradient(135deg, #4F46E5 0%, #6366F1 100%)",
          color: "#FFFFFF",
          fontFamily: "system-ui, -apple-system, sans-serif",
          fontWeight: 800,
          fontSize: 112,
          letterSpacing: "-0.02em",
          boxShadow: "0 24px 48px rgba(79, 70, 229, 0.35)",
        }}
      >
        M
      </div>
    ),
    size,
  );
}
