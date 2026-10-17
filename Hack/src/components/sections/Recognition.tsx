"use client";

import { useState, useCallback, useRef } from "react";
import { motion, AnimatePresence, useScroll, useTransform } from "framer-motion";
import { useReducedMotion } from "@lib/motion";
import { recognize, imageToBase64, validateImage, type RecognizeResponse } from "@lib/api";
import Reveal from "@components/Reveal";

export default function Recognition() {
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<string | null>(null);
  const [question, setQuestion] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<RecognizeResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [confidenceScore, setConfidenceScore] = useState<number>(0);
  const reduced = useReducedMotion();

  const sectionRef = useRef<HTMLElement>(null);
  const { scrollYProgress } = useScroll({
    target: sectionRef,
    offset: ["start end", "end start"]
  });

  const panelOpacity = useTransform(
    scrollYProgress,
    [0, 1],
    [1, 0]
  );

  const panelY = useTransform(
    scrollYProgress,
    [0, 1],
    [0, 100]
  );

  const handleFile = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const f = e.target.files?.[0];
    if (!f) return;
    const err = validateImage(f);
    if (err) {
      setError(err);
      return;
    }
    setFile(f);
    imageToBase64(f).then((b64) => setPreview(`data:image/${f.type.split("/")[1]};base64,${b64}`)).catch(() => setError("Could not read image."));
  }, []);

  const handleSubmit = async () => {
    if (!file || !preview) return;
    setLoading(true);
    setResult(null);
    setError(null);
    setConfidenceScore(0);

    // Animate confidence score
    const interval = setInterval(() => {
      setConfidenceScore((prev) => {
        if (prev >= 95) {
          clearInterval(interval);
          return 95;
        }
        return prev + 5;
      });
    }, 100);

    try {
      const base64 = preview.split(",")[1];
      const res = await recognize(base64, question);
      setResult(res);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Recognition failed.");
    } finally {
      setLoading(false);
      clearInterval(interval);
    }
  };

  const handleReset = () => {
    setFile(null);
    setPreview(null);
    setResult(null);
    setError(null);
    setQuestion("");
    setConfidenceScore(0);
  };

  return (
    <section
      id="recognition"
      ref={sectionRef}
      className="relative py-[var(--section)] overflow-hidden"
    >
      {/* Background effects */}
      <div className="absolute inset-0 bg-gradient-to-b from-heritage-surface via-heritage-surface to-heritage-deep -z-20" />
      <div className="absolute inset-0 bg-gradient-to-t from-accent-gold/5 via-transparent to-transparent -z-20" />

      {/* Floating geometric shapes */}
      <div className="absolute inset-0 -z-10">
        <div className="absolute top-20 left-10 w-72 h-72 bg-accent-gold/10 rounded-full blur-3xl" />
        <div className="absolute bottom-20 right-10 w-96 h-96 bg-accent-metallic/10 rounded-full blur-3xl" />
      </div>

      <div
        className="section-shell relative z-10"
        style={{ opacity: panelOpacity as unknown as number, transform: `translateY(${panelY as unknown as number}px)` }}
      >
        <Reveal>
          <span className="font-display text-xs uppercase tracking-[0.3em] text-accent-gold">Artificial Intelligence</span>
          <h2 className="section-title mt-3 text-display-md">
            Recognise. <span className="text-accent-gold">Understand.</span> Connect.
          </h2>
          <p className="section-subtitle mt-6">
            Advanced visual AI identifies heritage sites from photographs, extracting their stories, evidence, and cultural significance. Powered by machine learning and verified by historical scholarship.
          </p>
        </Reveal>

        <div className="mt-12 grid lg:grid-cols-2 gap-8 items-start">
          {/* Upload panel */}
          <Reveal delay={0.1}>
            <motion.div
              className="glass-strong p-6 md:p-8 space-y-6 relative overflow-hidden"
              whileHover={{ scale: 1.02, y: -5 }}
              transition={{ duration: 0.3, ease: [0.22, 1, 0.36, 1] }}
            >
              {/* Decorative corner accent */}
              <div className="absolute top-0 right-0 w-24 h-24 bg-gradient-to-br from-accent-gold/20 to-transparent rounded-bl" />

              <div className="relative border-2 border-dashed border-line hover:border-accent-gold/50 transition-colors duration-300 rounded-xl overflow-hidden min-h-[280px] flex flex-col items-center justify-center bg-heritage-surface/50">
                <input
                  type="file"
                  accept="image/jpeg,image/png,image/webp,image/heic"
                  onChange={handleFile}
                  className="absolute inset-0 w-full h-full opacity-0 cursor-pointer z-10"
                  aria-label="Upload an image of a heritage site"
                />
                <AnimatePresence mode="wait">
                  {preview ? (
                    <motion.img
                      key="preview"
                      src={preview}
                      alt="Uploaded heritage site"
                      initial={{ opacity: 0, scale: 0.95 }}
                      animate={{ opacity: 1, scale: 1 }}
                      exit={{ opacity: 0 }}
                      className="absolute inset-0 w-full h-full object-cover"
                    />
                  ) : (
                    <motion.div
                      key="placeholder"
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      exit={{ opacity: 0 }}
                      className="text-center px-6"
                    >
                      <motion.div
                        animate={{ scale: [1, 1.05, 1] }}
                        transition={{ duration: 2, repeat: Infinity }}
                        className="mb-6 inline-block"
                      >
                        <svg viewBox="0 0 64 64" width="64" height="64" fill="none" stroke="currentColor" strokeWidth="1.5" className="text-accent-gold">
                          <path d="M32 12L12 32h40z" />
                          <path d="M44 20L32 32l-12-12" />
                          <path d="M20 44L44 20" />
                        </svg>
                      </motion.div>
                      <h3 className="font-display text-lg text-ink-primary mb-3">Upload Heritage Image</h3>
                      <p className="font-display text-sm text-ink-secondary mb-2">Drag & drop or click to browse</p>
                      <p className="font-display text-xs text-ink-muted">Supports JPG, PNG, WebP, HEIC — max 10 MB</p>
                    </motion.div>
                  )}
                </AnimatePresence>
              </div>

              <div className="relative">
                <label htmlFor="question" className="block font-display text-xs uppercase tracking-widest text-ink-muted mb-3">
                  Optional research question
                </label>
                <textarea
                  id="question"
                  rows={3}
                  value={question}
                  onChange={(e) => setQuestion(e.target.value)}
                  placeholder="e.g. When was this built? Who designed it? What historical events surround this structure?"
                  className="w-full bg-heritage-elevated/50 border border-line rounded-lg px-5 py-4 text-sm text-ink-primary placeholder:text-ink-muted focus:outline-none focus:ring-2 focus:ring-accent-gold/50 focus:border-transparent resize-none transition-all"
                />
                <div className="absolute bottom-3 right-3 flex gap-1">
                  {['Why?', 'How?', 'What?', 'When?'].map((q) => (
                    <motion.button
                      key={q}
                      type="button"
                      onClick={() => setQuestion(q)}
                      className="w-7 h-7 rounded-full bg-accent-gold/10 hover:bg-accent-gold/20 border border-accent-gold/30 flex items-center justify-center text-xs font-display text-accent-gold"
                      whileHover={{ scale: 1.1 }}
                      whileTap={{ scale: 0.9 }}
                    >
                      {q}
                    </motion.button>
                  ))}
                </div>
              </div>

              <div className="flex gap-4">
                <motion.button
                  type="button"
                  onClick={handleSubmit}
                  disabled={!file || loading}
                  className="btn-primary flex-1 relative overflow-hidden"
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                >
                  <motion.div
                    className="absolute inset-0 bg-gradient-to-r from-accent-warm to-accent-gold"
                    initial={{ x: "-100%" }}
                    whileHover={{ x: "100%" }}
                    transition={{ duration: 0.6 }}
                  />
                  <span className="relative z-10 flex items-center justify-center gap-2">
                    {loading ? (
                      <>
                        <motion.span
                          className="inline-block w-5 h-5 border-2 border-heritage-deep/40 border-t-heritage-deep rounded-full"
                          animate={{ rotate: 360 }}
                          transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
                        />
                        Analysing...
                      </>
                    ) : (
                      <>Identify
                      <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" strokeWidth="2.5">
                        <path d="M5 12h14M13 6l6 6-6 6" />
                      </svg></>
                    )}
                  </span>
                </motion.button>

                {(file || result) && (
                  <motion.button
                    type="button"
                    onClick={handleReset}
                    className="btn-ghost"
                    whileHover={{ scale: 1.05 }}
                    whileTap={{ scale: 0.95 }}
                  >
                    Reset
                  </motion.button>
                )}
              </div>

              {/* Confidence indicator */}
              <AnimatePresence>
                {(loading || confidenceScore > 0) && (
                  <motion.div
                    initial={{ opacity: 0, height: 0 }}
                    animate={{ opacity: 1, height: "auto" }}
                    exit={{ opacity: 0, height: 0 }}
                    className="overflow-hidden"
                  >
                    <div className="bg-heritage-deep/50 rounded-lg p-4 border border-accent-gold/20">
                      <div className="flex items-center justify-between mb-2">
                        <span className="font-display text-sm text-ink-secondary">Analysis confidence</span>
                        <span className="font-display text-sm font-semibold text-accent-gold">
                          {loading ? "Processing..." : `${confidenceScore}%`}
                        </span>
                      </div>
                      <div className="w-full bg-heritage-elevated/50 rounded-full h-2 overflow-hidden">
                        <motion.div
                          className="bg-gradient-to-r from-accent-gold to-accent-warm h-full rounded-full"
                          initial={{ width: "0%" }}
                          animate={{ width: `${Math.min(confidenceScore, 100)}%` }}
                          transition={{ duration: 0.5, ease: "easeOut" }}
                        />
                      </div>
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>

              <AnimatePresence>
                {error && (
                  <motion.p
                    initial={{ opacity: 0, y: -10 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0 }}
                    className="text-sm text-red-400 bg-red-500/10 border border-red-500/30 rounded-lg px-4 py-3 flex items-center gap-3"
                    role="alert"
                  >
                    <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" strokeWidth="2">
                      <circle cx="12" cy="12" r="10" />
                      <line x1="12" y1="8" x2="12" y2="12" />
                      <line x1="12" y1="16" x2="12.01" y2="16" />
                    </svg>
                    {error}
                  </motion.p>
                )}
              </AnimatePresence>
            </motion.div>
          </Reveal>

          {/* Results panel */}
          <Reveal delay={0.2}>
            <AnimatePresence mode="wait">
              {result ? (
                <motion.div
                  key="result"
                  initial={{ opacity: 0, y: 30, scale: 0.95 }}
                  animate={{ opacity: 1, y: 0, scale: 1 }}
                  exit={{ opacity: 0, y: -20, scale: 0.95 }}
                  transition={{ duration: 0.5, ease: [0.22, 1, 0.36, 1] }}
                  className="glass-strong p-6 md:p-8 space-y-6 relative overflow-hidden"
                >
                  {/* Success indicator */}
                  <div className="absolute top-0 right-0 p-3">
                    <motion.div
                      initial={{ scale: 0 }}
                      animate={{ scale: 1 }}
                      transition={{ delay: 0.3, type: "spring", stiffness: 200 }}
                      className="w-12 h-12 rounded-full bg-green-500/20 border border-green-500/30 flex items-center justify-center"
                    >
                      <svg viewBox="0 0 24 24" width="24" height="24" fill="none" stroke="currentColor" strokeWidth="2" className="text-green-400">
                        <path d="M20 6L9 17l-5-5" />
                      </svg>
                    </motion.div>
                  </div>

                  <div className="flex items-start justify-between gap-4 mb-6">
                    <div>
                      <motion.span
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        transition={{ delay: 0.4 }}
                        className={`inline-block text-xs font-display uppercase tracking-widest px-3 py-1.5 rounded-full mb-3 ${
                          result.confident ? "bg-green-500/15 text-green-400 border border-green-500/30" : "bg-yellow-500/15 text-yellow-400 border border-yellow-500/30"
                        }`}
                      >
                        {result.confident ? "Verified Match" : "Low Confidence"}
                      </motion.span>
                      <motion.h3
                        initial={{ opacity: 0, x: -20 }}
                        animate={{ opacity: 1, x: 0 }}
                        transition={{ delay: 0.5, duration: 0.5 }}
                        className="font-editorial text-2xl text-ink-primary leading-tight"
                      >
                        {result.site?.name ?? "Unknown site"}
                      </motion.h3>
                      {result.site?.confidence && (
                        <motion.p
                          initial={{ opacity: 0 }}
                          animate={{ opacity: 1 }}
                          transition={{ delay: 0.6 }}
                          className="text-sm text-ink-muted mt-2 flex items-center gap-2"
                        >
                          <span className="w-2 h-2 rounded-full bg-accent-gold" />
                          Confidence: {Math.round(result.site.confidence * 100)}%
                        </motion.p>
                      )}
                    </div>
                    {result.site?.confidence && (
                      <motion.div
                        initial={{ opacity: 0, scale: 0.8 }}
                        animate={{ opacity: 1, scale: 1 }}
                        transition={{ delay: 0.7, type: "spring", stiffness: 200 }}
                        className="text-right"
                      >
                        <div className="text-4xl font-display font-semibold text-accent-gold">
                          {Math.round(result.site.confidence * 100)}%
                        </div>
                        <p className="text-[10px] uppercase tracking-widest text-ink-muted mt-1">reliability</p>
                      </motion.div>
                    )}
                  </div>

                  {result.site?.evidence && result.site.evidence.length > 0 && (
                    <motion.div
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      transition={{ delay: 0.8, duration: 0.5 }}
                    >
                      <p className="font-display text-xs uppercase tracking-widest text-ink-muted mb-4">Supporting Evidence</p>
                      <div className="space-y-3">
                        {result.site.evidence.map((ev, i) => (
                          <motion.div
                            key={i}
                            initial={{ opacity: 0, x: -20 }}
                            animate={{ opacity: 1, x: 0 }}
                            transition={{ delay: 0.9 + i * 0.1, duration: 0.4 }}
                            className="flex gap-4 p-4 bg-heritage-deep/30 rounded-lg border border-line hover:border-accent-gold/30 transition-colors"
                          >
                            <div className="w-8 h-8 rounded-full bg-accent-gold/20 flex items-center justify-center flex-shrink-0">
                              <span className="text-accent-gold font-display text-sm font-semibold">{i + 1}</span>
                            </div>
                            <div>
                              <p className="text-sm font-medium text-ink-primary mb-1">{ev.source}</p>
                              <p className="text-xs text-ink-secondary leading-relaxed">{ev.snippet}</p>
                              <div className="flex items-center gap-2 mt-2">
                                <div className="w-16 h-1 bg-gradient-to-r from-accent-gold to-transparent rounded-full" style={{ width: `${ev.score * 20}%` }} />
                                <span className="text-[10px] text-ink-muted">Score: {ev.score}/5</span>
                              </div>
                            </div>
                          </motion.div>
                        ))}
                      </div>
                    </motion.div>
                  )}

                  {result.answer && (
                    <motion.div
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      transition={{ delay: 1, duration: 0.5 }}
                      className="pt-6 border-t border-line"
                    >
                      <p className="font-display text-xs uppercase tracking-widest text-ink-muted mb-3">AI Analysis</p>
                      <p className="text-ink-primary leading-relaxed text-sm">{result.answer}</p>
                    </motion.div>
                  )}

                  {!result.confident && !result.error && (
                    <motion.p
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      transition={{ delay: 1 }}
                      className="text-sm text-amber-400 bg-amber-500/10 border border-amber-500/30 rounded-lg p-4 italic"
                    >
                      <strong>Low confidence match.</strong> The system detected similarities but lacks sufficient evidence for a definitive identification. Try uploading a clearer photo or a closer shot of distinctive architectural features.
                    </motion.p>
                  )}
                </motion.div>
              ) : (
                <motion.div
                  key="empty"
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  exit={{ opacity: 0 }}
                  className="h-full min-h-[400px] flex flex-col items-center justify-center text-center border-2 border-dashed border-line rounded-xl bg-heritage-surface/30 p-12 transition-all duration-300 hover:border-accent-gold/30 hover:bg-heritage-surface/50"
                >
                  <motion.div
                    initial={{ scale: 0.8, opacity: 0 }}
                    animate={{ scale: 1, opacity: 1 }}
                    transition={{ delay: 0.2, type: "spring", stiffness: 200 }}
                    className="mb-6 inline-block p-6 rounded-full bg-accent-gold/10"
                  >
                    <svg viewBox="0 0 48 48" width="48" height="48" fill="none" stroke="currentColor" strokeWidth="2" className="text-accent-gold">
                      <rect x="8" y="8" width="32" height="32" rx="4" />
                      <path d="M16 16h16v16H16z" />
                      <path d="M12 12h24v24H12z" strokeWidth="1.5" strokeDasharray="4 4" />
                    </svg>
                  </motion.div>
                  <h3 className="font-editorial text-xl text-ink-primary mb-2">Ready to identify</h3>
                  <p className="font-display text-sm text-ink-muted max-w-md">
                    Upload a heritage site image to begin the analysis. Our AI will recognize the monument, provide confidence scores, and uncover its historical story.
                  </p>
                </motion.div>
              )}
            </AnimatePresence>
          </Reveal>
        </div>
      </div>
    </section>
  );
}