import { useEffect, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { useUIStore } from "@store/ui";

const links = [
  { label: "Discover", href: "#home" },
  { label: "Recognition", href: "#recognition" },
  { label: "Heritage", href: "#heritage" },
  { label: "About", href: "#about" },
];

export default function Navigation() {
  const [scrolled, setScrolled] = useState(false);
  const { menuOpen, setMenuOpen } = useUIStore();

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 40);
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  return (
    <>
      <motion.header
        initial={{ y: -80, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        transition={{ duration: 0.7, ease: [0.22, 1, 0.36, 1] }}
        className={`fixed top-0 left-0 right-0 z-50 transition-all duration-300 ${
          scrolled ? "backdrop-blur-md bg-heritage-deep/70 border-b border-line" : "bg-transparent"
        }`}
      >
        <div className="section-shell flex items-center justify-between" style={{ height: "var(--nav-height)" }}>
          <a href="#home" className="flex items-center gap-2.5 group">
            <svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" strokeWidth="1.2" className="text-accent-gold">
              <path d="M3 20h18M5 20V10l7-5 7 5v10M10 20v-6h4v6" />
            </svg>
            <span className="font-display text-sm uppercase tracking-widest text-ink-primary">
              Heritage
            </span>
          </a>

          <nav className="hidden md:flex items-center gap-8" aria-label="Primary">
            {links.map((l) => (
              <a
                key={l.href}
                href={l.href}
                className="relative font-display text-sm text-ink-secondary hover:text-ink-primary transition-colors after:content-[''] after:absolute after:left-0 after:-bottom-1 after:h-px after:w-0 after:bg-accent-gold after:transition-all after:duration-300 hover:after:w-full"
              >
                {l.label}
              </a>
            ))}
          </nav>

          <div className="flex items-center gap-3">
            <a
              href="#recognition"
              className="hidden sm:inline-flex btn btn-primary"
            >
              Identify
            </a>
            <button
              type="button"
              onClick={() => setMenuOpen(!menuOpen)}
              className="md:hidden p-2 rounded-lg border border-line text-ink-primary"
              aria-label={menuOpen ? "Close menu" : "Open menu"}
              aria-expanded={menuOpen}
            >
              <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" strokeWidth="1.5">
                {menuOpen ? (
                  <path d="M6 6l12 12M18 6L6 18" />
                ) : (
                  <path d="M4 6h16M4 12h16M4 18h16" />
                )}
              </svg>
            </button>
          </div>
        </div>
      </motion.header>

      <AnimatePresence>
        {menuOpen && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.3 }}
            className="fixed inset-0 z-40 bg-heritage-deep/95 backdrop-blur-lg md:hidden"
            onClick={() => setMenuOpen(false)}
          >
            <nav className="flex flex-col items-center justify-center h-full gap-8" aria-label="Mobile">
              {links.map((l, i) => (
                <motion.a
                  key={l.href}
                  href={l.href}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.1 * i, duration: 0.4 }}
                  className="font-editorial text-3xl text-ink-primary"
                  onClick={() => setMenuOpen(false)}
                >
                  {l.label}
                </motion.a>
              ))}
            </nav>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
}