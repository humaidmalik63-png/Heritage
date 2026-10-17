import { create } from "zustand";
import { persist } from "zustand/middleware";

interface UIState {
  menuOpen: boolean;
  loadingComplete: boolean;
  hasSeenOnboarding: boolean;
  reducedMotion: boolean | null;
  apiBaseUrl: string;
  setMenuOpen: (open: boolean) => void;
  setLoadingComplete: (done: boolean) => void;
  setHasSeenOnboarding: (seen: boolean) => void;
  setReducedMotion: (pref: boolean | null) => void;
  hydrate: () => void;
}

export const useUIStore = create<UIState>()(
  persist(
    (set) => ({
      menuOpen: false,
      loadingComplete: false,
      hasSeenOnboarding: false,
      reducedMotion: null,
      apiBaseUrl: import.meta.env.VITE_API_BASE_URL || "/api",
      setMenuOpen: (open) => set({ menuOpen: open }),
      setLoadingComplete: (done) => set({ loadingComplete: done }),
      setHasSeenOnboarding: (seen) => set({ hasSeenOnboarding: seen }),
      setReducedMotion: (pref) => set({ reducedMotion: pref }),
      hydrate: () => {
        if (typeof window === "undefined") return;
        const mq = window.matchMedia("(prefers-reduced-motion: reduce)");
        set({ reducedMotion: mq.matches });
      },
    }),
    {
      name: "heritage-discovery-ui",
      partialize: (state) => ({
        hasSeenOnboarding: state.hasSeenOnboarding,
        reducedMotion: state.reducedMotion,
      }),
    }
  )
);