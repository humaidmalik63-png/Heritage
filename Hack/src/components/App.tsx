import { useEffect, useState } from "react";
import { useUIStore } from "@store/ui";
import { useReducedMotion } from "@lib/motion";
import { preloadThree } from "@lib/three";

import LoadingScreen from "@components/LoadingScreen";
import Navigation from "@components/Navigation";
import Hero from "@components/sections/Hero";
import Recognition from "@components/sections/Recognition";
import Heritage from "@components/sections/Heritage";
import Globe from "@components/sections/Globe";
import Preservation from "@components/sections/Preservation";
import Footer from "@components/Footer";
import SkipLink from "@components/SkipLink";

export default function App() {
  const [ready, setReady] = useState(false);
  const reduced = useReducedMotion();
  const { hydrate } = useUIStore();

  useEffect(() => {
    hydrate();
    preloadThree().finally(() => setReady(true));
  }, [hydrate]);

  if (!ready) {
    return (
      <div className="min-h-screen bg-heritage-deep">
        <LoadingScreen />
      </div>
    );
  }

  return (
    <div
      className={`min-h-screen bg-heritage-deep text-ink-primary ${reduced ? "motion-reduce" : ""}`}
      data-reduced-motion={reduced ? "reduce" : "no-preference"}
    >
      <SkipLink />
      <Navigation />
      <main id="main">
        <Hero />
        <Recognition />
        <Heritage />
        <Globe />
        <Preservation />
      </main>
      <Footer />
    </div>
  );
}