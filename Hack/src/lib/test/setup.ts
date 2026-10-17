import { vi } from "vitest";

// IntersectionObserver mock
class IntersectionObserverMock implements IntersectionObserver {
  readonly root: Element | null = null;
  readonly rootMargin: string = "0px";
  readonly thresholds: ReadonlyArray<number> = [0];
  observe() {}
  unobserve() {}
  takeRecords(): IntersectionObserverEntry[] {
    return [];
  }
  disconnect() {}
}

globalThis.IntersectionObserver =
  (globalThis as { IntersectionObserver?: typeof IntersectionObserver }).IntersectionObserver ??
  (IntersectionObserverMock as unknown as typeof IntersectionObserver);

// requestAnimationFrame mock
let rafId = 0;
globalThis.requestAnimationFrame = ((cb: FrameRequestCallback) => {
  rafId += 1;
  return setTimeout(() => cb(performance.now()), 0) as unknown as number;
}) as typeof requestAnimationFrame;

globalThis.cancelAnimationFrame = ((id: number) => {
  clearTimeout(id);
}) as typeof cancelAnimationFrame;

// matchMedia mock
Object.defineProperty(window, "matchMedia", {
  writable: true,
  value: vi.fn().mockImplementation((query: string) => ({
    matches: query.includes("reduce") ? false : false,
    media: query,
    addListener: vi.fn(),
    removeListener: vi.fn(),
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    dispatchEvent: vi.fn(),
  })),
});

// ResizeObserver mock
class ResizeObserverMock implements ResizeObserver {
  observe() {}
  unobserve() {}
  disconnect() {}
}

globalThis.ResizeObserver =
  (globalThis as { ResizeObserver?: typeof ResizeObserver }).ResizeObserver ??
  (ResizeObserverMock as unknown as typeof ResizeObserver);

// Scroll methods
globalThis.scrollTo = vi.fn() as typeof scrollTo;
globalThis.scroll = vi.fn() as typeof scroll;