import React, { useEffect, useRef } from 'react';
import { motion, useScroll, useTransform } from 'framer-motion';

export const CtaSection: React.FC = () => {
  const sectionRef = useRef<HTMLElement>(null);
  const { scrollYProgress } = useScroll({ target: sectionRef, offset: ['start end', 'end start'] });
  const scale = useTransform(scrollYProgress, [0, 0.5], [0.92, 1]);
  const opacity = useTransform(scrollYProgress, [0, 0.3], [0, 1]);

  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) entry.target.classList.add('visible');
        });
      },
      { threshold: 0.2 }
    );
    sectionRef.current?.querySelectorAll('.reveal').forEach((el) => observer.observe(el));
    return () => observer.disconnect();
  }, []);

  const scrollToRecognize = () => {
    const el = document.getElementById('recognize');
    if (el) el.scrollIntoView({ behavior: 'smooth' });
  };

  return (
    <section className="cta-section" ref={sectionRef} id="cta">
      {/* Background watermark */}
      <div className="cta-bg-text">HERITAGE</div>

      {/* Decorative lines */}
      <div style={{
        position: 'absolute',
        inset: 0,
        background: `
          repeating-linear-gradient(
            0deg,
            transparent,
            transparent 80px,
            rgba(201,168,76,0.02) 80px,
            rgba(201,168,76,0.02) 81px
          )
        `,
        pointerEvents: 'none',
      }} />

      <motion.div
        style={{ scale, opacity }}
        className="container"
      >
        <div style={{ position: 'relative', zIndex: 1 }}>
          <p className="label-gold reveal" style={{ marginBottom: '20px' }}>Scene Six · Final</p>

          <div className="gold-line gold-line-center reveal reveal-delay-1" />

          <h2 className="display-lg reveal reveal-delay-2" style={{ marginBottom: '32px', lineHeight: 1.05 }}>
            Discover Your
            <br />
            <span style={{ color: 'var(--gold-bright)', fontStyle: 'italic' }}>Next Story.</span>
          </h2>

          <p className="editorial reveal reveal-delay-3" style={{
            maxWidth: '560px',
            margin: '0 auto 48px',
          }}>
            Every photograph you take could be a doorway into five thousand years of civilisation.
            Let the platform show you what's on the other side.
          </p>

          <div style={{ display: 'flex', gap: '20px', justifyContent: 'center', flexWrap: 'wrap' }} className="reveal reveal-delay-4">
            <button className="btn-primary" onClick={scrollToRecognize} id="cta-begin-btn">
              <span>Begin Recognition</span>
              <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                <path d="M3 8H13M13 8L8 3M13 8L8 13" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
              </svg>
            </button>
          </div>

          {/* Project attribution */}
          <div className="reveal reveal-delay-5" style={{ marginTop: '80px' }}>
            <div style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '20px',
              padding: '16px 32px',
              border: '1px solid rgba(201,168,76,0.15)',
              background: 'rgba(8,7,6,0.6)',
            }}>
              <div>
                <p className="label-gold" style={{ marginBottom: '4px' }}>Smart India Hackathon</p>
                <p className="body-text" style={{ fontSize: '0.82rem' }}>
                  Visual Heritage Recognition &amp; Grounded Cultural Discovery Platform
                </p>
              </div>
              <div style={{ width: '1px', height: '40px', background: 'rgba(201,168,76,0.2)' }} />
              <div>
                <p className="label-gold" style={{ marginBottom: '4px' }}>Powered by</p>
                <p className="body-text" style={{ fontSize: '0.82rem' }}>CLIP · FAISS · Ollama · FastAPI</p>
              </div>
            </div>
          </div>
        </div>
      </motion.div>
    </section>
  );
};

export const Footer: React.FC = () => (
  <footer style={{
    padding: '40px 0',
    borderTop: '1px solid rgba(201,168,76,0.1)',
    background: 'var(--bg-void)',
  }}>
    <div className="container" style={{
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      flexWrap: 'wrap',
      gap: '16px',
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
        <svg width="20" height="20" viewBox="0 0 28 28" fill="none">
          <path d="M14 2L26 9V19L14 26L2 19V9L14 2Z" stroke="#c9a84c" strokeWidth="1.5" fill="none"/>
          <circle cx="14" cy="14" r="2" fill="#c9a84c"/>
        </svg>
        <span style={{ fontFamily: 'var(--font-display)', fontSize: '0.9rem', color: 'var(--ivory-muted)' }}>
          Heritage Discovery Platform
        </span>
      </div>
      <p className="body-text" style={{ fontSize: '0.78rem', color: 'var(--ivory-faint)' }}>
        Smart India Hackathon · Cultural heritage through artificial intelligence
      </p>
    </div>
  </footer>
);
