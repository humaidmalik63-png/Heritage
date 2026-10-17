import { useUIStore } from "@store/ui";

export interface HealthResponse {
  status: "ok" | "degraded";
  service_ready: boolean;
  index_size: number;
  default_top_k: number;
  similarity_threshold: number;
}

export interface RecognizeRequest {
  image_base64: string;
  question?: string;
  top_k?: number;
}

export interface RecognizeResponse {
  confident: boolean;
  site: {
    id: string;
    name: string;
    confidence: number;
    evidence: Array<{
      source: string;
      snippet: string;
      score: number;
    }>;
  } | null;
  answer: string | null;
  error?: string;
}

function baseUrl(): string {
  return useUIStore.getState().apiBaseUrl;
}

export async function checkHealth(): Promise<HealthResponse> {
  const res = await fetch(`${baseUrl()}/health`, { method: "GET" });
  if (!res.ok) throw new Error(`health check failed: ${res.status}`);
  return res.json();
}

export async function recognize(
  imageBase64: string,
  question?: string,
  topK?: number
): Promise<RecognizeResponse> {
  const body: RecognizeRequest = { image_base64: imageBase64 };
  if (question) body.question = question;
  if (topK) body.top_k = topK;

  const res = await fetch(`${baseUrl()}/recognize`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({ error: "unknown", detail: "request failed" }));
    throw new Error(err.detail || err.error || `recognition failed: ${res.status}`);
  }
  return res.json();
}

export function imageToBase64(file: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => {
      const result = reader.result;
      if (typeof result !== "string") return reject(new Error("could not read file"));
      const comma = result.indexOf(",");
      resolve(comma >= 0 ? result.slice(comma + 1) : result);
    };
    reader.onerror = () => reject(reader.error ?? new Error("file reader error"));
    reader.readAsDataURL(file);
  });
}

export function validateImage(file: File): string | null {
  const maxBytes = 10 * 1024 * 1024;
  const allowed = ["image/jpeg", "image/png", "image/webp", "image/heic"];
  if (!allowed.includes(file.type)) {
    return "Please upload a JPG, PNG, WebP or HEIC image.";
  }
  if (file.size > maxBytes) {
    return "Image is too large. Please upload an image under 10 MB.";
  }
  return null;
}