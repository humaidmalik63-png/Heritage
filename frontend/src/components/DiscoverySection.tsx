import React, { useEffect, useRef } from 'react';
import { motion, useScroll, useTransform } from 'framer-motion';

const discoveryPanels = [
  {
    icon: '◈',
    title: 'Grounded Knowledge',
    description:
      'Every historical fact surfaced by the platform is anchored to evidence from our curated catalogue — no hallucinated dates, no invented attributions.',
  },
  {
    icon: '◎',
    title: 'Visual Intelligence',
    description:
      'CLIP-based embeddings understand monuments the way a trained archaeologist does — by composition, style, material, and structural signature.',
  },
  {
    icon: '◇',
    title: 'Cultural Context',
    description:
      'Beyond identification, the system traces dynasties, patrons, architectural schools, and the human stories embedded in every carved surface.',
  },
  {
    icon: '◉',
    title: 'Evidence Chain',
    description:
      'All responses cite their sources. The RAG pipeline retrieves, ranks, and presents evidence so you can verify every claim independently.',
  },
];

const relatedSites = [
  { name: 'Humayun\'s Tomb', location: 'Delhi', category: 'Mausoleum', year: '1572' },
  { name: 'Fatehpur Sikri', location: 'Agra', category: 'Palace Complex', year: '1571' },
  { name: 'Khajuraho Group', location: 'Madhya Pradesh', category: 'Temples', year: '950–1050' },
  { name: 'Hampi Monuments', location: 'Karnataka', category: 'Vijayanagara Capital', year: '14th c.' },
  { name: 'Sanchi Stupa', location: 'Madhya Pradesh', category: 'Buddhist Stupa', year: '3rd c. BCE' },
  { name: 'Elephanta Caves', location: 'Mumbai Harbour', category: 'Rock-Cut Temple', year: '6th–8th c.' },
];

export const DiscoverySection: React.FC = () => {
  const sectionRef = useRef<HTMLElement>(null);
  const { scrollYProgress } = useScroll({ target: sectionRef, offset: ['start end', 'end start'] });
  const y = useTransform(scrollYProgress, [0, 1], [40, -40]);

  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) entry.target.classList.add('visible');
        });
      },
      { threshold: 0.15 }
    );
    sectionRef.current?.querySelectorAll('.reveal').forEach((el) => observer.observe(el));
    return () => observer.disconnect();
  }, []);

  return (
    <section ref={sectionRef} id="about" style={{
      padding: 'var(--section-pad) 0',
      background: 'linear-gradient(180deg, var(--bg-deep) 0%, var(--bg-void) 100%)',
      position: 'relative',
      overflow: 'hidden',
    }}>
      {/* Decorative arch background */}
      <div style={{
        position: 'absolute',
        top: '50%',
        left: '50%',
        transform: 'translate(-50%, -50%)',
        width: '800px',
        height: '800px',
        border: '1px solid rgba(201,168,76,0.04)',
        borderRadius: '50%',
        pointerEvents: 'none',
      }} />
      <div style={{
        position: 'absolute',
        top: '50%',
        left: '50%',
        transform: 'translate(-50%, -50%)',
        width: '1200px',
        height: '1200px',
        border: '1px solid rgba(201,168,76,0.025)',
        borderRadius: '50%',
        pointerEvents: 'none',
      }} />

      <div className="container">
        {/* Header */}
        <div className="reveal" style={{ textAlign: 'center', marginBottom: '80px' }}>
          <p className="label-gold" style={{ marginBottom: '16px' }}>Scene Five</p>
          <div className="gold-line gold-line-center" />
          <h2 className="display-lg" style={{ marginBottom: '24px' }}>Cultural Discovery</h2>
          <p className="editorial" style={{ maxWidth: '620px', margin: '0 auto' }}>
            The platform connects visual recognition to deep historical knowledge,
            building bridges between what you see and what it means.
          </p>
        </div>

        {/* Feature panels */}
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
          gap: '2px',
          background: 'rgba(201,168,76,0.06)',
          marginBottom: '80px',
        }}>
          {discoveryPanels.map((panel, i) => (
            <motion.div
              key={i}
              className={`reveal reveal-delay-${i + 1}`}
              whileHover={{ background: 'rgba(201,168,76,0.04)' }}
              style={{
                background: 'var(--bg-void)',
                padding: '48px 40px',
                transition: 'background 0.3s ease',
              }}
            >
              <div style={{
                fontSize: '1.8rem',
                color: 'var(--gold-bright)',
                marginBottom: '20px',
                fontFamily: 'monospace',
              }}>
                {panel.icon}
              </div>
              <h3 style={{
                fontFamily: 'var(--font-display)',
                fontSize: '1.3rem',
                fontWeight: 600,
                color: 'var(--ivory-primary)',
                marginBottom: '16px',
              }}>
                {panel.title}
              </h3>
              <p className="body-text" style={{ fontSize: '0.9rem' }}>{panel.description}</p>
            </motion.div>
          ))}
        </div>

        {/* Related sites catalogue */}
        <div className="reveal reveal-delay-2">
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '32px', flexWrap: 'wrap', gap: '16px' }}>
            <div>
              <p className="label-gold" style={{ marginBottom: '8px' }}>Also in the Catalogue</p>
              <div className="gold-line" />
            </div>
            <p className="body-text" style={{ fontSize: '0.82rem' }}>23 monuments · continuously expanding</p>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '1px', background: 'rgba(201,168,76,0.08)' }}>
            {relatedSites.map((site, i) => (
              <div key={i} className="stat-block" style={{ textAlign: 'left', padding: '28px 32px' }}>
                <p className="label-gold" style={{ marginBottom: '4px', fontSize: '0.62rem' }}>{site.category}</p>
                <h4 style={{ fontFamily: 'var(--font-display)', fontSize: '1.05rem', fontWeight: 600, color: 'var(--ivory-primary)', marginBottom: '6px' }}>
                  {site.name}
                </h4>
                <p className="body-text" style={{ fontSize: '0.8rem', marginBottom: '4px' }}>{site.location}</p>
                <p style={{ fontSize: '0.72rem', color: 'var(--ivory-muted)', fontStyle: 'italic' }}>{site.year}</p>
              </div>
            ))}
          </div>
        </div>

        {/* Technology stack callout */}
        <motion.div
          style={{ y }}
          className="reveal reveal-delay-3"
        >
          <div className="glass-heavy" style={{
            marginTop: '80px',
            padding: '48px',
            display: 'grid',
            gridTemplateColumns: '1fr 1fr',
            gap: '48px',
            alignItems: 'center',
          }}>
            <div>
              <p className="label-gold" style={{ marginBottom: '16px' }}>Technology Architecture</p>
              <div className="gold-line" />
              <h3 className="display-md" style={{ fontSize: '1.8rem', margin: '20px 0 16px' }}>
                Built for Accuracy.<br/>Designed for Discovery.
              </h3>
              <p className="body-text">
                CLIP visual embeddings capture architectural nuance. FAISS enables real-time
                nearest-neighbour search across thousands of monument images. Ollama-powered RAG
                grounds every response in verified catalogue data.
              </p>
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
              {[
                { label: 'Visual Embedding', tech: 'OpenAI CLIP · ViT-L/14' },
                { label: 'Vector Search', tech: 'FAISS · Flat L2 Index' },
                { label: 'Context Generation', tech: 'Ollama RAG · Local LLM' },
                { label: 'Heritage Catalogue', tech: '23 Sites · 1M+ Image Manifest' },
                { label: 'API Layer', tech: 'FastAPI · Python 3.11+' },
              ].map((item, i) => (
                <div key={i} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', paddingBottom: '12px', borderBottom: '1px solid rgba(201,168,76,0.1)' }}>
                  <span className="body-text" style={{ fontSize: '0.85rem' }}>{item.label}</span>
                  <span className="label-gold" style={{ fontSize: '0.65rem' }}>{item.tech}</span>
                </div>
              ))}
            </div>
          </div>
        </motion.div>
      </div>
    </section>
  );
};
