export function Footer() {
  return (
    <footer className="border-t border-border/60 bg-card">
      <div className="mx-auto max-w-6xl px-4 py-10 sm:px-6">
        <div className="flex flex-col items-start justify-between gap-6 md:flex-row md:items-center">
          <div>
            <p className="text-sm font-semibold">Medico</p>
            <p className="mt-1 text-sm text-muted-foreground">
              Prescription intelligence &amp; medicine availability.
            </p>
          </div>
          <p className="max-w-md text-xs leading-relaxed text-muted-foreground">
            Medico is an information tool, not medical advice. Always follow your
            doctor&apos;s instructions and confirm dosages with a licensed pharmacist
            before taking any medicine.
          </p>
        </div>
        <div className="mt-8 border-t border-border/60 pt-6 text-xs text-muted-foreground">
          © {new Date().getFullYear()} Medico. Built with Next.js, FastAPI, PaddleOCR, Gemini &amp; Firestore.
        </div>
      </div>
    </footer>
  );
}
