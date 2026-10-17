"use client";

import { useRef, useMemo } from "react";
import { Canvas } from "@react-three/fiber";
import { OrbitControls, Points, Sphere, Float, Environment } from "@react-three/drei";
import * as THREE from "three";
import { useReducedMotion } from "@lib/motion";
import { motion, useScroll, useTransform } from "framer-motion";
import Reveal from "@components/Reveal";

const SITES = [
  { name: "Taj Mahal", lat: 27.1751, lng: 78.0421 },
  { name: "Colosseum", lat: 41.8902, lng: 12.4922 },
  { name: "Machu Picchu", lat: -13.1631, lng: -72.5450 },
  { name: "Great Wall", lat: 40.4319, lng: 116.5704 },
  { name: "Petra", lat: 30.3285, lng: 35.4444 },
  { name: "Angkor Wat", lat: 13.4125, lng: 103.8670 },
  { name: "Pyramids of Giza", lat: 29.9792, lng: 31.1342 },
  { name: "Christ the Redeemer", lat: -22.9519, lng: -43.2105 },
];

function latLngToVec3(lat: number, lng: number, radius: number): THREE.Vector3 {
  const phi = (90 - lat) * (Math.PI / 180);
  const theta = (lng + 180) * (Math.PI / 180);
  return new THREE.Vector3(
    -radius * Math.sin(phi) * Math.cos(theta),
    radius * Math.cos(phi),
    radius * Math.sin(phi) * Math.sin(theta)
  );
}

// Particle system for globe atmosphere
function GlobeParticles() {
  const positions = useMemo(() => {
    return new Float32Array(
      SITES.flatMap((s) => latLngToVec3(s.lat, s.lng, 2.1).toArray())
    );
  }, []);

  return (
    <Points limit={8000} positions={positions}>
      <pointsMaterial
        size={0.06}
        color="#D4B483"
        transparent
        opacity={0.6}
        sizeAttenuation={true}
      />
    </Points>
  );
}

// Animated floating continents
function FloatingContinents() {
  return (
    <group>
      {[1, 2, 3].map((i) => (
        <Float
          key={i}
          speed={0.5 + i * 0.2}
          rotation={[0, Math.PI / 8, 0]}
        >
          <Sphere args={[3, 32, 32]}>
            <meshStandardMaterial
              color="#C4C7CE"
              opacity={0.08 + i * 0.04}
              transparent
              metalness={0.9}
              roughness={0.2}
            />
          </Sphere>
        </Float>
      ))}
    </group>
  );
}

export default function Globe() {
  const reduced = useReducedMotion();
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
    [0, 50]
  );

  return (
    <section
      id="globe"
      ref={sectionRef}
      className="py-[var(--section)] relative overflow-hidden"
    >
      <div className="section-shell relative z-10">
        <div className="grid lg:grid-cols-2 gap-12 items-center">
          <motion.div
            style={{ opacity: contentOpacity, y: contentY }}
            transition={{ duration: 0.8, ease: [0.22, 1, 0.36, 1] }}
          >
            <Reveal>
              <span className="font-display text-xs uppercase tracking-[0.3em] text-accent-gold">Global Legacy</span>
              <h2 className="section-title mt-3 text-display-md">
                Monuments that span
                <br />
                <span className="text-accent-metallic">continents</span>
              </h2>
              <p className="section-subtitle mt-6">
                From the Indus Valley to the Andes, humanity's greatest achievements are scattered across the Earth. The interactive globe reveals their ancient wisdom and geographic beauty.
              </p>
              <div className="mt-8 flex flex-wrap gap-3">
                {SITES.map((site, i) => (
                  <motion.span
                    key={site.name}
                    initial={{ opacity: 0, scale: 0.8 }}
                    whileInView={{ opacity: 1, scale: 1 }}
                    transition={{ delay: i * 0.05, duration: 0.5 }}
                    viewport={{ once: true }}
                    className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-accent-gold/10 border border-accent-gold/30"
                  >
                    <span className="w-2 h-2 rounded-full bg-accent-gold" />
                    <span className="font-display text-xs text-ink-secondary">{site.name}</span>
                  </motion.span>
                ))}
              </div>
            </Reveal>
          </motion.div>

          <Reveal delay={0.15}>
            <div className="aspect-square max-w-md mx-auto lg:mx-0 relative">
              {reduced ? (
                <div className="w-full h-full rounded-full bg-gradient-to-br from-accent-gold/20 via-heritage-elevated to-heritage-deep flex items-center justify-center">
                  <svg viewBox="0 0 100 100" width="200" height="200" fill="none" stroke="currentColor" strokeWidth="0.8" className="text-accent-gold/40">
                    <circle cx="50" cy="50" r="45" />
                    <ellipse cx="50" cy="50" rx="20" ry="45" />
                    <ellipse cx="50" cy="50" rx="45" ry="20" />
                  </svg>
                </div>
              ) : (
                <Canvas
                  camera={{ position: [0, 0, 6], fov: 50 }}
                  dpr={[1, 2]}
                  gl={{ antialias: true, alpha: true }}
                  style={{ background: "transparent" }}
                >
                  <ambientLight intensity={0.8} />
                  <pointLight position={[10, 10, 10]} intensity={1.5} color="#E8D1CB" />
                  <pointLight position={[-10, -5, 5]} intensity={0.8} color="#C4C7CE" />

                  <GlobeParticles />
                  <FloatingContinents />

                  <Environment preset="city" />

                  <OrbitControls
                    enableZoom={false}
                    enablePan={false}
                    autoRotate
                    autoRotateSpeed={0.3}
                    minPolarAngle={Math.PI / 4}
                    maxPolarAngle={Math.PI * 0.85}
                  />

                  <mesh rotation={[0, Math.PI / 6, 0]} scale={2}>
                    <torusKnotGeometry args={[0.8, 0.3, 200, 8]} />
                    <meshStandardMaterial
                      color="#11131A"
                      metalness={0.9}
                      roughness={0.1}
                      emissive="#1A1D27"
                      emissiveIntensity={0.1}
                    />
                  </mesh>
                </Canvas>
              )}
            </div>
          </Reveal>
        </div>
      </div>

      {/* Background decorations */}
      <div className="absolute inset-0 -z-20">
        <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[800px] h-[600px] bg-gradient-radial from-accent-gold/10 via-transparent to-transparent rounded-full" />
        <div className="absolute bottom-0 right-0 w-[600px] h-[800px] bg-gradient-radial from-accent-metallic/10 via-transparent to-transparent rounded-full" />
      </div>
    </section>
  );
}