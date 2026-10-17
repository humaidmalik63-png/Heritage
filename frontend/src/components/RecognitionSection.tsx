import React, { useState, useCallback, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

// ── Types ──────────────────────────────────────────────────────────────────────
interface RecognitionResult {
  site_id: string;
  confident: boolean;
  confirmed: boolean;
  decision: string;
  recognition_source: string;
  metadata: {
    name?: string;
    location?: string;
    state?: string;
    description?: string;
    historical_period?: string;
    category?: string;
    preservation_context?: string;
  };
  evidence: {
    facts?: string[];
    sources?: string[];
    [key: string]: unknown;
  };
  answer?: string;
  citations: string[];
  is_grounded: boolean;
  is_valid: boolean;
  reason?: string;
}

// ── Upload Icon ────────────────────────────────────────────────────────────────
const UploadIcon: React.FC = () => (
  <svg width="28" height="28" viewBox="0 0 28 28" fill="none">
    <path d="M14 20V12M14 12L10 16M14 12L18 16" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
    <path d="M6 20.5C4.3 19.7 3 17.9 3 15.8c0-2.8 2.1-5 4.8-5.2.3-3.4 3.1-6.1 6.6-6.1 3.2 0 5.9 2.2 6.5 5.2 2.4.4 4.1 2.5 4.1 4.9 0 2.1-1.3 3.9-3.1 4.7" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
  </svg>
);

// ── Scan Overlay ───────────────────────────────────────────────────────────────
const ScanOverlay: React.FC = () => (
  <div style={{ position: 'absolute', inset: 0, overflow: 'hidden', borderRadius: '4px', pointerEvents: 'none' }}>
    <div className="scan-animation" />
    {/* Corner brackets */}
    {[
      { top: 0, left: 0, borderTop: '2px solid #c9a84c', borderLeft: '2px solid #c9a84c' },
      { top: 0, right: 0, borderTop: '2px solid #c9a84c', borderRight: '2px solid #c9a84c' },
      { bottom: 0, left: 0, borderBottom: '2px solid #c9a84c', borderLeft: '2px solid #c9a84c' },
      { bottom: 0, right: 0, borderBottom: '2px solid #c9a84c', borderRight: '2px solid #c9a84c' },
    ].map((style, i) => (
      <div key={i} style={{ position: 'absolute', width: '20px', height: '20px', ...style }} />
    ))}
  </div>
);

// ── Result Panel ───────────────────────────────────────────────────────────────
const ResultPanel: React.FC<{ result: RecognitionResult }> = ({ result }) => {
  const meta = result.metadata || {};

  if (!result.confident) {
    return (
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6, ease: [0.22, 1, 0.36, 1] }}
        className="glass-panel"
        style={{ padding: '32px', marginTop: '32px' }}
      >
        <div className="label-gold" style={{ marginBottom: '12px' }}>Recognition Result</div>
        <div className="gold-line" />
        <p className="body-text" style={{ marginTop: '16px' }}>
          {result.reason || 'The image could not be matched to a known monument with sufficient confidence. Please try a clearer or more direct photograph.'}
        </p>
        <p className="label-gold" style={{ marginTop: '16px', color: 'var(--ivory-muted)' }}>
          Decision: {result.decision}
        </p>
      </motion.div>
    );
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 30 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.8, ease: [0.22, 1, 0.36, 1] }}
      style={{ marginTop: '40px' }}
    >
      {/* Identification header */}
      <div className="glass-heavy" style={{ padding: '40px' }}>
        <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', flexWrap: 'wrap', gap: '20px' }}>
          <div>
            <p className="label-gold" style={{ marginBottom: '8px' }}>Heritage Identified</p>
            <div className="gold-line" style={{ marginBottom: '16px' }} />
            <h3 className="display-md" style={{ fontSize: '2rem', marginBottom: '8px' }}>
              {meta.name || result.site_id.replace(/_/g, ' ')}
            </h3>
            {meta.location && (
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
                <div style={{ width: '5px', height: '5px', borderRadius: '50%', background: 'var(--gold-bright)' }} />
                <span className="label-gold">{meta.location}{meta.state ? `, ${meta.state}` : ''}</span>
              </div>
            )}
            {meta.historical_period && (
              <p className="monument-period" style={{ margin: 0 }}>{meta.historical_period}</p>
            )}
          </div>

          {/* Source badge */}
          <div style={{ textAlign: 'right' }}>
            <div className="monument-badge">
              <svg width="12" height="12" viewBox="0 0 12 12" fill="currentColor">
                <circle cx="6" cy="6" r="5.5" fill="none" stroke="currentColor"/>
                <path d="M4 6l1.5 1.5L8 4" stroke="currentColor" strokeWidth="1.2" fill="none" strokeLinecap="round"/>
              </svg>
              {result.recognition_source === 'local' ? 'AI Recognition' :
               result.recognition_source === 'ollama' ? 'AI + Context' : 'Analysed'}
            </div>
          </div>
        </div>

        {/* Description */}
        {meta.description && (
          <p className="body-text" style={{ marginTop: '24px', paddingTop: '24px', borderTop: '1px solid rgba(201,168,76,0.15)' }}>
            {meta.description}
          </p>
        )}

        {/* Preservation context */}
        {meta.preservation_context && (
          <div className="monument-badge" style={{ marginTop: '20px' }}>
            <svg width="12" height="12" viewBox="0 0 12 12" fill="none">
              <path d="M6 1L11 3.5V6C11 9 6 11 6 11C6 11 1 9 1 6V3.5L6 1Z" stroke="currentColor" strokeWidth="1"/>
            </svg>
            {meta.preservation_context}
          </div>
        )}
      </div>

      {/* AI Answer / RAG response */}
      {result.answer && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3, duration: 0.6 }}
          className="glass-panel"
          style={{ padding: '32px', marginTop: '20px' }}
        >
          <p className="label-gold" style={{ marginBottom: '12px' }}>
            {result.is_grounded ? 'Grounded Historical Context' : 'Historical Context'}
          </p>
          <div className="gold-line" />
          <p className="body-text" style={{ marginTop: '16px', lineHeight: 1.9 }}>{result.answer}</p>

          {/* Citations */}
          {result.citations?.length > 0 && (
            <div style={{ marginTop: '20px', paddingTop: '20px', borderTop: '1px solid rgba(201,168,76,0.1)' }}>
              <p className="label-gold" style={{ marginBottom: '8px', color: 'var(--ivory-muted)' }}>Sources</p>
              {result.citations.slice(0, 3).map((cite, i) => (
                <p key={i} className="body-text" style={{ fontSize: '0.8rem', color: 'var(--ivory-muted)', marginBottom: '4px' }}>
                  [{i + 1}] {cite}
                </p>
              ))}
            </div>
          )}
        </motion.div>
      )}

      {/* Evidence facts */}
      {result.evidence?.facts && result.evidence.facts.length > 0 && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.5, duration: 0.6 }}
          style={{ marginTop: '20px' }}
        >
          <p className="label-gold" style={{ marginBottom: '20px' }}>Key Facts</p>
          <div className="evidence-grid">
            {result.evidence.facts.slice(0, 6).map((fact: string, i: number) => (
              <div key={i} className="evidence-card glass-panel">
                <div style={{ color: 'var(--gold-bright)', fontSize: '0.7rem', marginBottom: '8px' }}>◆</div>
                <p className="body-text" style={{ fontSize: '0.88rem' }}>{fact}</p>
              </div>
            ))}
          </div>
        </motion.div>
      )}
    </motion.div>
  );
};

// ── Main Recognition Component ─────────────────────────────────────────────────
export const RecognitionSection: React.FC = () => {
  const [isDragging, setIsDragging] = useState(false);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [isScanning, setIsScanning] = useState(false);
  const [result, setResult] = useState<RecognitionResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [question, setQuestion] = useState('');
  const fileInputRef = useRef<HTMLInputElement>(null);
  const sectionRef = useRef<HTMLElement>(null);

  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) entry.target.classList.add('visible');
        });
      },
      { threshold: 0.15 }
    );
    sectionRef.current?.querySelectorAll('.reveal').forEach((el) => observer.observe(el));
    return () => observer.disconnect();
  }, []);

  const toBase64 = (file: File): Promise<string> =>
    new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = () => resolve(reader.result as string);
      reader.onerror = reject;
      reader.readAsDataURL(file);
    });

  const processFile = useCallback(async (file: File) => {
    if (!file.type.startsWith('image/')) {
      setError('Please upload an image file (JPG, PNG, WebP).');
      return;
    }

    // Preview
    const objectUrl = URL.createObjectURL(file);
    setPreviewUrl(objectUrl);
    setResult(null);
    setError(null);
    setIsScanning(true);

    try {
      const base64 = await toBase64(file);

      const response = await fetch('/recognize', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          image_base64: base64,
          question: question.trim() || undefined,
          top_k: 5,
        }),
      });

      if (!response.ok) {
        const err = await response.json().catch(() => ({ detail: 'Recognition failed.' }));
        throw new Error(err.detail || `Server error ${response.status}`);
      }

      const data: RecognitionResult = await response.json();
      setResult(data);
    } catch (e: unknown) {
      if (e instanceof TypeError && e.message.includes('fetch')) {
        setError('Cannot reach the heritage API. Please ensure the FastAPI backend is running on port 8000.');
      } else {
        setError(e instanceof Error ? e.message : 'Recognition failed. Please try again.');
      }
    } finally {
      setIsScanning(false);
    }
  }, [question]);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    const file = e.dataTransfer.files[0];
    if (file) processFile(file);
  }, [processFile]);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) processFile(file);
  };

  const reset = () => {
    setPreviewUrl(null);
    setResult(null);
    setError(null);
    setIsScanning(false);
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  return (
    <section className="recognition-section" id="recognize" ref={sectionRef}>
      <div className="container">

        {/* Header */}
        <div className="reveal" style={{ textAlign: 'center', marginBottom: '80px' }}>
          <p className="label-gold" style={{ marginBottom: '16px' }}>Scene Four</p>
          <div className="gold-line gold-line-center" />
          <h2 className="display-lg" style={{ marginBottom: '24px' }}>AI Heritage Recognition</h2>
          <p className="editorial" style={{ maxWidth: '600px', margin: '0 auto' }}>
            Upload a photograph of any Indian monument. Our CLIP-based visual intelligence
            will identify it and surface grounded historical context from our curated catalogue.
          </p>
        </div>

        {/* Main interface */}
        <div style={{
          display: 'grid',
          gridTemplateColumns: previewUrl ? '1fr 1fr' : '1fr',
          gap: '40px',
          maxWidth: previewUrl ? '1200px' : '700px',
          margin: '0 auto',
          transition: 'all 0.6s ease',
        }}>

          {/* Upload / Preview pane */}
          <div className="reveal reveal-delay-2">
            {!previewUrl ? (
              <>
                {/* Question input */}
                <div className="glass-panel" style={{ padding: '20px 24px', marginBottom: '16px' }}>
                  <label className="label-gold" style={{ display: 'block', marginBottom: '8px' }}>
                    Ask a question (optional)
                  </label>
                  <input
                    type="text"
                    id="heritage-question-input"
                    value={question}
                    onChange={(e) => setQuestion(e.target.value)}
                    placeholder="e.g. When was this built? Who commissioned it?"
                    style={{
                      width: '100%',
                      background: 'transparent',
                      border: 'none',
                      outline: 'none',
                      color: 'var(--ivory-primary)',
                      fontFamily: 'var(--font-ui)',
                      fontSize: '0.9rem',
                      paddingTop: '4px',
                    }}
                  />
                </div>

                {/* Drop zone */}
                <div
                  className={`upload-zone${isDragging ? ' dragging' : ''}`}
                  id="heritage-upload-zone"
                  onDragOver={(e) => { e.preventDefault(); setIsDragging(true); }}
                  onDragLeave={() => setIsDragging(false)}
                  onDrop={handleDrop}
                  onClick={() => fileInputRef.current?.click()}
                  role="button"
                  tabIndex={0}
                  aria-label="Upload monument image"
                  onKeyDown={(e) => e.key === 'Enter' && fileInputRef.current?.click()}
                >
                  <div className="upload-icon">
                    <UploadIcon />
                  </div>
                  <h3 style={{ fontFamily: 'var(--font-display)', fontSize: '1.3rem', marginBottom: '12px', color: 'var(--ivory-primary)' }}>
                    Drop your image here
                  </h3>
                  <p className="body-text" style={{ fontSize: '0.88rem', marginBottom: '20px' }}>
                    or click to browse · JPG, PNG, WebP · up to 10 MB
                  </p>
                  <div className="btn-ghost" style={{ pointerEvents: 'none', display: 'inline-flex' }}>
                    <span>Select Image</span>
                  </div>
                  <input
                    ref={fileInputRef}
                    type="file"
                    id="heritage-file-input"
                    accept="image/jpeg,image/png,image/webp"
                    style={{ display: 'none' }}
                    onChange={handleFileChange}
                  />
                </div>

                {/* Error */}
                {error && (
                  <motion.div
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    className="glass-panel"
                    style={{ padding: '16px 20px', marginTop: '16px', borderLeft: '2px solid rgba(200,80,60,0.6)' }}
                  >
                    <p className="body-text" style={{ fontSize: '0.88rem', color: '#e88' }}>{error}</p>
                  </motion.div>
                )}
              </>
            ) : (
              /* Image preview with scan animation */
              <div style={{ position: 'relative' }}>
                <div className="glass-panel" style={{ overflow: 'hidden', borderRadius: '4px', position: 'relative' }}>
                  <img
                    src={previewUrl}
                    alt="Uploaded monument"
                    style={{ width: '100%', maxHeight: '480px', objectFit: 'cover', display: 'block' }}
                  />
                  {isScanning && <ScanOverlay />}
                </div>

                {/* Scanning status */}
                <AnimatePresence>
                  {isScanning && (
                    <motion.div
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      exit={{ opacity: 0 }}
                      className="glass-heavy"
                      style={{ padding: '20px 24px', marginTop: '16px', display: 'flex', alignItems: 'center', gap: '16px' }}
                    >
                      <div style={{
                        width: '20px', height: '20px', borderRadius: '50%',
                        border: '2px solid rgba(201,168,76,0.2)',
                        borderTop: '2px solid var(--gold-bright)',
                        animation: 'spin 0.8s linear infinite',
                      }} />
                      <div>
                        <p className="label-gold">Analysing monument</p>
                        <p className="body-text" style={{ fontSize: '0.82rem' }}>CLIP embedding · FAISS retrieval · Evidence grounding</p>
                      </div>
                    </motion.div>
                  )}
                </AnimatePresence>

                {/* Reset button */}
                {!isScanning && (
                  <button className="btn-ghost" onClick={reset} style={{ marginTop: '16px', width: '100%', justifyContent: 'center' }} id="upload-reset-btn">
                    <span>Analyse Another Image</span>
                  </button>
                )}

                {/* Error */}
                {error && !isScanning && (
                  <motion.div
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    className="glass-panel"
                    style={{ padding: '16px 20px', marginTop: '16px', borderLeft: '2px solid rgba(200,80,60,0.6)' }}
                  >
                    <p className="body-text" style={{ fontSize: '0.88rem', color: '#e88' }}>{error}</p>
                  </motion.div>
                )}
              </div>
            )}
          </div>

          {/* Result pane */}
          {result && (
            <div className="reveal">
              <ResultPanel result={result} />
            </div>
          )}
        </div>
      </div>

      <style>{`
        @keyframes spin { to { transform: rotate(360deg); } }
      `}</style>
    </section>
  );
};
