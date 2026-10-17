import React, { useEffect, useRef } from 'react';

// Monument data with paths to actual raw images served from the backend's static folder
// The Vite dev server serves /assets from the public folder, so we use relative paths
// The actual images are in ../../data/raw/<id>/ — we'll link them via backend proxy or copy
// For the frontend build, we use absolute URL paths that the backend serves, or fallback to
// Unsplash for dev (replaced with actual images in production by file copy)

interface Monument {
  id: string;
  name: string;
  location: string;
  state: string;
  period: string;
  category: string;
  description: string;
  imageSrc: string;
  imageAlt: string;
  number: string;
  reversed: boolean;
}

const monuments: Monument[] = [
  {
    id: 'taj_mahal',
    name: 'Taj Mahal',
    location: 'Agra',
    state: 'Uttar Pradesh',
    period: 'Mughal Empire · 1632–1653',
    category: 'Mausoleum',
    description: 'Commissioned by Emperor Shah Jahan as an eternal testament to love, the Taj Mahal stands as the supreme expression of Mughal architecture — 20,000 artisans working in white Makrana marble, inlaid with 28 varieties of precious stone.',
    imageSrc: '/monuments/taj_mahal_01.jpg',
    imageAlt: 'Taj Mahal reflected in the Hauz-i-Kausar pool',
    number: '01',
    reversed: false,
  },
  {
    id: 'qutub_minar',
    name: 'Qutb Minar',
    location: 'Delhi',
    state: 'Delhi',
    period: 'Delhi Sultanate · 1193',
    category: 'Minaret',
    description: 'At 72.5 metres, the Qutb Minar is the tallest brick minaret in the world. Constructed in red sandstone with intricate Arabic calligraphy, its five tapering storeys announced a new era of Islamic architecture in the subcontinent.',
    imageSrc: '/monuments/qutub_minar_01.jpg',
    imageAlt: 'Qutb Minar rising against the Delhi sky',
    number: '02',
    reversed: true,
  },
  {
    id: 'red_fort',
    name: 'Red Fort',
    location: 'Old Delhi',
    state: 'Delhi',
    period: 'Mughal Empire · 1639–1648',
    category: 'Imperial Fort',
    description: "Shah Jahan's red sandstone citadel served as the Mughal seat of power for nearly two centuries. From its ramparts, India's Prime Minister raises the national flag every Independence Day — a tradition unbroken since 1947.",
    imageSrc: '/monuments/red_fort_01.jpg',
    imageAlt: "Red Fort's Lahori Gate at dusk",
    number: '03',
    reversed: false,
  },
  {
    id: 'ajanta_caves',
    name: 'Ajanta Caves',
    location: 'Aurangabad',
    state: 'Maharashtra',
    period: '2nd c. BCE – 6th c. CE',
    category: 'Rock-Cut Caves',
    description: 'Thirty Buddhist cave monasteries cut into a horseshoe gorge, their walls covered in the finest narrative paintings ever produced in ancient India. Forgotten for thirteen centuries, rediscovered in 1819 by a British cavalry officer on a tiger hunt.',
    imageSrc: '/monuments/ajanta_caves_01.jpg',
    imageAlt: 'Interior of Ajanta Cave 1 with Bodhisattva Padmapani',
    number: '04',
    reversed: true,
  },
  {
    id: 'konark_sun_temple',
    name: 'Konark Sun Temple',
    location: 'Konark',
    state: 'Odisha',
    period: 'Eastern Ganga Dynasty · 1250',
    category: 'Temple',
    description: 'Conceived as a colossal stone chariot for the sun god Surya, the Konark temple features 24 intricately carved wheels — solar calendars accurate to the minute — and seven horses straining across the cosmos. Mariners once called it the Black Pagoda.',
    imageSrc: '/monuments/konark_sun_temple_01.jpg',
    imageAlt: 'The great wheel of the Konark Sun Temple',
    number: '05',
    reversed: false,
  },
];

interface MonumentCardProps {
  monument: Monument;
  index: number;
}

const MonumentCard: React.FC<MonumentCardProps> = ({ monument, index }) => {
  const cardRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            entry.target.classList.add('visible');
          }
        });
      },
      { threshold: 0.2 }
    );
    const reveals = cardRef.current?.querySelectorAll('.reveal');
    reveals?.forEach((el) => observer.observe(el));
    return () => observer.disconnect();
  }, []);

  return (
    <div
      ref={cardRef}
      className={`monument-scene${monument.reversed ? ' reverse' : ''}`}
      style={{
        borderTop: index > 0 ? '1px solid rgba(201,168,76,0.1)' : 'none',
      }}
    >
      {/* Image pane */}
      <div className="monument-image-pane">
        <img
          src={monument.imageSrc}
          alt={monument.imageAlt}
          loading="lazy"
          onError={(e) => {
            // Fallback if local image not found
            (e.target as HTMLImageElement).style.display = 'none';
            (e.target as HTMLImageElement).parentElement!.style.background =
              'linear-gradient(135deg, #1c1916 0%, #141210 100%)';
          }}
        />
        <div className="monument-image-overlay" />
      </div>

      {/* Content pane */}
      <div className="monument-content-pane">
        <div className="monument-number reveal">{monument.number}</div>

        <div className="monument-location reveal">
          <div className="monument-location-dot" />
          <span className="label-gold">{monument.location}, {monument.state}</span>
        </div>

        <div className="gold-line reveal reveal-delay-1" />

        <h2 className="monument-title reveal reveal-delay-2">{monument.name}</h2>

        <p className="monument-period reveal reveal-delay-2">{monument.period}</p>

        <p className="monument-description reveal reveal-delay-3">{monument.description}</p>

        <div className="monument-badge reveal reveal-delay-4">
          <svg width="12" height="12" viewBox="0 0 12 12" fill="none">
            <circle cx="6" cy="6" r="5" stroke="currentColor" strokeWidth="1"/>
            <path d="M6 3v3l2 1.5" stroke="currentColor" strokeWidth="1" strokeLinecap="round"/>
          </svg>
          UNESCO World Heritage Site
        </div>

        <div className="monument-badge reveal reveal-delay-5" style={{ marginTop: '8px' }}>
          <svg width="12" height="12" viewBox="0 0 12 12" fill="none">
            <path d="M6 1l1.5 3h3l-2.5 2 1 3L6 7.5 3 9l1-3L1.5 4h3L6 1z" stroke="currentColor" strokeWidth="1" fill="none"/>
          </svg>
          {monument.category}
        </div>
      </div>
    </div>
  );
};

export const MonumentsSection: React.FC = () => {
  const sectionRef = useRef<HTMLElement>(null);

  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            entry.target.classList.add('visible');
          }
        });
      },
      { threshold: 0.1 }
    );
    const reveals = sectionRef.current?.querySelectorAll('.section-reveal');
    reveals?.forEach((el) => observer.observe(el));
    return () => observer.disconnect();
  }, []);

  return (
    <section ref={sectionRef} id="monuments">
      {/* Section header */}
      <div className="container" style={{ paddingTop: 'var(--section-pad)', paddingBottom: '80px' }}>
        <div className="section-reveal" style={{
          opacity: 0,
          transform: 'translateY(30px)',
          transition: 'opacity 0.9s ease, transform 0.9s ease',
          textAlign: 'center',
        }}>
          <p className="label-gold" style={{ marginBottom: '16px' }}>Scene Three</p>
          <div className="gold-line gold-line-center" />
          <h2 className="display-lg" style={{ marginBottom: '24px' }}>Five Monuments</h2>
          <p className="editorial" style={{ maxWidth: '560px', margin: '0 auto' }}>
            Each a universe unto itself. Each a conversation between human ambition and geological time.
          </p>
        </div>
      </div>

      {/* Monument scenes */}
      {monuments.map((monument, i) => (
        <MonumentCard key={monument.id} monument={monument} index={i} />
      ))}

      {/* Section close */}
      <div style={{
        padding: '80px 0',
        textAlign: 'center',
        borderTop: '1px solid rgba(201,168,76,0.1)',
        background: 'linear-gradient(to bottom, var(--bg-void), var(--bg-deep))',
      }}>
        <p className="label-gold">23 monuments catalogued · Expanding continuously</p>
      </div>
    </section>
  );
};

// Export monument IDs for use by recognition
export { monuments };
