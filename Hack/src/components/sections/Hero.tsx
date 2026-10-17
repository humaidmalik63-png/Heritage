"use client";

import { useEffect, useState, useRef } from "react";
import { motion, AnimatePresence, useScroll, useTransform, useSpring } from "framer-motion";
import Reveal from "@components/Reveal";
import HeroScene from "@components/3d/HeroScene";
import { useUIStore } from "@store/ui";

export default function Hero() {
  const [scrollProgress, setScrollProgress] = useState(0);
  const [mousePosition, setMousePosition] = useState({ x: 0, y: 0 });
  const heroRef = useRef<HTMLDivElement>(null);
  const { setLoadingComplete } = useUIStore();

  const { scrollYProgress } = useScroll({
    target: heroRef,
    offset: ["start start", "end start"]
  });

  // Track scroll progress for section reveals
  useEffect(() => {
    const unsubscribe = scrollYProgress.on("change", (latest: number) => {
      setScrollProgress(Math.max(0, Math.min(1, latest)));
    });
    return unsubscribe;
  }, [scrollYProgress]);

  // Mouse move parallax for 3D depth
  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      const heroElement = heroRef.current;
      if (!heroElement) return;
      const rect = heroElement.getBoundingClientRect();
      const x = (e.clientX - rect.left) / rect.width - 0.5;
      const y = (e.clientY - rect.top) / rect.height - 0.5;
      setMousePosition({ x, y });
    };
    window.addEventListener("mousemove", handleMouseMove);
    return () => window.removeEventListener("mousemove", handleMouseMove);
  }, []);

  // Simulate loading completion
  useEffect(() => {
    const timer = setTimeout(() => setLoadingComplete(true), 2500);
    return () => clearTimeout(timer);
  }, [setLoadingComplete]);

  // Calculate dynamic styles based on scroll and mouse position
  const titleX = useTransform(useSpring(scrollProgress, { stiffness: 120, damping: 20 }), [0, 1], [0, 60]);
  const titleOpacity = useSpring(scrollProgress * 2, { stiffness: 120, damping: 20 });
  const subtitleOpacity = useSpring(scrollProgress * 1.5, { stiffness: 120, damping: 20 });
  const ctaScale = useSpring(1 - scrollProgress * 0.8, { stiffness: 100, damping: 15 });

  return (
    <section
      id="home"
      ref={heroRef}
      className="relative min-h-screen flex items-center overflow-hidden"
    >
      {/* 3D Scene with mouse-interactive parallax */}
      <div
        className="absolute inset-0"
        style={{
          transform: `perspective(1000px) rotateX(${mousePosition.y * -5}deg) rotateY(${mousePosition.x * 10}deg)`
        }}
      >
        <HeroScene />
      </div>

      {/* Cinematic overlay gradients */}
      <div className="absolute inset-0 bg-gradient-to-b from-heritage-deep via-heritage-deep/80 to-heritage-surface pointer-events-none" />
      <div className="absolute inset-0 bg-gradient-to-t from-accent-gold/20 via-transparent to-transparent pointer-events-none" />

      {/* Content container with scroll-triggered animations */}
      <div
        className="relative z-10 section-shell w-full pt-[var(--nav-height)] pb-20"
        style={{
          opacity: titleOpacity as unknown as number,
          transform: `translateX(${titleX as unknown as number}px)`
        }}
      >
        <div className="max-w-3xl">
          <Reveal delay={0.1}>
            <span
              className="inline-flex items-center gap-3 font-display text-sm uppercase tracking-[0.4em] text-accent-gold mb-6"
              style={{
                textShadow: "0 0 20px rgba(212, 180, 131, 0.5)"
              }}
            >
              <motion.span
                className="w-8 h-px bg-accent-gold"
                initial={{ scaleX: 0 }}
                animate={{ scaleX: 1 }}
                transition={{ duration: 0.8, delay: 0.3 }}
              />
              Visual AI for heritage
              <motion.span
                className="w-8 h-px bg-accent-gold"
                initial={{ scaleX: 0 }}
                animate={{ scaleX: 1 }}
                transition={{ duration: 0.8, delay: 0.5 }}
              />
            </span>
          </Reveal>

          <Reveal delay={0.25} y={48}>
            <h1
              className="font-editorial text-display-xl text-ink-primary leading-none mb-6"
              style={{
                textShadow: "2px 2px 8px rgba(0, 0, 0, 0.8)"
              }}
            >
              <motion.span
                initial={{ opacity: 0, x: -30 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ duration: 0.8, delay: 0.6 }}
                className="inline-block"
              >
                Recognise the
              </motion.span>
              <br />
              <motion.span
                initial={{ opacity: 0, x: -30 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ duration: 0.8, delay: 0.7 }}
                className="inline-block font-garamond italic text-accent-gold"
                style={{
                  textShadow: "0 0 30px rgba(212, 180, 131, 0.8)"
                }}
              >
                stories of place.
              </motion.span>
            </h1>
          </Reveal>

          <Reveal delay={0.45} y={36}>
            <motion.p
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ duration: 1, delay: 0.9 }}
              className="section-subtitle mt-10 max-w-2xl text-lg leading-relaxed text-ink-secondary"
            >
              Point your camera at a monument and let the timeless wisdom emerge from the fusion of ancient architecture and modern AI intelligence. Each frame becomes a portal to history, geometry, and narrative — bridging millennia through pixels.
            </motion.p>
          </Reveal>

          <Reveal delay={0.6} y={24}>
            <motion.div
              style={{ scale: ctaScale }}
              whileHover={{ scale: 1.05, y: -5 }}
              whileTap={{ scale: 0.95 }}
              transition={{ duration: 0.3, ease: [0.22, 1, 0.36, 1] }}
              className="mt-16 flex flex-col sm:flex-row gap-6"
            >
              <a
                href="#recognition"
                className="btn-primary relative overflow-hidden group"
              >
                <span className="relative z-10">Identify a site</span>
                <motion.div
                  className="absolute inset-0 bg-gradient-to-r from-accent-warm to-accent-gold"
                  initial={{ x: "-100%" }}
                  whileHover={{ x: "100%" }}
                  transition={{ duration: 0.6, ease: "easeInOut" }}
                />
              </a>
              <a
                href="#heritage"
                className="btn-ghost relative overflow-hidden group"
              >
                <span className="relative z-10">Explore the catalogue</span>
                <motion.div
                  className="absolute inset-0 bg-accent-gold/20"
                  initial={{ x: "100%" }}
                  whileHover={{ x: "0%" }}
                  transition={{ duration: 0.6, ease: "easeInOut" }}
                />
              </a>
            </motion.div>
          </Reveal>

          {/* Cinematic scroll indicator */}
          <motion.div
            initial={{ opacity: 1 }}
            animate={{ opacity: scrollProgress > 0.8 ? 0 : 1 }}
            transition={{ duration: 0.5 }}
            className="absolute bottom-12 left-1/2 -translate-x-1/2 flex flex-col items-center gap-3 text-ink-muted"
          >
            <span className="font-display text-xs uppercase tracking-widest">Scroll to begin</span>
            <motion.div
              className="w-px h-24 bg-gradient-to-b from-accent-gold to-transparent"
              initial={{ height: "96px" }}
              animate={{ height: scrollProgress > 0.8 ? 0 : "96px" }}
              transition={{ duration: 0.8, ease: "easeInOut" }}
            />
          </motion.div>
        </div>
      </div>
    </section>
  );
}