"use client";

import { useRef } from "react";
import { motion, useScroll, useTransform } from "framer-motion";
import Reveal from "@components/Reveal";

const principles = [
  {
    title: "Document",
    icon: "📚",
    desc: "Every recognised site is linked to open academic and institutional sources. We verify historical accuracy and cite primary references for transparency."
  },
  {
    title: "Preserve",
    icon: "🛡️",
    desc: "We avoid geolocation noise that could expose fragile or unguarded sites to over-tourism. Preservation includes digital conservation and controlled access."
  },
  {
    title: "Share",
    icon: "🌐",
    desc: "The catalogue grows through verified community contributions. Anyone can submit images or information, subject to peer review."
  },
  {
    title: "Teach",
    icon: "👨‍🏫",
    desc: "Each entry includes interactive timelines, architectural analysis, and cultural context. Educational resources accompany every discovery."
  },
];

const stats = [
  { value: "12", label: "Countries represented", suffix: "", icon: "🌍" },
  { value: "40+", label: "Heritage sites catalogued", suffix: "+", icon: "🏛️" },
  { value: "98%", label: "Mean confidence on benchmark set", suffix: "", icon: "📊" },
  { value: "500+", label: "Research papers referenced", suffix: "+", icon: "📖" },
];

export default function Preservation() {
  const sectionRef = useRef<HTMLElement>(null);
  const { scrollYProgress } = useScroll({
    target: sectionRef,
    offset: ["start end", "end start"]
  });

  const contentOpacity = useTransform(
    scrollYProgress,
    [0, 1],
    [1, 0]
  );

  const contentY = useTransform(
    scrollYProgress,
    [0, 1],
    [0, 60]
  );

  return (
    <section
      id="about"
      ref={sectionRef}
      className="py-[var(--section)] relative overflow-hidden"
    >
      {/* Background effects */}
      <div className="absolute inset-0 bg-gradient-to-b from-heritage-deep via-heritage-surface to-heritage-deep -z-20" />
      <div className="absolute inset-0 bg-gradient-to-t from-accent-gold/5 via-transparent to-transparent -z-20" />

      {/* Decorative elements */}
      <div className="absolute inset-0 -z-10">
        <div className="absolute top-20 left-10 w-72 h-72 bg-accent-gold/10 rounded-full blur-3xl" />
        <div className="absolute bottom-20 right-10 w-96 h-96 bg-accent-metallic/10 rounded-full blur-3xl" />
      </div>

      <div className="section-shell relative z-10">
        <Reveal>
          <span className="font-display text-xs uppercase tracking-[0.3em] text-accent-gold">Our Mission</span>
          <h2 className="section-title mt-3 text-display-md">
            Preserving the past
            <br />
            <span className="text-accent-metallic">for future generations</span>
          </h2>
          <p className="section-subtitle mt-6">
            We believe that understanding our shared heritage strengthens cultural identity and promotes global peace. Through rigorous documentation and accessible technology, we make historical knowledge available to everyone.
          </p>
        </Reveal>

        <div className="mt-16 grid lg:grid-cols-2 gap-8">
          {principles.map((p, i) => (
            <Reveal key={p.title} delay={i * 0.1}>
              <motion.div
                className="group glass p-8 rounded-xl h-full relative overflow-hidden"
                whileHover={{
                  scale: 1.02,
                  y: -8,
                  boxShadow: "0 20px 40px rgba(212, 180, 131, 0.2)"
                }}
                transition={{ duration: 0.4, ease: [0.22, 1, 0.36, 1] }}
              >
                {/* Decorative corner */}
                <div className="absolute top-0 right-0 w-24 h-24 bg-gradient-to-br from-accent-gold/20 to-transparent rounded-bl" />

                <div className="relative z-10">
                  <div className="text-4xl mb-6 flex items-center gap-4">
                    <motion.span
                      className="text-5xl"
                      initial={{ scale: 0.8, opacity: 0 }}
                      whileInView={{ scale: 1, opacity: 1 }}
                      transition={{ delay: i * 0.1 + 0.2, type: "spring", stiffness: 200 }}
                    >
                      {p.icon}
                    </motion.span>
                    <h3 className="font-editorial text-2xl text-ink-primary group-hover:text-accent-gold transition-colors">
                      {p.title}
                    </h3>
                  </div>
                  <motion.p
                    className="text-ink-secondary leading-relaxed text-base"
                    initial={{ opacity: 0 }}
                    whileInView={{ opacity: 1 }}
                    transition={{ delay: i * 0.1 + 0.3, duration: 0.5 }}
                  >
                    {p.desc}
                  </motion.p>
                </div>

                {/* Hover glow effect */}
                <motion.div
                  className="absolute inset-0 bg-gradient-to-r from-accent-gold/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-500"
                  initial={{ opacity: 0 }}
                  whileHover={{ opacity: 1 }}
                />
              </motion.div>
            </Reveal>
          ))}
        </div>

        <div className="mt-20 grid grid-cols-2 md:grid-cols-4 gap-6">
          {stats.map((s, i) => (
            <Reveal key={s.label} delay={i * 0.05}>
              <motion.div
                className="text-center p-6 glass rounded-xl"
                whileHover={{
                  scale: 1.05,
                  backgroundColor: "rgba(212, 180, 131, 0.1)"
                }}
                transition={{ duration: 0.3 }}
              >
                <motion.div
                  className="text-4xl mb-3 flex justify-center"
                  initial={{ scale: 0.5, opacity: 0 }}
                  whileInView={{ scale: 1, opacity: 1 }}
                  transition={{ delay: i * 0.05 + 0.2, type: "spring", stiffness: 150 }}
                >
                  {s.icon}
                </motion.div>
                <motion.div
                  className="font-editorial text-3xl font-bold text-accent-gold mb-2"
                  initial={{ opacity: 0 }}
                  whileInView={{ opacity: 1 }}
                  transition={{ delay: i * 0.05 + 0.3 }}
                >
                  {s.value}
                  <span className="font-sans text-lg ml-1">{s.suffix}</span>
                </motion.div>
                <p className="font-display text-xs text-ink-muted uppercase tracking-wider">
                  {s.label}
                </p>
              </motion.div>
            </Reveal>
          ))}
        </div>
      </div>
    </section>
  );
}