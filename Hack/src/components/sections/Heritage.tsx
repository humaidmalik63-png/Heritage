"use client";

import { useRef } from "react";
import { motion, useScroll, useTransform } from "framer-motion";
import Reveal from "@components/Reveal";
import HeritageCard from "@components/cards/HeritageCard";

const sites = [
  {
    id: "taj-mahal",
    name: "Taj Mahal",
    location: "Agra, India",
    year: "1632",
    image: "/assets/covers/taj-mahal.jpg",
    description: "An ivory-white marble mausoleum commissioned by Emperor Shah Jahan in memory of his wife Mumtaz Mahal. A masterpiece of Islamic architecture and UNESCO World Heritage site."
  },
  {
    id: "colosseum",
    name: "Colosseum",
    location: "Rome, Italy",
    year: "70 AD",
    image: "/assets/covers/colosseum.jpg",
    description: "The largest ancient amphitheatre ever built, capable of seating 50,000–80,000 spectators. An enduring symbol of Roman engineering and entertainment culture."
  },
  {
    id: "machu-picchu",
    name: "Machu Picchu",
    location: "Cusco, Peru",
    year: "1450",
    image: "/assets/covers/machu-picchu.jpg",
    description: "A 15th-century Incan citadel set high in the Andes Mountains, a masterpiece of urban planning, astronomy, and stone masonry."
  },
  {
    id: "great-wall",
    name: "Great Wall",
    location: "China",
    year: "7th century BC",
    image: "/assets/covers/great-wall.jpg",
    description: "A series of fortifications stretching over 13,000 miles, built to protect against invasions. The longest and most ambitious military structure in history."
  },
  {
    id: "petra",
    name: "Petra",
    location: "Ma'an, Jordan",
    year: "312 BC",
    image: "/assets/covers/petra.jpg",
    description: "A rocky city carved directly into red sandstone cliffs, capital of the Nabataean Kingdom. An archaeological wonder of the ancient world."
  },
  {
    id: "angkor-wat",
    name: "Angkor Wat",
    location: "Siem Reap, Cambodia",
    year: "1150",
    image: "/assets/covers/angkor-wat.jpg",
    description: "The largest religious monument in the world, originally built as a Hindu temple dedicated to Vishnu. A masterpiece of Khmer architecture."
  },
];

export default function Heritage() {
  const sectionRef = useRef<HTMLElement>(null);
  const { scrollYProgress } = useScroll({
    target: sectionRef,
    offset: ["start end", "end start"]
  });

  const cardsOpacity = useTransform(
    scrollYProgress,
    [0, 1],
    [1, 0]
  );

  const cardsY = useTransform(
    scrollYProgress,
    [0, 1],
    [0, 100]
  );

  const titleScale = useTransform(
    scrollYProgress,
    [0, 1],
    [1, 1.3]
  );

  const titleY = useTransform(
    scrollYProgress,
    [0, 1],
    [0, -20]
  );

  return (
    <section
      id="heritage"
      ref={sectionRef}
      className="py-[var(--section)] bg-heritage-surface/30"
    >
      <div className="section-shell">
        <Reveal>
          <motion.div
            style={{
              transform: `translateY(${titleY as unknown as number}px) scale(${titleScale as unknown as number})`
            }}
          >
            <span className="font-display text-xs uppercase tracking-[0.3em] text-accent-gold">Experience Heritage</span>
            <h2 className="section-title mt-3 text-display-md">
              Timeless monuments that endure
            </h2>
            <p className="section-subtitle mt-6">
              Each site tells a story of human achievement, architectural brilliance, and cultural significance — from ancient wonders to living testaments of our shared heritage.
            </p>
          </motion.div>
        </Reveal>

        <div className="mt-16 relative">
          <motion.div
            className="absolute inset-0 bg-gradient-to-t from-heritage-surface/0 via-heritage-surface/50 to-heritage-surface pointer-events-none -z-10"
            style={{ opacity: 1 - scrollYProgress.get() }}
          />

          <div
            className="grid sm:grid-cols-2 lg:grid-cols-3 gap-8"
            style={{
              opacity: cardsOpacity as unknown as number,
              transform: `translateY(${cardsY as unknown as number}px)`
            }}
          >
            {sites.map((site, i) => (
              <Reveal key={site.id} delay={i * 0.06}>
                <HeritageCard site={site} />
              </Reveal>
            ))}
          </div>
        </div>

        {/* Decorative elements */}
        <div className="absolute top-0 right-0 w-96 h-96 bg-accent-gold/10 rounded-full blur-3xl -z-20" />
        <div className="absolute bottom-0 left-0 w-80 h-80 bg-accent-metallic/10 rounded-full blur-3xl -z-20" />
      </div>
    </section>
  );
}