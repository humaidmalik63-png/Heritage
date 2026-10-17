import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

interface NavProps {
  onNavigate: (section: string) => void;
}

const navItems = [
  { label: 'Home', id: 'hero' },
  { label: 'Discover', id: 'journey' },
  { label: 'Recognize', id: 'recognize' },
  { label: 'Explore', id: 'monuments' },
  { label: 'About', id: 'about' },
];

export const Navigation: React.FC<NavProps> = ({ onNavigate }) => {
  const [scrolled, setScrolled] = useState(false);
  const [menuOpen, setMenuOpen] = useState(false);

  useEffect(() => {
    const handleScroll = () => setScrolled(window.scrollY > 60);
    window.addEventListener('scroll', handleScroll, { passive: true });
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  const scrollTo = (id: string) => {
    const el = document.getElementById(id);
    if (el) el.scrollIntoView({ behavior: 'smooth', block: 'start' });
    setMenuOpen(false);
    onNavigate(id);
  };

  return (
    <nav className={`nav-container${scrolled ? ' scrolled' : ''}`}>
      {/* Logo */}
      <a className="nav-logo" onClick={() => scrollTo('hero')} style={{ cursor: 'pointer' }}>
        <svg width="28" height="28" viewBox="0 0 28 28" fill="none">
          <path d="M14 2L26 9V19L14 26L2 19V9L14 2Z" stroke="#c9a84c" strokeWidth="1.5" fill="none"/>
          <path d="M14 8L20 11.5V18.5L14 22L8 18.5V11.5L14 8Z" fill="rgba(201,168,76,0.15)" stroke="#c9a84c" strokeWidth="1"/>
          <circle cx="14" cy="14" r="2" fill="#c9a84c"/>
        </svg>
        Heritage<span className="nav-logo-accent">.</span>
      </a>

      {/* Desktop nav */}
      <ul className="nav-links">
        {navItems.map((item) => (
          <li key={item.id}>
            <a
              className="nav-link"
              onClick={() => scrollTo(item.id)}
              aria-label={`Navigate to ${item.label}`}
            >
              {item.label}
            </a>
          </li>
        ))}
      </ul>

      {/* Mobile burger */}
      <button
        className="nav-link"
        style={{ display: 'none', background: 'none', border: 'none', fontSize: '1.5rem' }}
        onClick={() => setMenuOpen(!menuOpen)}
        aria-label="Open menu"
        id="mobile-menu-btn"
      >
        ☰
      </button>

      {/* Mobile drawer */}
      <AnimatePresence>
        {menuOpen && (
          <motion.div
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            style={{
              position: 'fixed',
              top: 0,
              left: 0,
              right: 0,
              bottom: 0,
              background: 'rgba(8,7,6,0.97)',
              zIndex: 999,
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '40px',
            }}
          >
            <button onClick={() => setMenuOpen(false)} style={{ position: 'absolute', top: 24, right: 24, background: 'none', border: 'none', color: '#c9a84c', fontSize: '1.5rem', cursor: 'pointer' }}>✕</button>
            {navItems.map((item) => (
              <a
                key={item.id}
                className="display-md"
                onClick={() => scrollTo(item.id)}
                style={{ cursor: 'pointer', textDecoration: 'none' }}
              >
                {item.label}
              </a>
            ))}
          </motion.div>
        )}
      </AnimatePresence>
    </nav>
  );
};
