type Event = {
  name: string;
  params?: Record<string, unknown>;
};

const queue: Event[] = [];
let flushed = false;

export const Analytics = {
  init() {
    if (typeof window === "undefined") return;
    if (flushed) return;
    flushed = true;
    window.addEventListener("beforeunload", () => Analytics.flush());
  },
  track(name: string, params?: Record<string, unknown>) {
    queue.push({ name, params });
    if (queue.length >= 10) Analytics.flush();
  },
  flush() {
    if (queue.length === 0) return;
    if (typeof navigator.sendBeacon === "function") {
      const blob = new Blob([JSON.stringify(queue)], { type: "application/json" });
      navigator.sendBeacon("/api/analytics", blob);
    }
    queue.length = 0;
  },
};