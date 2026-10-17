import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { useUIStore } from "@store/ui";

export default function LoadingScreen() {
  const [progress, setProgress] = useState(0);
  const [phase, setPhase] = useState<"birds" | "fog" | "ready">("birds");
  const { setLoadingComplete } = useUIStore();

  useEffect(() => {
    const timer = setInterval(() => {
      setProgress((p) => Math.min(100, p + Math.random() * 12 + 4));
    }, 220);

    const phaseTimer = setTimeout(() => setPhase("fog"), 700);
    const doneTimer = setTimeout(() => {
      setLoadingComplete(true);
      clearInterval(timer);
    }, 2600);

    return () => {
      clearInterval(timer);
      clearTimeout(phaseTimer);
      clearTimeout(doneTimer);
    };
  }, [setLoadingComplete]);

  return (
    <motion.div
      className="fixed inset-0 z-[100] flex flex-col items-center justify-center bg-heritage-deep overflow-hidden"
      exit={{ opacity: 0 }}
      transition={{ duration: 1.2, ease: [0.22, 1, 0.36, 1] }}
    >
      <div className="absolute inset-0 bg-gradient-to-b from-heritage-deep via-heritage-surface to-heritage-deep" />

      <div className="relative z-10 text-center">
        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 1, ease: [0.22, 1, 0.36, 1] }}
          className="mb-10"
        >
          <svg
            viewBox="0 0 24 24"
            width="56"
            height="56"
            fill="none"
            stroke="currentColor"
            strokeWidth="1.2"
            className="text-accent-gold mx-auto"
          >
            <motion.path
              d="M3 20h18M5 20V10l7-5 7 5v10M10 20v-6h4v6"
              initial={{ pathLength: 0 }}
              animate={{ pathLength: 1 }}
              transition={{ duration: 1.6, ease: "easeIn" }}
            />
          </svg>
        </motion.div>

        <motion.p
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4, duration: 0.8 }}
          className="font-editorial text-2xl md:text-3xl text-ink-primary tracking-wide"
        >
          Heritage
        </motion.p>
        <motion.p
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.7, duration: 0.8 }}
          className="font-display text-xs uppercase tracking-[0.4em] text-ink-secondary mt-2"
        >
          Discovery
        </motion.p>

        <div className="mt-10 w-48 mx-auto">
          <div className="h-px bg-line overflow-hidden rounded-full">
            <motion.div
              className="h-full bg-gradient-to-r from-accent-gold to-accent-warm"
              style={{ width: `${progress}%` }}
              transition={{ duration: 0.2 }}
            />
          </div>
          <p className="mt-3 font-display text-[11px] uppercase tracking-widest text-ink-muted">
            {phase === "birds" ? "Awakening the sky" : "Parting the fog"}
          </p>
        </div>
      </div>
    </motion.div>
  );
}