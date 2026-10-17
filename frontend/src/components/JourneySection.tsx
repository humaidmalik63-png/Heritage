import React, { useEffect, useRef } from 'react';
import { motion, useScroll, useTransform } from 'framer-motion';

const timelineData = [
  {
    year: '2nd c. BCE',
    title: 'Ancient Foundations',
    text: 'Buddhist monks carve the first sanctuaries at Ajanta into the living rock of the Western Ghats, beginning a tradition that would define Indian sacred art for centuries.',
  },
  {
    year: '12th century',
    title: 'The Delhi Sultanate',
    text: 'Qutb ud-Din Aibak raises the Qutb Minar in Delhi — a 72-metre sandstone declaration of a new cultural order, blending Persian calligraphy with local craftsmanship.',
  },
  {
    year: '17th century',
    title: 'Mughal Zenith',
    text: 'Emperor Shah Jahan commissions the Taj Mahal as an eternal monument to love, combining Persian, Ottoman, and Indian architectural traditions into one sublime whole.',
  },
  {
    year: '13th century',
    title: 'Eastern Ganga Glory',
    text: 'The Konark Sun Temple rises on the Odisha coast — a colossal stone chariot for Surya, its 24 wheels and 7 horses measuring the passage of time with geometric precision.',
  },
];

export const JourneySection: React.FC = () => {
  const sectionRef = useRef<HTMLElement>(null);
  const { scrollYProgress } = useScroll({
    target: sectionRef,
    offset: ['start end', 'end start'],
  });

  const y1 = useTransform(scrollYProgress, [0, 1], [60, -60]);
  const opacity = useTransform(scrollYProgress, [0, 0.1, 0.9, 1], [0, 1, 1, 0]);

  // Reveal on scroll
  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            entry.target.classList.add('visible');
          }
        });
      },
      { threshold: 0.15 }
    );
    const reveals = sectionRef.current?.querySelectorAll('.reveal');
    reveals?.forEach((el) => observer.observe(el));
    return () => observer.disconnect();
  }, []);

  return (
    <section className="section-wrapper" id="journey" ref={sectionRef}
      style={{ background: 'linear-gradient(180deg, var(--bg-void) 0%, var(--bg-deep) 100%)' }}>
      <div className="container">

        {/* Section header */}
        <motion.div style={{ opacity }} className="reveal">
          <div style={{ textAlign: 'center', marginBottom: '80px' }}>
            <p className="label-gold" style={{ marginBottom: '16px' }}>Scene Two</p>
            <div className="gold-line gold-line-center" />
            <h2 className="display-lg" style={{ marginBottom: '24px' }}>
              Journey Through Time
            </h2>
            <p className="editorial" style={{ maxWidth: '600px', margin: '0 auto' }}>
              Five thousand years of civilisation, compressed into stones, pigments, and shadow.
              Each monument a chapter; each carving a sentence in an ancient conversation.
            </p>
          </div>
        </motion.div>

        {/* Stats row */}
        <div className="stats-row reveal reveal-delay-2">
          {[
            { number: '3,693', label: 'ASI-Protected Sites' },
            { number: '42', label: 'UNESCO World Heritage' },
            { number: '5,000+', label: 'Years of History' },
            { number: '28+', label: 'Monument Categories' },
          ].map((stat, i) => (
            <div className="stat-block" key={i}>
              <div className="stat-number">{stat.number}</div>
              <div className="stat-label">{stat.label}</div>
            </div>
          ))}
        </div>

        {/* Timeline */}
        <div style={{ position: 'relative', marginTop: '120px' }}>
          <div style={{
            position: 'absolute',
            left: '50%',
            top: 0,
            bottom: 0,
            width: '1px',
            background: 'linear-gradient(to bottom, transparent, rgba(201,168,76,0.3) 20%, rgba(201,168,76,0.3) 80%, transparent)',
            transform: 'translateX(-50%)',
          }} />

          {timelineData.map((item, i) => (
            <div
              key={i}
              className={`reveal reveal-delay-${i + 1}`}
              style={{
                display: 'grid',
                gridTemplateColumns: '1fr 80px 1fr',
                alignItems: 'start',
                marginBottom: '80px',
                gap: 0,
              }}
            >
              {/* Left or right content */}
              {i % 2 === 0 ? (
                <>
                  <div style={{ textAlign: 'right', paddingRight: '48px' }}>
                    <div className="label-gold" style={{ marginBottom: '8px' }}>{item.year}</div>
                    <h3 className="display-md" style={{ fontSize: '1.8rem', marginBottom: '12px' }}>{item.title}</h3>
                    <p className="body-text" style={{ maxWidth: '360px', marginLeft: 'auto' }}>{item.text}</p>
                  </div>
                  <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', paddingTop: '8px' }}>
                    <div style={{
                      width: '12px',
                      height: '12px',
                      borderRadius: '50%',
                      background: 'var(--gold-bright)',
                      border: '2px solid var(--bg-void)',
                      boxShadow: '0 0 20px rgba(201,168,76,0.6)',
                    }} />
                  </div>
                  <div />
                </>
              ) : (
                <>
                  <div />
                  <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', paddingTop: '8px' }}>
                    <div style={{
                      width: '12px',
                      height: '12px',
                      borderRadius: '50%',
                      background: 'var(--gold-bright)',
                      border: '2px solid var(--bg-void)',
                      boxShadow: '0 0 20px rgba(201,168,76,0.6)',
                    }} />
                  </div>
                  <div style={{ paddingLeft: '48px' }}>
                    <div className="label-gold" style={{ marginBottom: '8px' }}>{item.year}</div>
                    <h3 className="display-md" style={{ fontSize: '1.8rem', marginBottom: '12px' }}>{item.title}</h3>
                    <p className="body-text" style={{ maxWidth: '360px' }}>{item.text}</p>
                  </div>
                </>
              )}
            </div>
          ))}
        </div>

        {/* Atmospheric pull quote */}
        <motion.div
          style={{ y: y1, opacity }}
          className="reveal reveal-delay-4"
        >
          <div style={{
            textAlign: 'center',
            padding: '80px 40px',
            borderTop: '1px solid rgba(201,168,76,0.15)',
            borderBottom: '1px solid rgba(201,168,76,0.15)',
            marginTop: '80px',
          }}>
            <p style={{
              fontFamily: 'var(--font-editorial)',
              fontSize: 'clamp(1.5rem, 3vw, 2.5rem)',
              fontStyle: 'italic',
              color: 'var(--ivory-secondary)',
              lineHeight: 1.4,
              maxWidth: '800px',
              margin: '0 auto',
            }}>
              "In stone, in pigment, in the careful measurement of shadow —
              ancient builders encoded everything they understood about the cosmos."
            </p>
            <div className="gold-line gold-line-center" style={{ marginTop: '32px', width: '40px' }} />
          </div>
        </motion.div>
      </div>
    </section>
  );
};
