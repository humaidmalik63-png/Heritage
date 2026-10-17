import React from 'react';
import { HeroCanvas } from './HeroCanvas';

export const HeroSection: React.FC = () => {
  const scrollToDiscover = () => {
    const el = document.getElementById('journey');
    if (el) el.scrollIntoView({ behavior: 'smooth' });
  };

  const scrollToRecognize = () => {
    const el = document.getElementById('recognize');
    if (el) el.scrollIntoView({ behavior: 'smooth' });
  };

  return (
    <section className="hero-section" id="hero">
      {/* 3D Canvas */}
      <HeroCanvas />

      {/* Gradient overlay */}
      <div className="hero-gradient-overlay" />

      {/* Content */}
      <div className="hero-content">
        <div className="hero-eyebrow">
          <div className="hero-eyebrow-line" />
          <span className="label-gold">Visual Heritage Recognition Platform</span>
        </div>

        <div className="hero-headline">
          <h1 className="display-xl" style={{ whiteSpace: 'pre-line' }}>
            EVERY{'\n'}
            <span style={{ color: 'var(--gold-bright)', fontStyle: 'italic' }}>MONUMENT</span>
            {'\n'}HAS A STORY.
          </h1>
        </div>

        <div className="hero-subtext">
          <p className="editorial">
            Discover cultural heritage through artificial intelligence, immersive exploration,
            and grounded historical knowledge.
          </p>
        </div>

        <div className="hero-actions">
          <button className="btn-primary" onClick={scrollToRecognize} id="hero-begin-btn">
            <span>Begin Your Journey</span>
            <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
              <path d="M3 8H13M13 8L8 3M13 8L8 13" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
            </svg>
          </button>
          <button className="btn-ghost" onClick={scrollToDiscover} id="hero-discover-btn">
            <span>Explore Monuments</span>
          </button>
        </div>
      </div>

      {/* Scroll indicator */}
      <div className="scroll-indicator">
        <div className="scroll-indicator-line" />
        <span className="scroll-indicator-label">Scroll</span>
      </div>

      {/* Bottom fade */}
      <div style={{
        position: 'absolute',
        bottom: 0,
        left: 0,
        right: 0,
        height: '200px',
        background: 'linear-gradient(to top, var(--bg-void), transparent)',
        zIndex: 2,
        pointerEvents: 'none',
      }} />
    </section>
  );
};
