import { useCallback } from 'react';
import './index.css';

import { Navigation } from './components/Navigation';
import { HeroSection } from './components/HeroSection';
import { JourneySection } from './components/JourneySection';
import { MonumentsSection } from './components/MonumentsSection';
import { RecognitionSection } from './components/RecognitionSection';
import { DiscoverySection } from './components/DiscoverySection';
import { CtaSection, Footer } from './components/CtaSection';

function App() {
  const handleNavigate = useCallback((_section: string) => {
    // Navigation is handled by the scrollTo inside Navigation component
  }, []);

  return (
    <>
      <Navigation onNavigate={handleNavigate} />
      <main>
        <HeroSection />
        <JourneySection />
        <MonumentsSection />
        <RecognitionSection />
        <DiscoverySection />
        <CtaSection />
      </main>
      <Footer />
    </>
  );
}

export default App;
