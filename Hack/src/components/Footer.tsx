import Reveal from "@components/Reveal";

export default function Footer() {
  return (
    <footer className="border-t border-line bg-heritage-surface/30">
      <div className="section-shell py-16">
        <div className="flex flex-col md:flex-row items-center justify-between gap-6">
          <Reveal>
            <div className="flex items-center gap-2.5">
              <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" strokeWidth="1.2" className="text-accent-gold">
                <path d="M3 20h18M5 20V10l7-5 7 5v10M10 20v-6h4v6" />
              </svg>
              <span className="font-display text-xs uppercase tracking-widest text-ink-secondary">
                Heritage Discovery
              </span>
            </div>
          </Reveal>
          <Reveal delay={0.1}>
            <p className="font-display text-sm text-ink-secondary">
              Recognise the stories of place.
            </p>
          </Reveal>
          <Reveal delay={0.2}>
            <p className="font-display text-xs text-ink-muted">
              © {new Date().getFullYear()} Heritage Discovery. Built with care.
            </p>
          </Reveal>
        </div>
      </div>
    </footer>
  );
}