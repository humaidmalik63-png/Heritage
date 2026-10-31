/* ==========================================================================
   Heritage Discovery — application logic
   Vanilla JS. No frameworks, no external runtime dependencies.

   Every value rendered here comes from one of two places:
     1. GET  /health     -> liveness + index size
     2. POST /recognize  -> recognition, metadata, evidence, citations
     3. the local monument catalogue JSON
   Nothing about a monument is ever invented: if the API did not return a
   field, the corresponding block is not rendered.
   ========================================================================== */
(function () {
  'use strict';

  /* ── configuration ────────────────────────────────────────────────────── */

  // ── Phase 2: Seven-Image Cinematic Slideshow Configuration ───────────────
  // Exactly seven heritage images for the continuous background slideshow (New Seven Wonders of the World).
  // Each entry carries its modern WebP asset, mobile-optimized WebP asset, progressive JPEG fallback, site name, and focal framing.
  var SLIDESHOW_CONFIG = [
    { src: 'assets/images/slideshow/great-wall.webp', mobileSrc: 'assets/images/slideshow/great-wall-sm.webp', fallback: 'assets/images/slideshow/great-wall.jpg', position: '50% 50%', mobilePosition: '50% 50%', name: 'Great Wall of China' },
    { src: 'assets/images/slideshow/petra.webp', mobileSrc: 'assets/images/slideshow/petra-sm.webp', fallback: 'assets/images/slideshow/petra.jpg', position: '50% 36%', mobilePosition: '50% 30%', name: 'Petra, Jordan' },
    { src: 'assets/images/slideshow/christ-redeemer.webp', mobileSrc: 'assets/images/slideshow/christ-redeemer-sm.webp', fallback: 'assets/images/slideshow/christ-redeemer.jpg', position: '50% 30%', mobilePosition: '50% 25%', name: 'Christ the Redeemer, Brazil' },
    { src: 'assets/images/slideshow/machu-picchu.webp', mobileSrc: 'assets/images/slideshow/machu-picchu-sm.webp', fallback: 'assets/images/slideshow/machu-picchu.jpg', position: '50% 50%', mobilePosition: '55% 50%', name: 'Machu Picchu, Peru' },
    { src: 'assets/images/slideshow/chichen-itza.webp', mobileSrc: 'assets/images/slideshow/chichen-itza-sm.webp', fallback: 'assets/images/slideshow/chichen-itza.jpg', position: '50% 50%', mobilePosition: '50% 50%', name: 'Chichén Itzá, Mexico' },
    { src: 'assets/images/slideshow/colosseum.webp', mobileSrc: 'assets/images/slideshow/colosseum-sm.webp', fallback: 'assets/images/slideshow/colosseum.jpg', position: '50% 45%', mobilePosition: '50% 40%', name: 'Colosseum, Italy' },
    { src: 'assets/images/slideshow/taj-mahal.webp', mobileSrc: 'assets/images/slideshow/taj-mahal-sm.webp', fallback: 'assets/images/slideshow/taj-mahal.jpg', position: '50% 48%', mobilePosition: '50% 46%', name: 'Taj Mahal, India' }
  ];
  var SLIDESHOW_IMAGES = SLIDESHOW_CONFIG.map(function (item) { return item.src; });
  var SLIDESHOW_INTERVAL_MS = 5000; // 5-second automatic rotation

  function isMobileViewport() {
    return (window.innerWidth && window.innerWidth <= 768) ||
           (window.innerHeight && window.innerHeight > window.innerWidth);
  }

  function getSlideUrl(item) {
    if (!item) return '';
    if (isMobileViewport() && item.mobileSrc) return item.mobileSrc;
    return item.src || item.fallback;
  }

  function getSlidePosition(item) {
    if (!item) return '50% 50%';
    var isMobile = isMobileViewport();
    return (isMobile && item.mobilePosition) ? item.mobilePosition : (item.position || '50% 50%');
  }

  // Controller hook allowing manual cues from chapter controls without timer lock-in
  var slideshowController = {
    cueSlide: function () {},
    getCurrentIndex: function () { return 0; }
  };

  // ── Phase 7: Deliberate Image-to-Chapter Mapping Configuration ────────────
  // Maps 6 storytelling chapters to curated heritage monuments from the 7-image collection.
  // Both timers remain strictly independent (5s background vs 8s narrative chapters).
  var CHAPTER_IMAGE_MAP = [0, 1, 2, 3, 4, 6];

  var cachedHeroHeight = 0;
  function getCachedHeroHeight() {
    if (!cachedHeroHeight) {
      var heroEl = $('#hero');
      if (heroEl) cachedHeroHeight = heroEl.offsetHeight || 800;
    }
    return cachedHeroHeight || 800;
  }
  window.addEventListener('resize', function () {
    var heroEl = $('#hero');
    if (heroEl) cachedHeroHeight = heroEl.offsetHeight || 800;
  }, { passive: true });

  function isExperienceSuspended() {
    if (document.hidden) return true;
    if (current === 'detail') return true;

    // Suspend when hero is scrolled out of view without forced layout reflows
    var scrollY = window.scrollY || window.pageYOffset || 0;
    var heroH = getCachedHeroHeight();
    if (scrollY > heroH * 0.55) {
      return true;
    }

    // Suspend during active upload, preview or while recognition is processing
    var uploadPreview = $('#upload-preview');
    var uploadZone = $('#upload-zone');
    if (uploadPreview && !uploadPreview.hidden) return true;
    if (uploadZone && uploadZone.classList.contains('is-busy')) return true;

    // Suspend when viewing recognition results
    var resultRegion = $('#result-region');
    if (resultRegion && resultRegion.children.length > 0) return true;
    if (typeof busy !== 'undefined' && busy) return true;

    // Suspend when user is typing in form inputs
    var active = document.activeElement;
    if (active && (active.tagName === 'INPUT' || active.tagName === 'TEXTAREA' || active.tagName === 'SELECT')) {
      return true;
    }

    return false;
  }

  function resolveInitialApiBase() {
    try {
      var stored = localStorage.getItem('heritage_api_base');
      if (stored && stored.trim()) {
        var cleanStored = stored.trim().replace(/\/$/, '');
        // On HTTPS pages, do not use dead services (n13o), insecure HTTP, or stale :8000
        if (cleanStored.includes('heritage-n13o') || (location.protocol === 'https:' && (cleanStored.startsWith('http://') || cleanStored.includes(':8000')))) {
          try { localStorage.removeItem('heritage_api_base'); } catch (_) {}
        } else {
          return cleanStored;
        }
      }
    } catch (_) {}

    var attr = (document.documentElement.getAttribute('data-api-base') || '').trim();
    if (attr) return attr.replace(/\/$/, '');

    try {
      if (typeof import.meta !== 'undefined' && import.meta.env && import.meta.env.VITE_API_BASE) {
        var envBase = String(import.meta.env.VITE_API_BASE).trim();
        if (envBase) return envBase.replace(/\/$/, '');
      }
    } catch (_) {}

    if (location.protocol === 'file:') return 'http://localhost:8000';
    if (location.hostname === 'localhost' || location.hostname === '127.0.0.1') {
      return location.protocol + '//' + location.hostname + ':8000';
    }
    // Remote host (e.g. Vercel): default to the user's live Render cloud backend
    return 'https://heritage-1-why4.onrender.com';
  }

  var API_BASE = resolveInitialApiBase();

  function setApiBase(url) {
    API_BASE = (url || '').trim().replace(/\/$/, '');
    try {
      if (API_BASE) {
        localStorage.setItem('heritage_api_base', API_BASE);
      } else {
        localStorage.removeItem('heritage_api_base');
      }
    } catch (_) {}
    refreshHealth();
  }

  // The catalogue lives outside this folder. When the frontend is served from
  // a local HTTP server rooted at the project, the relative path resolves; the
  // bundled copy is the fallback so the prototype also works standalone.
  var CATALOGUE_SOURCES = [
    '../data/metadata/global_monument_catalogue.json',
    'assets/data/global_monument_catalogue.json'
  ];

  // The gallery manifest is generated from the project's real photographs by
  // frontend_new/scripts/prepare_gallery.py.  It lists only files that exist,
  // so a missing photograph simply means a shorter gallery -- never a
  // placeholder.
  var GALLERY_SOURCES = ['assets/data/gallery.json'];
  var MAX_GALLERY = 5;

  // Card images for monuments that have no local photograph.  Written by
  // frontend_new/scripts/fetch_monument_images.py, which downloads one verified
  // Wikimedia Commons image per monument and records its attribution beside it.
  // The manifest only lists files that actually exist, so a missing entry means
  // "no image" -> the architectural placeholder, never a broken <img>.
  var MONUMENT_IMAGE_SOURCES = ['assets/images/monuments/image_manifest.json'];

  var MAX_BYTES = 10 * 1024 * 1024;          // matches backend MAX_IMAGE_BYTES
  var MAX_DATA_URL_CHARS = Math.floor(MAX_BYTES * 0.75); // base64 expansion, kept under the cap
  var MAX_EDGE = 1600;                     // longest edge after downscale
  var ACCEPTED = ['image/jpeg', 'image/jpg', 'image/png', 'image/webp'];
  var PAGE_SIZE = 24;

  var ERROR_MESSAGES = {
    invalid_input: 'That photograph could not be accepted. Try a JPG, PNG or WebP under 10 MB.',
    not_found: 'That photograph could not be read by the service.',
    unprocessable_image: 'That file could not be read as an image. Try a different photograph.',
    internal_error: 'The recognition service could not complete that request.',
    service_not_ready: 'The recognition service is still starting up. Try again in a moment.'
  };

  var REASON_TEXT = {
    low_similarity: 'Image embeddings fell below the open-set verification threshold (similarity < 0.8500 or margin < 0.1000). Not confirmed as an indexed catalogue monument.',
    no_evidence: 'The monument was identified by visual similarity, but no grounded evidence record is stored in the local repository.',
    non_heritage: 'Visual analysis indicated that the subject matter does not represent a recognized cultural heritage monument.',
    answer_declined: 'The grounded architectural response was declined due to insufficient textual evidence support.',
    ungrounded_answer: 'The synthesized response could not be verified against primary evidence records.'
  };

  /* ── tiny helpers ─────────────────────────────────────────────────────── */

  function $(sel, root) { return (root || document).querySelector(sel); }
  function $$(sel, root) { return Array.prototype.slice.call((root || document).querySelectorAll(sel)); }

  function el(tag, className, text) {
    var node = document.createElement(tag);
    if (className) node.className = className;
    if (text != null) node.textContent = text;
    return node;
  }

  /* Build a label/value row only when the value actually exists. */
  function field(label, value, className) {
    if (value === null || value === undefined) return null;
    var text = String(value).trim();
    if (!text) return null;
    var wrap = el('div', 'field ' + (className || ''));
    wrap.appendChild(el('span', 'field__label', label));
    wrap.appendChild(el('span', 'field__text', text));
    return wrap;
  }

  function pct(v) {
    if (typeof v !== 'number' || !isFinite(v)) return '—';
    return v.toFixed(4);
  }

  /* Render the confidence score if present.
     Under no circumstances is 100% ever rendered, as empirical models never achieve
     absolute certainty. Calibrated probabilities are only used when backed by empirical
     validation data; otherwise raw similarity and competitor margins are preferred.

     One decimal at most, with a bare trailing ".0" dropped -- 0.923 reads as
     92.3%, 0.684 as 68.4%, 0.41 as 41%. */
  function formatConfidence(value) {
    if (typeof value !== 'number' || !isFinite(value)) return null;
    var pctValue = value * 100;
    if (pctValue >= 99.95) return '99.9%';
    if (pctValue <= 0) return '0%';
    return (Math.round(pctValue * 10) / 10).toFixed(1).replace(/\.0$/, '') + '%';
  }

  /* The single CONFIDENCE cell for a result.  Uses the numeric value when the
     backend supplied one, otherwise the qualitative status it supplied, and
     otherwise nothing at all. */
  function confidenceMetric(numeric, statusText) {
    var text = formatConfidence(numeric);
    if (!text && statusText) text = String(statusText);
    return text;
  }

  function bytes(n) {
    if (n < 1024) return n + ' B';
    if (n < 1024 * 1024) return (n / 1024).toFixed(1) + ' KB';
    return (n / (1024 * 1024)).toFixed(1) + ' MB';
  }

  function reducedMotion() {
    return window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  }

  function coarsePointer() {
    return window.matchMedia && window.matchMedia('(hover: none), (pointer: coarse)').matches;
  }

  function debounce(fn, wait) {
    var timer;
    return function () {
      var context = this, args = arguments;
      clearTimeout(timer);
      timer = setTimeout(function () {
        fn.apply(context, args);
      }, wait);
    };
  }

  /* ── privacy-first telemetry dispatcher ─────────────────────────────────── */

  function hasAnalyticsConsent() {
    try {
      var raw = localStorage.getItem('heritage_cookie_consent');
      if (!raw) return false;
      var parsed = JSON.parse(raw);
      return Boolean(parsed && parsed.analytics);
    } catch (e) {
      return false;
    }
  }

  function trackEvent(name, payload) {
    if (!hasAnalyticsConsent()) return;
    try {
      var eventData = {
        name: name,
        path: window.location.hash || '#home',
        timestamp: new Date().toISOString(),
        details: payload || {}
      };
      window.dispatchEvent(new CustomEvent('heritage:telemetry', { detail: eventData }));
      if (Array.isArray(window._heritageTelemetryBuffer)) {
        window._heritageTelemetryBuffer.push(eventData);
      }
    } catch (e) {
      // Fail silently to never interfere with primary UX
    }
  }

  /* ── router ───────────────────────────────────────────────────────────── */

  var views = {};
  var current = 'home';
  var lastFocus = null;
  var booted = false;          // set once init() has finished wiring the DOM

  var VIEW_SEO = {
    home: {
      title: 'Heritage Discovery — Visual Recognition & Cultural Discovery Platform',
      hash: '#home'
    },
    recognition: {
      title: 'Visual Identification Console — Heritage Discovery',
      hash: '#recognition'
    },
    heritage: {
      title: 'Monuments & Archaeological Catalogue — Heritage Discovery',
      hash: '#heritage'
    },
    about: {
      title: 'System Architecture & Health — Heritage Discovery',
      hash: '#about'
    },
    detail: {
      title: 'Monument Architectural Profile — Heritage Discovery',
      hash: '#heritage'
    }
  };

  function updateViewMeta(viewName) {
    var meta = VIEW_SEO[viewName];
    if (!meta) return;
    document.title = meta.title;
    var canonical = $('link[rel="canonical"]');
    if (canonical) {
      var base = window.location.origin + window.location.pathname.replace(/\/$/, '');
      canonical.setAttribute('href', base + '/' + meta.hash);
    }
  }

  function showView(name, opts) {
    var target = views[name] ? name : 'home';

    if (target === 'detail') {
      if (views.detail) {
        lastFocus = document.activeElement;
        views.detail.hidden = false;
        views.detail.classList.add('is-active');
        document.body.style.overflow = 'hidden';
      }
      current = 'detail';
      updateViewMeta('detail');
      trackEvent('page_view', { view: 'detail' });

      $$('.nav__link').forEach(function (link) {
        var isHeritage = link.getAttribute('data-nav') === 'heritage';
        if (isHeritage) link.setAttribute('aria-current', 'page');
        else link.removeAttribute('aria-current');
      });

      var backLink = $('#back-to-heritage');
      if (backLink) backLink.focus();
      return;
    }

    // Closing detail overlay if active
    if (views.detail && !views.detail.hidden) {
      views.detail.hidden = true;
      views.detail.classList.remove('is-active');
      document.body.style.overflow = '';
      if (lastFocus && typeof lastFocus.focus === 'function') {
        lastFocus.focus();
        lastFocus = null;
      }
    }

    current = target;
    updateViewMeta(target);
    trackEvent('page_view', { view: target });

    $$('.nav__link').forEach(function (link) {
      var isCurrent = link.getAttribute('data-nav') === target;
      if (isCurrent) link.setAttribute('aria-current', 'page');
      else link.removeAttribute('aria-current');
    });

    $$('.menu-panel__link').forEach(function (link) {
      var isCurrent = link.getAttribute('data-nav') === target;
      if (isCurrent) {
        link.setAttribute('aria-current', 'page');
        link.classList.add('is-active');
      } else {
        link.removeAttribute('aria-current');
        link.classList.remove('is-active');
      }
    });

    var targetEl = views[target];
    if (targetEl) {
      targetEl.classList.add('is-visible');
      if (!opts || opts.scroll !== false) {
        if (target === 'home') {
          window.scrollTo({ top: 0, behavior: reducedMotion() ? 'auto' : 'smooth' });
        } else {
          targetEl.scrollIntoView({
            behavior: reducedMotion() ? 'auto' : 'smooth',
            block: 'start'
          });
        }
      }
    }

    // Sync chapter rail and dock
    var railIndex = { home: 0, recognition: 1, heritage: 4, about: 5 }[target];
    if (typeof railIndex === 'number') {
      $$('.rail__item').forEach(function (item, idx) {
        item.classList.toggle('is-active', idx === railIndex);
      });
    }

    // Guarded: on a cold start routed straight to #heritage, showView() runs
    // before initExplorer() has bound these elements. init() kicks the load off
    // once everything is wired.
    if (booted && target === 'heritage' && catalogue.length === 0 && !catalogueLoading) loadCatalogue();
    if (target === 'about') refreshHealth();

    if (!opts || opts.focus !== false) {
      if (targetEl && target !== 'home') targetEl.focus({ preventScroll: true });
    }
  }

  function initScrollSpy() {
    if (!window.IntersectionObserver) return;

    var sectionIds = ['home', 'recognition', 'heritage', 'about'];
    var sections = sectionIds.map(function (k) { return views[k]; }).filter(Boolean);

    // Initial reveal of any sections already visible in the viewport
    sections.forEach(function (sec) {
      var rect = sec.getBoundingClientRect();
      if (rect.top < window.innerHeight && rect.bottom > 0) {
        sec.classList.add('is-visible', 'is-in-view');
      }
    });

    var observer = new IntersectionObserver(function (entries) {
      if (current === 'detail') return;

      entries.forEach(function (entry) {
        if (entry.isIntersecting) {
          entry.target.classList.add('is-visible', 'is-in-view');

          var viewName = entry.target.getAttribute('data-view');
          if (viewName && current !== viewName && (entry.intersectionRatio >= 0.25 || entry.boundingClientRect.top < window.innerHeight * 0.4)) {
            current = viewName;
            $$('.nav__link').forEach(function (link) {
              var isCurrent = link.getAttribute('data-nav') === viewName;
              if (isCurrent) link.setAttribute('aria-current', 'page');
              else link.removeAttribute('aria-current');
            });

            $$('.menu-panel__link').forEach(function (link) {
              var isCurrent = link.getAttribute('data-nav') === viewName;
              if (isCurrent) {
                link.setAttribute('aria-current', 'page');
                link.classList.add('is-active');
              } else {
                link.removeAttribute('aria-current');
                link.classList.remove('is-active');
              }
            });

            var railIndex = { home: 0, recognition: 1, heritage: 4, about: 5 }[viewName];
            if (typeof railIndex === 'number') {
              $$('.rail__item').forEach(function (item, idx) {
                item.classList.toggle('is-active', idx === railIndex);
              });
            }

            var dockChapter = $('#dock-chapter');
            if (dockChapter) {
              var dockNames = {
                home: '01 — Discover',
                recognition: '02 — Recognition',
                heritage: '05 — Explore',
                about: '06 — Evidence'
              };
              if (dockNames[viewName]) dockChapter.textContent = dockNames[viewName];
            }

            if (location.hash.slice(1) !== viewName) {
              history.replaceState(null, '', '#' + viewName);
            }
          }
        }
      });
    }, {
      rootMargin: '-10% 0px -30% 0px',
      threshold: [0.1, 0.25, 0.5]
    });

    sections.forEach(function (sec) {
      observer.observe(sec);
    });
  }

  function initRouter() {
    views = {
      home: $('#view-home'),
      recognition: $('#view-recognition'),
      heritage: $('#view-heritage'),
      detail: $('#view-detail'),
      about: $('#view-about')
    };

    document.addEventListener('click', function (ev) {
      var trigger = ev.target.closest('[data-nav]');
      if (!trigger) return;
      var view = trigger.getAttribute('data-nav');
      if (!views[view]) return;
      ev.preventDefault();
      closeMenu();
      showView(view);
      if (location.hash.slice(1) !== view) {
        history.replaceState(null, '', '#' + view);
      }
    });

    document.addEventListener('keydown', function (ev) {
      if (ev.key === 'Escape' && current === 'detail') {
        ev.preventDefault();
        showView('heritage');
        if (location.hash.slice(1) !== 'heritage') {
          history.replaceState(null, '', '#heritage');
        }
      }
    });

    window.addEventListener('hashchange', function () {
      var name = location.hash.slice(1).split('/')[0];
      if (views[name]) showView(name);
    });

    var initial = location.hash.slice(1).split('/')[0];
    showView(views[initial] ? initial : 'home', {
      focus: false,
      scroll: Boolean(initial && initial !== 'home')
    });
  }

  /* ── mobile menu ──────────────────────────────────────────────────────── */

  var menuPanel, menuScrim, menuToggle, menuClose, lastMenuFocus = null;

  function openMenu() {
    if (!menuPanel || menuToggle.getAttribute('aria-expanded') === 'true') return;
    lastMenuFocus = document.activeElement;
    menuScrim.hidden = false;
    menuPanel.hidden = false;
    // Force layout so the transition starts from the closed state. A plain
    // requestAnimationFrame is not enough: rAF is throttled in a background
    // tab, which would leave the panel stuck off-screen.
    void menuPanel.offsetWidth;
    menuScrim.classList.add('is-open');
    menuPanel.classList.add('is-open');
    menuToggle.setAttribute('aria-expanded', 'true');
    menuToggle.setAttribute('aria-label', 'Close menu');
    document.body.style.overflow = 'hidden';
    menuClose.focus();
  }

  function closeMenu() {
    if (!menuPanel || menuToggle.getAttribute('aria-expanded') !== 'true') return;
    menuScrim.classList.remove('is-open');
    menuPanel.classList.remove('is-open');
    menuToggle.setAttribute('aria-expanded', 'false');
    menuToggle.setAttribute('aria-label', 'Open menu');
    document.body.style.overflow = '';
    window.setTimeout(function () {
      if (menuToggle.getAttribute('aria-expanded') !== 'true') {
        menuPanel.hidden = true;
        menuScrim.hidden = true;
      }
    }, reducedMotion() ? 0 : 480);
    // Restore focus to the control that opened the panel. If focus was on
    // <body> (a programmatic open), send it to the toggle instead.
    if (lastMenuFocus && lastMenuFocus !== document.body && lastMenuFocus.focus) lastMenuFocus.focus();
    else menuToggle.focus();
  }

  function initMenu() {
    menuPanel = $('#mobile-menu');
    menuScrim = $('#menu-scrim');
    menuToggle = $('#menu-toggle');
    menuClose = $('#menu-close');

    menuToggle.addEventListener('click', function () {
      if (menuToggle.getAttribute('aria-expanded') === 'true') closeMenu();
      else openMenu();
    });
    menuClose.addEventListener('click', closeMenu);
    menuScrim.addEventListener('click', closeMenu);

    document.addEventListener('keydown', function (ev) {
      if (menuToggle.getAttribute('aria-expanded') !== 'true') return;

      if (ev.key === 'Escape') { ev.preventDefault(); closeMenu(); return; }

      if (ev.key === 'Tab') {
        var focusables = $$('button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])', menuPanel)
          .filter(function (node) { return node.offsetParent !== null; });
        if (!focusables.length) return;
        var first = focusables[0];
        var last = focusables[focusables.length - 1];
        if (ev.shiftKey && document.activeElement === first) { ev.preventDefault(); last.focus(); }
        else if (!ev.shiftKey && document.activeElement === last) { ev.preventDefault(); first.focus(); }
      }
    });
  }

  /* ── chapter rail ─────────────────────────────────────────────────────── */

  /* ── automatic storytelling chapter transitions (Phase 4 & 7) ──────────── */

  var CHAPTER_INTERVAL_MS = 8000;

  var CHAPTERS = [
    { eyebrow: 'Chapter 01 — Discover', title: ['Recognise the', 'stories of place'],
      desc: 'Identify monuments from photographs using computer vision, explore their history, and discover the architectural stories behind remarkable places.',
      dock: '01 — Discover', imageIndex: 0 },
    { eyebrow: 'Chapter 02 — Recognise', title: ['Every monument', 'begins as a photograph'],
      desc: 'Upload a photograph and the system embeds it with CLIP, then searches the indexed catalogue for visually similar monuments.',
      dock: '02 — Recognition', imageIndex: 1 },
    { eyebrow: 'Chapter 03 — Match', title: ['Similarity alone', 'is not identification'],
      desc: 'An open-set gate measures how far the best match stands above the field. A weak or ambiguous result is rejected rather than guessed.',
      dock: '03 — Match', imageIndex: 2 },
    { eyebrow: 'Chapter 04 — Verify', title: ['A match is only', 'accepted when it separates'],
      desc: 'Acceptance requires both a similarity threshold and a calibrated margin over the nearest competing site.',
      dock: '04 — Verify', imageIndex: 4 },
    { eyebrow: 'Chapter 05 — Explore', title: ['The catalogue', 'is the context'],
      desc: 'Explore 455 monuments by name, city, country, region or type, with the historical record attached to each one.',
      dock: '05 — Explore', imageIndex: 6 },
    { eyebrow: 'Chapter 06 — Evidence', title: ['Every claim', 'carries its source'],
      desc: 'Local identifications are reported with the catalogue metadata and the evidence records held with them, each with its named source.',
      dock: '06 — Evidence', imageIndex: 3 }
  ];

  function initChapters() {
    var items = $$('.rail__item');
    var dockChapter = $('#dock-chapter');
    var btnPrev = $('#chapter-prev');
    var btnNext = $('#chapter-next');
    var btnToggle = $('#chapter-play-toggle');
    var progressBar = $('#dock-chapter-progress');
    var heroInner = $('.hero__inner');

    var currentChapter = 0;
    var timer = null;
    var isUserPaused = false;
    var isHoverPaused = false;
    var isNarrativeTransitioning = false;

    function shouldSuspend() {
      if (isUserPaused || isHoverPaused) return true;
      return isExperienceSuspended();
    }

    function setChapter(index, opts) {
      if (typeof index !== 'number' || index < 0 || index >= CHAPTERS.length) return;
      currentChapter = index;
      var chapter = CHAPTERS[index];
      if (!chapter) return;

      items.forEach(function (item, i) {
        var isActive = i === index;
        item.classList.toggle('is-active', isActive);
        item.setAttribute('aria-current', isActive ? 'true' : 'false');
      });

      if (dockChapter) {
        dockChapter.textContent = chapter.dock || (String(index + 1).padStart(2, '0') + ' — ' + chapter.eyebrow.replace(/^Chapter \d+ — /, ''));
      }

      var eyebrowChapter = $('#hero-eyebrow-chapter') || $('.hero__eyebrow .eyebrow__text') || $('#home-eyebrow');
      var lines = $$('.hero__title .line__in');
      var desc = $('.hero__desc');

      var immediate = opts && opts.immediate;

      if (reducedMotion() || immediate || !heroInner) {
        if (eyebrowChapter) eyebrowChapter.textContent = chapter.eyebrow;
        if (lines[0]) lines[0].textContent = chapter.title[0];
        if (lines[1]) lines[1].textContent = chapter.title[1];
        if (desc) desc.textContent = chapter.desc;
      } else {
        // Coordinated narrative cross-reveal: fade out old text gently, then reveal new text
        isNarrativeTransitioning = true;
        heroInner.classList.add('is-narrative-leaving');

        window.setTimeout(function () {
          if (eyebrowChapter) eyebrowChapter.textContent = chapter.eyebrow;
          if (lines[0]) lines[0].textContent = chapter.title[0];
          if (lines[1]) lines[1].textContent = chapter.title[1];
          if (desc) desc.textContent = chapter.desc;

          heroInner.classList.remove('is-narrative-leaving');

          // Trigger staggered entry reveal without forced synchronous reflows
          lines.forEach(function (line) {
            line.style.animation = 'none';
          });
          if (desc) desc.style.animation = 'none';

          window.requestAnimationFrame(function () {
            lines.forEach(function (line, i) {
              line.style.animation = 'maskUp 0.85s var(--ease-out) both';
              line.style.animationDelay = (i * 0.1) + 's';
            });
            if (desc) {
              desc.style.animation = 'fadeUp 0.8s var(--ease-out) 0.22s both';
            }
          });

          isNarrativeTransitioning = false;
        }, 220);
      }

      if (!opts || opts.resetProgress !== false) {
        resetProgress();
      }
    }

    function advance() {
      if (shouldSuspend() || isNarrativeTransitioning) {
        stopTimer();
        timer = window.setTimeout(advance, 1500);
        return;
      }

      var next = (currentChapter + 1) % CHAPTERS.length;
      setChapter(next);
      scheduleNext();
    }

    function scheduleNext() {
      stopTimer();
      timer = window.setTimeout(advance, CHAPTER_INTERVAL_MS);
      resetProgress();
    }

    function stopTimer() {
      if (timer) {
        window.clearTimeout(timer);
        timer = null;
      }
      stopProgress();
    }

    function resetProgress() {
      if (!progressBar) return;
      progressBar.classList.remove('is-animating');
      progressBar.style.width = '0%';
      if (reducedMotion() || shouldSuspend()) return;
      window.requestAnimationFrame(function () {
        progressBar.classList.add('is-animating');
      });
    }

    function stopProgress() {
      if (!progressBar) return;
      progressBar.classList.remove('is-animating');
      progressBar.style.width = '0%';
    }

    function updatePlayButtonUI() {
      if (!btnToggle) return;
      var iconPause = btnToggle.querySelector('.icon-pause');
      var iconPlay = btnToggle.querySelector('.icon-play');
      if (isUserPaused) {
        if (iconPause) iconPause.setAttribute('hidden', '');
        if (iconPlay) iconPlay.removeAttribute('hidden');
        btnToggle.setAttribute('aria-label', 'Resume automatic chapter progression');
        btnToggle.setAttribute('title', 'Resume automatic chapter progression');
      } else {
        if (iconPause) iconPause.removeAttribute('hidden');
        if (iconPlay) iconPlay.setAttribute('hidden', '');
        btnToggle.setAttribute('aria-label', 'Pause automatic chapter progression');
        btnToggle.setAttribute('title', 'Pause automatic chapter progression');
      }
    }

    // Manual navigation: clicking on chapter rail items
    items.forEach(function (btn) {
      btn.addEventListener('click', function () {
        var index = parseInt(btn.getAttribute('data-chapter'), 10);
        setChapter(index);

        // Cue deliberate image mapping on manual chapter selection without resetting slideshow interval
        var mappedImage = CHAPTER_IMAGE_MAP[index];
        if (typeof mappedImage === 'number' && slideshowController.cueSlide) {
          slideshowController.cueSlide(mappedImage);
        }

        var navMap = { 0: 'home', 1: 'recognition', 4: 'heritage', 5: 'about' };
        if (navMap[index]) {
          showView(navMap[index]);
          if (location.hash.slice(1) !== navMap[index]) {
            history.replaceState(null, '', '#' + navMap[index]);
          }
        }
        if (!isUserPaused) scheduleNext();
      });
    });

    // Manual navigation: Previous & Next buttons
    if (btnPrev) {
      btnPrev.addEventListener('click', function () {
        var prev = (currentChapter - 1 + CHAPTERS.length) % CHAPTERS.length;
        setChapter(prev);
        var mappedImage = CHAPTER_IMAGE_MAP[prev];
        if (typeof mappedImage === 'number' && slideshowController.cueSlide) {
          slideshowController.cueSlide(mappedImage);
        }
        if (!isUserPaused) scheduleNext();
      });
    }

    if (btnNext) {
      btnNext.addEventListener('click', function () {
        var next = (currentChapter + 1) % CHAPTERS.length;
        setChapter(next);
        var mappedImage = CHAPTER_IMAGE_MAP[next];
        if (typeof mappedImage === 'number' && slideshowController.cueSlide) {
          slideshowController.cueSlide(mappedImage);
        }
        if (!isUserPaused) scheduleNext();
      });
    }

    if (btnToggle) {
      btnToggle.addEventListener('click', function () {
        isUserPaused = !isUserPaused;
        updatePlayButtonUI();
        if (isUserPaused) {
          stopTimer();
        } else {
          scheduleNext();
        }
      });
    }

    // Hover pause over chapter controls & reading area
    var chapterControls = $('.dock__cell--chapter');
    if (chapterControls) {
      chapterControls.addEventListener('mouseenter', function () {
        isHoverPaused = true;
      });
      chapterControls.addEventListener('mouseleave', function () {
        isHoverPaused = false;
        if (!isUserPaused && !shouldSuspend()) {
          resetProgress();
        }
      });
    }

    // Hover pause over hero content while reading
    if (heroInner) {
      heroInner.addEventListener('mouseenter', function () {
        isHoverPaused = true;
      });
      heroInner.addEventListener('mouseleave', function () {
        isHoverPaused = false;
        if (!isUserPaused && !shouldSuspend()) {
          resetProgress();
        }
      });
    }

    // Window scroll listener: pause/resume when entering/leaving hero
    window.addEventListener('scroll', function () {
      if (shouldSuspend()) {
        stopTimer();
      } else if (!timer && !isUserPaused) {
        scheduleNext();
      }
    }, { passive: true });

    // Page visibility listener: pause when backgrounded, resume when visible
    document.addEventListener('visibilitychange', function () {
      if (document.hidden || shouldSuspend()) {
        stopTimer();
      } else if (!isUserPaused && !shouldSuspend()) {
        scheduleNext();
      }
    });

    // Initialize at chapter 0 immediately without transition delay
    setChapter(0, { immediate: true });
    if (!reducedMotion()) {
      scheduleNext();
    }
  }

  /* ── cinematic parallax (pointer & scroll depth) ─────────────────────── */

  function initParallax() {
    if (reducedMotion()) return;

    var bg = $('#hero-bg');
    var rail = $('.rail');
    var hero = $('#hero');
    if (!hero || !bg) return;

    var raf = null;
    var tx = 0, ty = 0;
    var scrollY = 0;
    var heroRect = null;
    var heroHeight = hero.offsetHeight || 800;
    var isCoarse = coarsePointer();

    function measureHero() {
      heroRect = hero.getBoundingClientRect();
      heroHeight = hero.offsetHeight || 800;
    }
    measureHero();

    function updateParallax() {
      // Restrained scroll parallax: bg gently glides at ~22% speed of scroll
      var scrollOffset = Math.min(scrollY * 0.22, heroHeight * 0.35);
      var ptrX = isCoarse ? 0 : (-tx * 10);
      var ptrY = isCoarse ? 0 : (-ty * 7);

      bg.style.transform = 'scale(1.05) translate3d(' + ptrX.toFixed(2) + 'px,' + (scrollOffset + ptrY).toFixed(2) + 'px, 0)';
      if (rail && !isCoarse) {
        rail.style.transform = 'translateY(-50%) translateX(' + (tx * 6).toFixed(2) + 'px)';
      }
      raf = null;
    }

    function requestTick() {
      if (raf === null) {
        raf = window.requestAnimationFrame(updateParallax);
      }
    }

    // Pointer movement (desktop mouse only)
    if (!isCoarse) {
      hero.addEventListener('pointermove', function (ev) {
        if (ev.pointerType !== 'mouse') return;
        if (!heroRect) measureHero();
        tx = (ev.clientX - heroRect.left) / heroRect.width - 0.5;
        ty = (ev.clientY - heroRect.top) / heroRect.height - 0.5;
        requestTick();
      }, { passive: true });

      hero.addEventListener('pointerleave', function () {
        tx = 0;
        ty = 0;
        requestTick();
      });
    }

    // Scroll parallax (active only while hero is in/near viewport)
    window.addEventListener('scroll', function () {
      var currentY = window.scrollY || window.pageYOffset || 0;
      if (currentY <= heroHeight * 1.3) {
        scrollY = currentY;
        requestTick();
      }
    }, { passive: true });

    window.addEventListener('resize', function () {
      measureHero();
      isCoarse = coarsePointer();
      requestTick();
    }, { passive: true });

    // Initial position
    requestTick();
  }

  /* ── cinematic cursor effects (desktop pointer only) ──────────────────── */

  function initCursor() {
    if (reducedMotion() || coarsePointer() || (window.innerWidth && window.innerWidth <= 900)) {
      return;
    }

    var spotlight = document.getElementById('cursor-spotlight');
    var dot = document.getElementById('cursor-dot');
    if (!spotlight || !dot) return;

    var targetX = -1000;
    var targetY = -1000;
    var spotX = -1000;
    var spotY = -1000;
    var dotX = -1000;
    var dotY = -1000;

    var isVisible = false;
    var isHovering = false;
    var lastTarget = null;
    var lastInteractive = false;
    var raf = null;
    var isRunning = false;

    // Interactive target selector: buttons, links, controls, cards, upload trigger
    var interactiveSelector = 'a, button, [role="button"], input, select, textarea, label, [data-nav], .btn, .card, .upload, .field__input, .menu-toggle, .rail__item, .hero__badge, .stat';

    function render() {
      // Differential damping: dot is responsive (0.24), spotlight has cinematic lag (0.085)
      var dDotX = targetX - dotX;
      var dDotY = targetY - dotY;
      var dSpotX = targetX - spotX;
      var dSpotY = targetY - spotY;

      dotX += dDotX * 0.24;
      dotY += dDotY * 0.24;
      spotX += dSpotX * 0.085;
      spotY += dSpotY * 0.085;

      dot.style.transform = 'translate3d(' + dotX.toFixed(2) + 'px,' + dotY.toFixed(2) + 'px,0) translate(-50%,-50%)';
      spotlight.style.transform = 'translate3d(' + spotX.toFixed(2) + 'px,' + spotY.toFixed(2) + 'px,0) translate(-50%,-50%)';

      // Check if motion has settled below 0.15px
      var isMoving = Math.abs(dDotX) > 0.15 || Math.abs(dDotY) > 0.15 || Math.abs(dSpotX) > 0.15 || Math.abs(dSpotY) > 0.15;

      if (isMoving && isVisible) {
        raf = window.requestAnimationFrame(render);
      } else {
        isRunning = false;
        raf = null;
      }
    }

    function wakeLoop() {
      if (!isRunning && isVisible) {
        isRunning = true;
        raf = window.requestAnimationFrame(render);
      }
    }

    function onPointerMove(ev) {
      if (ev.pointerType && ev.pointerType !== 'mouse') return;

      var x = ev.clientX;
      var y = ev.clientY;

      if (!isVisible) {
        isVisible = true;
        spotlight.classList.add('is-visible');
        dot.classList.add('is-visible');
        if (targetX < 0) {
          spotX = x;
          spotY = y;
          dotX = x;
          dotY = y;
        }
      }

      targetX = x;
      targetY = y;

      var target = ev.target;
      var interactive = lastInteractive;
      if (target !== lastTarget) {
        lastTarget = target;
        interactive = Boolean(target && target.closest && target.closest(interactiveSelector));
        lastInteractive = interactive;
      }

      if (interactive && !isHovering) {
        isHovering = true;
        spotlight.classList.add('is-hovering');
        dot.classList.add('is-hovering');
      } else if (!interactive && isHovering) {
        isHovering = false;
        spotlight.classList.remove('is-hovering');
        dot.classList.remove('is-hovering');
      }

      wakeLoop();
    }

    function onPointerLeave() {
      isVisible = false;
      isHovering = false;
      lastTarget = null;
      lastInteractive = false;
      spotlight.classList.remove('is-visible', 'is-hovering');
      dot.classList.remove('is-visible', 'is-hovering');
      if (raf) {
        window.cancelAnimationFrame(raf);
        raf = null;
        isRunning = false;
      }
    }

    window.addEventListener('pointermove', onPointerMove, { passive: true });
    document.addEventListener('pointerleave', onPointerLeave, { passive: true });
    window.addEventListener('blur', onPointerLeave);

    window.addEventListener('resize', function () {
      if (reducedMotion() || coarsePointer() || (window.innerWidth && window.innerWidth <= 900)) {
        onPointerLeave();
      }
    }, { passive: true });
  }

  /* ── cinematic storyline effects (Phase 3) ──────────────────────────── */

  function initStoryline() {
    var revealElements = $$('.story-reveal');
    if (!revealElements.length) return;

    if (reducedMotion()) {
      revealElements.forEach(function (node) {
        node.classList.add('is-revealed');
      });
      return;
    }

    if (!window.IntersectionObserver) {
      revealElements.forEach(function (node) {
        node.classList.add('is-revealed');
      });
      return;
    }

    // Observer for elements as the user scrolls
    var storyObserver = new IntersectionObserver(function (entries, observer) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) {
          entry.target.classList.add('is-revealed');
          // Once revealed, unobserve to prevent replaying animations or memory retention
          observer.unobserve(entry.target);
        }
      });
    }, {
      rootMargin: '0px 0px -40px 0px',
      threshold: [0.08, 0.2]
    });

    revealElements.forEach(function (node) {
      storyObserver.observe(node);
    });
  }

  /* ── seven-image background slideshow ─────────────────────────────────── */

  function initSlideshow() {
    var bg = $('#hero-bg');
    if (!bg || !SLIDESHOW_CONFIG || !SLIDESHOW_CONFIG.length) return;

    var slideA = $('#hero-slide-a');
    var slideB = $('#hero-slide-b');

    if (!slideA) {
      slideA = el('div', 'hero__slide');
      slideA.id = 'hero-slide-a';
      bg.appendChild(slideA);
    }
    if (!slideB) {
      slideB = el('div', 'hero__slide');
      slideB.id = 'hero-slide-b';
      bg.appendChild(slideB);
    }

    var currentIndex = 0;
    var activeSlide = slideA;
    var timer = null;
    var preloadedImgs = {};
    var isTransitioning = false;
    var isLoading = false;

    function preload(url) {
      if (!url || preloadedImgs[url]) return;
      var img = new Image();
      img.src = url;
      preloadedImgs[url] = img;
    }

    // Initialize slideA with the first image and custom focal position
    var firstItem = SLIDESHOW_CONFIG[0];
    var firstUrl = getSlideUrl(firstItem);
    slideA.style.backgroundImage = 'url("' + firstUrl + '")';
    slideA.style.backgroundPosition = getSlidePosition(firstItem);
    slideA.classList.add('is-active', 'ken-burns-a');
    preload(firstUrl);
    if (SLIDESHOW_CONFIG.length > 1) {
      preload(getSlideUrl(SLIDESHOW_CONFIG[1]));
    }
    updateMonumentBadge(firstItem.name);

    function updateMonumentBadge(name) {
      var monumentEl = $('#hero-eyebrow-monument');
      if (!monumentEl || !name) return;
      if (reducedMotion()) {
        monumentEl.textContent = name;
        return;
      }
      monumentEl.classList.add('is-fading');
      window.setTimeout(function () {
        monumentEl.textContent = name;
        monumentEl.classList.remove('is-fading');
      }, 200);
    }

    function performTransition(targetIndex, nextItem, nextUrl, onDone) {
      isLoading = false;
      isTransitioning = true;

      var incoming = (activeSlide === slideA) ? slideB : slideA;
      var outgoing = activeSlide;

      // Position incoming over outgoing without brightness dip
      incoming.style.backgroundImage = 'url("' + nextUrl + '")';
      incoming.style.backgroundPosition = getSlidePosition(nextItem);
      incoming.classList.remove('ken-burns-a', 'ken-burns-b', 'is-active');
      incoming.classList.add('is-incoming'); // z-index: 2, opacity: 0

      // Use requestAnimationFrame instead of forced layout reflow
      window.requestAnimationFrame(function () {
        if (!reducedMotion()) {
          incoming.classList.add(targetIndex % 2 === 0 ? 'ken-burns-a' : 'ken-burns-b');
        }
        incoming.classList.add('is-active');

        updateMonumentBadge(nextItem.name);

        var transitionDuration = reducedMotion() ? 50 : 1450;
        window.setTimeout(function () {
          outgoing.classList.remove('is-active', 'is-incoming', 'ken-burns-a', 'ken-burns-b');
          outgoing.style.backgroundImage = '';
          incoming.classList.remove('is-incoming');
          activeSlide = incoming;
          currentIndex = targetIndex;
          isTransitioning = false;

          // Intelligently preload next image in sequence
          var subsequent = (currentIndex + 1) % SLIDESHOW_CONFIG.length;
          preload(getSlideUrl(SLIDESHOW_CONFIG[subsequent]));

          if (onDone) onDone();
        }, transitionDuration);
      });
    }

    function transitionToSlide(targetIndex, onDone) {
      if (typeof targetIndex !== 'number' || targetIndex < 0 || targetIndex >= SLIDESHOW_CONFIG.length) {
        if (onDone) onDone();
        return;
      }
      if (targetIndex === currentIndex && activeSlide.classList.contains('is-active')) {
        if (onDone) onDone();
        return;
      }

      var nextItem = SLIDESHOW_CONFIG[targetIndex];
      var nextUrl = getSlideUrl(nextItem);
      isLoading = true;

      // If already preloaded and cached, transition immediately without network delay
      if (preloadedImgs[nextUrl] && preloadedImgs[nextUrl].complete) {
        performTransition(targetIndex, nextItem, nextUrl, onDone);
        return;
      }

      var testImg = new Image();
      testImg.onload = function () {
        preloadedImgs[nextUrl] = testImg;
        performTransition(targetIndex, nextItem, nextUrl, onDone);
      };

      testImg.onerror = function () {
        // Fall back to JPEG if WebP fails
        if (nextItem.fallback && nextUrl !== nextItem.fallback) {
          nextUrl = nextItem.fallback;
          performTransition(targetIndex, nextItem, nextUrl, onDone);
          return;
        }
        isLoading = false;
        isTransitioning = false;
        console.warn('Slideshow image unavailable: ' + nextUrl);
        currentIndex = targetIndex;
        if (onDone) onDone();
      };

      testImg.src = nextUrl;
    }

    function advance() {
      if (isExperienceSuspended() || isTransitioning || isLoading) {
        scheduleNext();
        return;
      }

      var nextIndex = (currentIndex + 1) % SLIDESHOW_CONFIG.length;
      transitionToSlide(nextIndex, function () {
        scheduleNext();
      });
    }

    function scheduleNext() {
      stopTimer();
      timer = window.setTimeout(advance, SLIDESHOW_INTERVAL_MS);
    }

    function stopTimer() {
      if (timer) {
        window.clearTimeout(timer);
        timer = null;
      }
    }

    // Expose controller for deliberate manual cues without resetting slideshow interval
    slideshowController.cueSlide = function (targetIndex) {
      if (typeof targetIndex !== 'number') return;
      if (targetIndex === currentIndex || isTransitioning || isLoading) return;
      transitionToSlide(targetIndex, null);
    };

    slideshowController.getCurrentIndex = function () {
      return currentIndex;
    };

    // Listeners for window scroll, visibility and responsive resizing
    var handleResize = debounce(function () {
      if (activeSlide && SLIDESHOW_CONFIG[currentIndex]) {
        var cur = SLIDESHOW_CONFIG[currentIndex];
        activeSlide.style.backgroundPosition = getSlidePosition(cur);
        var expectedUrl = getSlideUrl(cur);
        if (expectedUrl && activeSlide.style.backgroundImage.indexOf(expectedUrl) === -1) {
          activeSlide.style.backgroundImage = 'url("' + expectedUrl + '")';
        }
      }
      if (isExperienceSuspended()) {
        stopTimer();
      } else if (!timer) {
        scheduleNext();
      }
    }, 120);

    window.addEventListener('resize', handleResize, { passive: true });
    window.addEventListener('orientationchange', handleResize, { passive: true });

    window.addEventListener('scroll', function () {
      if (isExperienceSuspended()) {
        stopTimer();
      } else if (!timer) {
        scheduleNext();
      }
    }, { passive: true });

    document.addEventListener('visibilitychange', function () {
      if (document.hidden || isExperienceSuspended()) {
        stopTimer();
      } else if (!timer) {
        scheduleNext();
      }
    });

    scheduleNext();
  }

  /* ── health ───────────────────────────────────────────────────────────── */

  var health = null;
  var healthTimer = null;
  var isCheckingHealth = false;

  function refreshHealth(silent) {
    if (!API_BASE) {
      health = null;
      paintHealth();
      return Promise.resolve(null);
    }
    if (isCheckingHealth) return Promise.resolve(health);
    isCheckingHealth = true;

    var dockSystem = $('#dock-system');
    if (dockSystem && !health && !silent) {
      dockSystem.textContent = 'Connecting...';
      dockSystem.className = 'dock__v is-warn';
    }

    return fetch(API_BASE + '/health')
      .then(function (res) { return res.ok ? res.json() : null; })
      .then(function (data) {
        isCheckingHealth = false;
        health = data;
        paintHealth();
        if (healthTimer) { clearTimeout(healthTimer); healthTimer = null; }
        return data;
      })
      .catch(function () {
        isCheckingHealth = false;
        health = null;
        paintHealth();
        // Render free tier sleeps after 15 min; auto-retry every 5s during cold-start!
        if (!healthTimer) {
          healthTimer = setTimeout(function () {
            healthTimer = null;
            refreshHealth(true);
          }, 5000);
        }
        return null;
      });
  }

  function paintHealth() {
    var dockSystem = $('#dock-system');
    var dockIndex = $('#dock-index');

    if (!dockSystem || !dockIndex) return;

    if (!API_BASE) {
      dockSystem.textContent = 'API not connected';
      dockSystem.className = 'dock__v is-warn';
      dockSystem.title = 'Click to connect a Heritage Backend API URL';
      dockIndex.textContent = '—';
      setHealthPanel(null);
      return;
    }

    if (!health) {
      dockSystem.textContent = isCheckingHealth ? 'Connecting...' : 'Backend asleep / offline';
      dockSystem.className = 'dock__v is-err';
      dockSystem.title = 'Target: ' + API_BASE + ' (Click to configure or wait for Render spin-up)';
      dockIndex.textContent = '—';
      setHealthPanel(null);
      return;
    }

    var ok = health.service_ready && health.status === 'ok';
    dockSystem.textContent = ok ? 'Ready' : (health.status || 'Degraded');
    dockSystem.className = 'dock__v ' + (ok ? 'is-ok' : 'is-warn');
    dockSystem.title = 'Backend online: ' + API_BASE;
    dockIndex.textContent = typeof health.index_size === 'number' ? String(health.index_size) : '—';
    setHealthPanel(health);
  }

  function setHealthPanel(data) {
    var panel = $('#about-health');
    if (!panel) return;
    var map = {
      status: data ? data.status : 'unreachable',
      ready: data ? (data.service_ready ? 'yes' : 'no') : '—',
      index: data && typeof data.index_size === 'number' ? String(data.index_size) : '—',
      threshold: data && typeof data.similarity_threshold === 'number' ? String(data.similarity_threshold) : '—',
      catalogue: catalogue.length ? String(catalogue.length) : '—'
    };
    Object.keys(map).forEach(function (key) {
      var node = panel.querySelector('[data-health="' + key + '"]');
      if (node) node.textContent = map[key];
    });
  }

  /* ── upload ───────────────────────────────────────────────────────────── */

  var fileInput, uploadZone, uploadIdle, uploadPreview, previewImg, previewName, previewSize;
  var recognizeBtn, recStatus, uploadError, resultRegion;
  var selected = null;          // { file, dataUrl, name, size }
  var busy = false;

  function initUpload() {
    fileInput = $('#file-input');
    uploadZone = $('#upload-zone');
    uploadIdle = $('#upload-idle');
    uploadPreview = $('#upload-preview');
    previewImg = $('#preview-img');
    previewName = $('#preview-name');
    previewSize = $('#preview-size');
    recognizeBtn = $('#recognize-btn');
    recStatus = $('#rec-status');
    uploadError = $('#upload-error');
    resultRegion = $('#result-region');

    // clicking anywhere on the zone opens the picker, except the buttons,
    // which have their own handlers below
    uploadZone.addEventListener('click', function (ev) {
      if (ev.target.closest('button')) return;
      fileInput.click();
    });

    // keyboard access for the whole drop zone, not just the inner button
    uploadZone.addEventListener('keydown', function (ev) {
      if (ev.key === 'Enter' || ev.key === ' ' || ev.key === 'Spacebar') {
        if (ev.target.closest('button')) return;
        ev.preventDefault();
        fileInput.click();
      }
    });

    $('#upload-browse').addEventListener('click', function (ev) {
      ev.stopPropagation();
      fileInput.click();
    });
    $('#replace-btn').addEventListener('click', function (ev) {
      ev.stopPropagation();
      fileInput.click();
    });
    $('#remove-btn').addEventListener('click', function (ev) {
      ev.stopPropagation();
      clearSelection();
    });

    fileInput.addEventListener('change', function () {
      if (fileInput.files && fileInput.files[0]) acceptFile(fileInput.files[0]);
      fileInput.value = '';
    });

    ['dragenter', 'dragover'].forEach(function (name) {
      uploadZone.addEventListener(name, function (ev) {
        ev.preventDefault();
        ev.stopPropagation();
        if (!busy) uploadZone.classList.add('is-drag');
      });
    });
    ['dragleave', 'drop'].forEach(function (name) {
      uploadZone.addEventListener(name, function (ev) {
        ev.preventDefault();
        ev.stopPropagation();
        if (name === 'dragleave' && ev.relatedTarget && uploadZone.contains(ev.relatedTarget)) return;
        uploadZone.classList.remove('is-drag');
      });
    });
    uploadZone.addEventListener('drop', function (ev) {
      if (busy) return;
      var dt = ev.dataTransfer;
      if (!dt) return;
      var file = dt.files && dt.files[0];
      if (file) acceptFile(file);
      else {
        showUploadError('That drop did not contain a readable file.');
      }
    });

    recognizeBtn.addEventListener('click', runRecognition);
  }

  function showUploadError(message) {
    uploadError.textContent = message;
    uploadError.hidden = !message;
  }

  /* Downscale before upload.
     The backend rejects any decoded payload above 10 MB with HTTP 400, and a
     modern phone photo is routinely larger than that. Re-encoding through a
     canvas keeps the recognisable content at a few hundred KB. Returns the
     original data URL when it is already small enough. */
  function downscale(dataUrl) {
    return new Promise(function (resolve) {
      if (dataUrl.length <= MAX_DATA_URL_CHARS) { resolve(dataUrl); return; }

      var img = new Image();
      img.onload = function () {
        try {
          var longest = Math.max(img.naturalWidth, img.naturalHeight);
          if (!longest) { resolve(dataUrl); return; }

          var ratio = Math.min(1, MAX_EDGE / longest);
          var w = Math.max(1, Math.round(img.naturalWidth * ratio));
          var h = Math.max(1, Math.round(img.naturalHeight * ratio));

          var canvas = document.createElement('canvas');
          canvas.width = w;
          canvas.height = h;
          var ctx = canvas.getContext('2d');
          if (!ctx) { resolve(dataUrl); return; }
          ctx.drawImage(img, 0, 0, w, h);

          var encoded = canvas.toDataURL('image/jpeg', 0.9);
          // if JPEG did not get it under the limit, try a smaller edge
          if (encoded.length > MAX_DATA_URL_CHARS && ratio < 0.5) {
            resolve(downscaleTo(img, w * 0.6, h * 0.6));
          } else {
            resolve(encoded);
          }
        } catch (err) {
          resolve(dataUrl);
        }
      };
      img.onerror = function () { resolve(dataUrl); };
      img.src = dataUrl;
    });
  }

  function downscaleTo(img, w, h) {
    var canvas = document.createElement('canvas');
    canvas.width = Math.max(1, Math.round(w));
    canvas.height = Math.max(1, Math.round(h));
    var ctx = canvas.getContext('2d');
    ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
    return canvas.toDataURL('image/jpeg', 0.82);
  }

  function acceptFile(file) {
    showUploadError('');

    if (ACCEPTED.indexOf(file.type) < 0) {
      showUploadError('Unsupported file type. Choose a JPG, PNG or WebP image.');
      return;
    }
    if (file.size > MAX_BYTES) {
      showUploadError('That image is ' + bytes(file.size) + '. The limit is 10 MB — try a smaller photo.');
      return;
    }
    if (file.size === 0) {
      showUploadError('That file is empty.');
      return;
    }

    var reader = new FileReader();
    reader.onerror = function () { showUploadError('That file could not be read from disk.'); };
    reader.onload = function () {
      var dataUrl = String(reader.result);
      downscale(dataUrl).then(function (payload) {
        selected = { file: file, dataUrl: payload, name: file.name, size: file.size };
        previewImg.src = payload;
        previewImg.alt = 'Preview of the uploaded image: ' + file.name;
        previewName.textContent = file.name;
        var note = bytes(file.size);
        if (payload !== dataUrl) note += ' · sent at reduced resolution';
        note += ' · ' + (file.type.replace('image/', '').toUpperCase());
        previewSize.textContent = note;
        uploadIdle.hidden = true;
        uploadPreview.hidden = false;
        recognizeBtn.disabled = false;
        recStatus.textContent = 'Ready to run';
        recStatus.className = 'recognition-actions__status';
        resultRegion.innerHTML = '';
        resetPipeline();
      });
    };
    reader.readAsDataURL(file);
  }

  function clearSelection() {
    selected = null;
    previewImg.removeAttribute('src');
    previewImg.alt = '';
    uploadIdle.hidden = false;
    uploadPreview.hidden = true;
    recognizeBtn.disabled = true;
    recStatus.textContent = '';
    recStatus.className = 'recognition-actions__status';
    resultRegion.innerHTML = '';
    showUploadError('');
    uploadZone.classList.remove('is-drag');
    resetPipeline();
  }

  /* ── pipeline stages ──────────────────────────────────────────────────── */

  var STAGES = ['image', 'analysis', 'match', 'evidence'];
  var stageTimers = [];

  function clearStageTimers() {
    stageTimers.forEach(function (id) { window.clearTimeout(id); });
    stageTimers = [];
  }

  function setStage(name) {
    var index = STAGES.indexOf(name);
    $$('.pipeline__stage').forEach(function (node, i) {
      var isActive = i === index;
      var isDone = i < index;
      node.classList.toggle('is-active', isActive);
      node.classList.toggle('is-done', isDone);
      if (isActive) node.setAttribute('aria-current', 'step');
      else node.removeAttribute('aria-current');
    });
  }

  function completePipeline() {
    $$('.pipeline__stage').forEach(function (node) {
      node.classList.remove('is-active');
      node.classList.add('is-done');
      node.removeAttribute('aria-current');
    });
  }

  function resetPipeline() {
    clearStageTimers();
    $$('.pipeline__stage').forEach(function (node) {
      node.classList.remove('is-active', 'is-done');
      node.removeAttribute('aria-current');
    });
  }

  /* ── recognition ──────────────────────────────────────────────────────── */

  function runRecognition() {
    if (!selected || busy) return;

    if (!API_BASE) {
      clearStageTimers();
      resetPipeline();
      recStatus.textContent = 'Setup Required';
      recStatus.className = 'recognition-actions__status is-err';
      resultRegion.innerHTML = '';
      resultRegion.appendChild(errorPanel('This frontend is hosted on Vercel, but no backend API is connected yet. Enter your backend URL below to connect.', true));
      return;
    }

    busy = true;
    recognizeBtn.disabled = true;
    uploadZone.classList.add('is-busy');
    recStatus.className = 'recognition-actions__status is-busy';
    resultRegion.innerHTML = '';

    resetPipeline();
    setStage('image');
    stageTimers.push(window.setTimeout(function () { setStage('analysis'); }, 450));
    stageTimers.push(window.setTimeout(function () { setStage('match'); }, 1400));

    var payload = { image_base64: selected.dataUrl, question: '', top_k: 5 };

    trackEvent('recognition_started', {
      file_size_bytes: selected.file ? selected.file.size : 0
    });

    fetch(API_BASE + '/recognize', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    })
      .then(function (res) {
        return res.json()
          .catch(function () { return null; })
          .then(function (body) { return { ok: res.ok, status: res.status, body: body }; });
      })
      .then(function (outcome) {
        if (!outcome.body) throw { code: 'internal_error', status: outcome.status };
        if (!outcome.ok) throw { code: outcome.body.error, detail: outcome.body.detail, status: outcome.status };
        return outcome.body;
      })
      .then(function (data) {
        clearStageTimers();
        setStage('evidence');
        renderResult(data);
        completePipeline();
        var isGlobal = data.recognition_source === 'gemini' || data.recognition_source === 'ollama';
        recStatus.textContent = data.recognition_source === 'unknown' ? 'Not confirmed'
          : (isGlobal && (!data.global_identification || data.global_identification.unknown || !data.global_identification.site_name)) ? 'Not confirmed'
          : isGlobal ? 'Identified (External Recognition)'
          : 'Complete';
        recStatus.className = 'recognition-actions__status';

        trackEvent('recognition_completed', {
          recognition_source: data.recognition_source,
          has_match: data.recognition_source === 'faiss' || data.recognition_source === 'gemini',
          score: data.similarity !== undefined ? data.similarity : (data.global_identification ? data.global_identification.confidence : null)
        });
      })
      .catch(function (err) {
        clearStageTimers();
        resetPipeline();
        var code = err && err.code;
        // A fetch() network failure rejects with a TypeError and carries no
        // status, so it is matched by type rather than by status code.
        var offline = err instanceof TypeError || (err && err.status === 0);
        var targetHint = API_BASE ? (' at ' + API_BASE) : '';
        var message = ERROR_MESSAGES[code] ||
          (offline
            ? 'The recognition service could not be reached' + targetHint + '. Is your backend running and reachable?'
            : 'Recognition could not be completed. Please try again.');
        recStatus.textContent = 'Failed';
        recStatus.className = 'recognition-actions__status is-err';
        resultRegion.innerHTML = '';
        resultRegion.appendChild(errorPanel(message, offline));

        trackEvent('recognition_failed', {
          code: code || 'network_error',
          offline: offline
        });
      })
      .then(function () {
        busy = false;
        recognizeBtn.disabled = !selected;
        uploadZone.classList.remove('is-busy');
      });
  }

  function renderApiConnector() {
    var box = el('div', 'api-connector');
    var title = el('div', 'api-connector__title', 'Connect Backend API');
    var desc = el('p', 'api-connector__desc',
      'The frontend is active on Vercel. Monument recognition with PyTorch & OpenCLIP requires the Python backend. Enter your backend API URL below:');

    var form = el('div', 'api-connector__form');
    var input = el('input', 'api-connector__input');
    input.type = 'url';
    input.placeholder = 'https://your-backend.onrender.com or http://localhost:8000';
    input.value = API_BASE || '';

    var btn = el('button', 'btn btn--subtle api-connector__btn', 'Connect API');
    btn.type = 'button';

    var statusEl = el('div', 'api-connector__status');

    var options = el('div', 'api-connector__options');
    var optLabel = el('span', 'api-connector__options-label', 'Presets:');
    options.appendChild(optLabel);

    var presets = [
      { label: 'Render Cloud (Live)', url: 'https://heritage-1-why4.onrender.com' },
      { label: 'Local (127.0.0.1:8000)', url: 'http://127.0.0.1:8000' },
      { label: 'Localhost (8000)', url: 'http://localhost:8000' }
    ];

    presets.forEach(function (preset) {
      var optBtn = el('button', 'api-connector__preset-chip', preset.label);
      optBtn.type = 'button';
      optBtn.addEventListener('click', function () {
        input.value = preset.url;
        testAndSave(preset.url);
      });
      options.appendChild(optBtn);
    });

    function testAndSave(targetUrl) {
      var clean = (targetUrl || '').trim().replace(/\/$/, '');
      if (!clean) {
        statusEl.textContent = 'Please enter a URL.';
        statusEl.className = 'api-connector__status is-err';
        return;
      }
      btn.disabled = true;
      btn.textContent = 'Connecting...';
      statusEl.textContent = 'Testing connection to ' + clean + '/health ...';
      statusEl.className = 'api-connector__status is-busy';

      fetch(clean + '/health', { mode: 'cors' })
        .then(function (res) {
          if (!res.ok) throw new Error('HTTP ' + res.status);
          return res.json();
        })
        .then(function (data) {
          btn.disabled = false;
          btn.textContent = 'Connected';
          statusEl.textContent = '✓ Successfully connected! Backend status: ' + (data.status || 'ok') + ' (' + (data.index_size || 0) + ' monuments indexed).';
          statusEl.className = 'api-connector__status is-ok';
          setApiBase(clean);
          if (recognizeBtn && selected) {
            recognizeBtn.disabled = false;
          }
        })
        .catch(function () {
          btn.disabled = false;
          btn.textContent = 'Connect API';
          var hint = (location.protocol === 'https:' && clean.startsWith('http://'))
            ? ' Note: This site is loaded over HTTPS. Browsers block unencrypted HTTP (Mixed Content). Use an HTTPS URL (e.g. from ngrok, Render, or Hugging Face).'
            : ' Ensure the backend is running and CORS is enabled.';
          statusEl.textContent = '✗ Could not connect to ' + clean + '.' + hint;
          statusEl.className = 'api-connector__status is-err';
        });
    }

    btn.addEventListener('click', function () {
      testAndSave(input.value);
    });

    input.addEventListener('keydown', function (e) {
      if (e.key === 'Enter') {
        e.preventDefault();
        testAndSave(input.value);
      }
    });

    form.appendChild(input);
    form.appendChild(btn);

    box.appendChild(title);
    box.appendChild(desc);
    box.appendChild(form);
    box.appendChild(statusEl);
    box.appendChild(options);

    return box;
  }

  function errorPanel(message, isOffline) {
    var card = el('div', 'result result--unknown');
    var body = el('div', 'result__body');
    body.appendChild(el('p', 'result__label', isOffline ? 'Backend Service Offline' : 'Recognition unavailable'));
    body.appendChild(el('p', 'result__text', message));
    if (isOffline) {
      body.appendChild(renderApiConnector());
    }
    card.appendChild(body);
    return card;
  }

  /* ── result rendering ─────────────────────────────────────────────────── */

  function section(title, node) {
    if (!node) return null;
    var wrap = el('section', 'result__section');
    wrap.appendChild(el('p', 'result__label', title));
    wrap.appendChild(node);
    return wrap;
  }

  /* ── heritage gallery ──────────────────────────────────────────────────────

     Every frame is a real photograph that exists in this project.  The
     manifest is produced by scripts/prepare_gallery.py from data/raw/, so a
     monument with three photographs yields three frames -- never padding, never
     a stand-in.  Selecting a supporting frame promotes it to the hero. */

  var gallerySites = null;
  var galleryLoading = false;
  var galleryLoadFailed = false;

  function loadGalleryManifest() {
    if (gallerySites || galleryLoading) return Promise.resolve(gallerySites);
    galleryLoading = true;

    var chain = GALLERY_SOURCES.map(function (path) {
      return function (prev) {
        if (prev) return prev;
        return fetch(path)
          .then(function (res) {
            if (!res.ok) throw new Error('bad status ' + res.status);
            return res.json();
          })
          .catch(function () { return null; });
      };
    });

    return chain.reduce(function (p, step) { return p.then(step); }, Promise.resolve())
      .then(function (data) {
        galleryLoading = false;
        if (data && data.sites && typeof data.sites === 'object') {
          gallerySites = data.sites;
        } else {
          gallerySites = {};
          galleryLoadFailed = true;
        }
        return gallerySites;
      });
  }

  /* Real frames for a site_id, newest manifest first, capped at MAX_GALLERY. */
  function galleryFrames(siteId) {
    if (!siteId || !gallerySites) return [];
    var entries = gallerySites[siteId];
    if (!Array.isArray(entries) || !entries.length) return [];
    return entries
      .filter(function (e) { return e && e.src; })
      .slice(0, MAX_GALLERY);
  }

  function buildGallery(frames, altText) {
    if (!frames.length) return null;

    var gallery = el('div', 'gallery');
    gallery.setAttribute('data-count', String(frames.length));

    var viewport = el('div', 'gallery__viewport');
    var track = el('div', 'gallery__track');
    track.setAttribute('role', 'group');
    track.setAttribute('aria-label', altText || 'Heritage photographs');

    frames.forEach(function (frame, i) {
      var item = el('figure', 'gallery__item');
      /* data-frame is the frame's identity in the manifest and never changes;
         DOM position is what promotion moves. */
      item.setAttribute('data-frame', String(i));

      var img = el('img', 'gallery__img');
      img.src = frame.src;
      img.alt = (altText || 'Heritage photograph') + ' — ' + (frame.label || 'photograph ' + (i + 1));
      img.decoding = 'async';
      item.appendChild(img);

      if (frame.label) {
        item.appendChild(el('figcaption', 'gallery__caption', frame.label));
      }
      track.appendChild(item);
    });
    viewport.appendChild(track);
    gallery.appendChild(viewport);

    /* pagination dots -- shown on mobile, where the gallery is a carousel */
    if (frames.length > 1) {
      var dots = el('div', 'gallery__dots');
      dots.setAttribute('role', 'tablist');
      dots.setAttribute('aria-label', 'Select photograph');
      frames.forEach(function (frame, i) {
        var dot = el('button', 'gallery__dot');
        dot.type = 'button';
        dot.setAttribute('data-frame', String(i));
        dot.setAttribute('role', 'tab');
        dot.setAttribute('aria-label', (frame.label || 'Photograph ' + (i + 1)));
        dots.appendChild(dot);
      });
      dots.firstChild.classList.add('is-active');
      dots.firstChild.setAttribute('aria-selected', 'true');
      gallery.appendChild(dots);
    }

    /* supporting strip (desktop). Clicking a frame promotes it to the hero.
       Built from the same frames, so what is clickable is what was fetched. */
    if (frames.length > 1) {
      var strip = el('div', 'gallery__strip');
      strip.setAttribute('role', 'group');
      strip.setAttribute('aria-label', 'Supporting views');

      frames.forEach(function (frame, i) {
        var tile = el('article', 'gallery__tile');
        tile.setAttribute('data-frame', String(i));

        /* An <article> holds the block-level content; a transparent button
           layered over it is the hit target and carries the accessible name. */
        var hit = el('button', 'gallery__hit');
        hit.type = 'button';
        hit.setAttribute('data-select', String(i));
        hit.setAttribute('aria-label',
          'Show ' + (frame.label || 'photograph ' + (i + 1)) + ' as the main view');

        var thumb = el('img', 'gallery__thumb');
        thumb.src = frame.thumb || frame.src;
        thumb.alt = '';
        thumb.loading = 'lazy';
        thumb.decoding = 'async';

        tile.appendChild(thumb);
        tile.appendChild(hit);
        strip.appendChild(tile);
      });

      /* Frame 0 is the hero on first paint, so it must start flagged -- or the
         strip repeats the photograph already shown above it. */
      strip.firstChild.classList.add('is-primary');

      gallery.appendChild(strip);
    }

    return gallery;
  }

  /* Promote a frame to the hero.

     The tile is MOVED in the DOM rather than having its index rewritten: a
     relabelled tile keeps its old photograph, which desynchronises the strip
     from the hero.  The carousel slide is moved to match, so desktop and
     mobile always agree on which frame is showing. */
  function selectGalleryFrame(gallery, frameIndex) {
    if (!gallery) return;
    var track = $('.gallery__track', gallery);
    var strip = $('.gallery__strip', gallery);
    var frame = String(frameIndex);

    function frameOf(node) { return node && node.getAttribute('data-frame'); }

    /* hero: the chosen frame becomes the first child, which is the only one
       the desktop stylesheet reveals. */
    if (track) {
      $$('.gallery__item', track).forEach(function (node) {
        if (frameOf(node) === frame) track.insertBefore(node, track.firstChild);
      });
    }

    /* strip: same frame first, flagged so it is not shown twice */
    if (strip) {
      var tiles = $$('.gallery__tile', strip);
      tiles.forEach(function (tile) {
        var match = frameOf(tile) === frame;
        if (match) strip.insertBefore(tile, strip.firstChild);
        tile.classList.toggle('is-primary', match);
      });
    }

    /* dots follow frame identity, not DOM position */
    $$('.gallery__dot', gallery).forEach(function (dot) {
      var match = frameOf(dot) === frame;
      dot.classList.toggle('is-active', match);
      dot.setAttribute('aria-selected', match ? 'true' : 'false');
    });

    gallery.setAttribute('data-active', frame);

    /* On mobile the hero is the carousel, so scroll it to the chosen frame
       instead of relying on it being first. */
    scrollGalleryTo(gallery, frameIndex);
  }

  /* Bring a frame into view.  Uses scrollIntoView on the slide itself, which
     works for both the desktop hero and the mobile carousel. */
  function scrollGalleryTo(gallery, frameIndex) {
    var frame = String(frameIndex);
    var item = $$('.gallery__item', gallery).filter(function (node) {
      return node.getAttribute('data-frame') === frame;
    })[0];
    if (!item) return;

    var viewport = $('.gallery__viewport', gallery);
    if (viewport && viewport.scrollWidth > viewport.clientWidth + 1) {
      viewport.scrollTo({ left: item.offsetLeft - viewport.offsetLeft, behavior: 'smooth' });
    } else {
      viewport.scrollLeft = 0;
    }
  }

  /* Promote on click of a supporting tile or a pagination dot.  Bound with
     delegation on the card so re-rendering the result cannot leak handlers.
     Only the buttons match: a plain tap on a carousel slide must not reorder
     the track under the visitor's finger. */
  function wireGallery(card) {
    card.addEventListener('click', function (event) {
      var hit = event.target.closest ? event.target.closest('button[data-select], button[data-frame]') : null;
      if (!hit) return;
      var gallery = hit.closest('.gallery');
      if (!gallery) return;
      var index = parseInt(hit.getAttribute('data-select') || hit.getAttribute('data-frame'), 10);
      if (isNaN(index)) return;
      event.preventDefault();
      selectGalleryFrame(gallery, index);
    });

    /* A swipe is not a click, so the pagination dots are synced from the
       carousel's own scroll position.  This only moves the indicator -- it
       never reorders the track, which would fight the gesture. */
    $$('.gallery__viewport', card).forEach(function (viewport) {
      var gallery = viewport.closest('.gallery');
      viewport.addEventListener('scroll', function () {
        var items = $$('.gallery__item', viewport);
        if (items.length < 2) return;

        var box = viewport.getBoundingClientRect();
        var centre = box.left + box.width / 2;
        var nearest = null;
        var nearestDistance = Infinity;

        items.forEach(function (item) {
          var rect = item.getBoundingClientRect();
          var distance = Math.abs((rect.left + rect.width / 2) - centre);
          if (distance < nearestDistance) {
            nearestDistance = distance;
            nearest = item;
          }
        });
        if (!nearest) return;

        var frame = nearest.getAttribute('data-frame');
        $$('.gallery__dot', gallery).forEach(function (dot) {
          var match = dot.getAttribute('data-frame') === frame;
          if (dot.classList.contains('is-active') !== match) {
            dot.classList.toggle('is-active', match);
            dot.setAttribute('aria-selected', match ? 'true' : 'false');
          }
        });
      }, { passive: true });
    });
  }

  function renderResult(data) {
    var card = el('article', 'result');
    var source = data.recognition_source || 'unknown';
    var g = data.global_identification || null;
    var isGemini = source === 'gemini' || source === 'ollama';
    var isGeminiUnknown = isGemini && (!g || g.unknown === true || g.identified === false || !g.site_name);
    var isUnknown = source === 'unknown' || isGeminiUnknown;

    card.classList.add(
      source === 'local' ? 'result--local' : (isGemini && !isGeminiUnknown) ? 'result--global' : 'result--unknown'
    );

    /* banner */
    var banner = el('div', 'result__banner');
    var badgeText =
      source === 'local' ? 'Local Catalogue Identification · Verified'
      : isGemini ? 'External Identification'
      : 'Identification Declined · Inconclusive';
    banner.appendChild(el('span', 'result__badge', badgeText));
    card.appendChild(banner);

    var body = el('div', 'result__body');

    /* --- UNKNOWN / UNIDENTIFIED ---------------------------------------- */
    if (isUnknown) {
      /* No gallery: showing photographs of a monument the backend refused to
         confirm would be presenting an unconfirmed guess as an archive view. */

      var uHead = el('div', 'result__headline');
      uHead.appendChild(el('p', 'result__verdict', 'Identification Declined'));
      uHead.appendChild(el('h3', 'result__name', 'Inconclusive Visual Match'));
      body.appendChild(uHead);

      /* Diagnostic Metrics - transparently display similarity metrics without fabricating percentages */
      var diagWrap = el('div', 'result__metrics');
      diagWrap.style.display = 'flex';
      diagWrap.style.flexWrap = 'wrap';
      diagWrap.style.gap = '1.5rem';
      diagWrap.style.alignItems = 'flex-start';

      var topSim = typeof data.similarity === 'number' ? data.similarity : null;
      if (typeof topSim === 'number' && isFinite(topSim)) {
        var uSim = el('div', 'result__confidence');
        uSim.appendChild(el('p', 'result__label', 'Top CLIP Cosine Similarity'));
        uSim.appendChild(el('p', 'result__confidence-value', topSim.toFixed(4)));
        diagWrap.appendChild(uSim);
      }

      if (typeof data.margin === 'number' && isFinite(data.margin)) {
        var uMargin = el('div', 'result__confidence');
        uMargin.appendChild(el('p', 'result__label', 'Competitor Margin'));
        var uMarginStr = (data.margin >= 0 ? '+' : '') + data.margin.toFixed(4);
        uMargin.appendChild(el('p', 'result__confidence-value', uMarginStr));
        diagWrap.appendChild(uMargin);
      }

      var uGate = el('div', 'result__confidence');
      uGate.appendChild(el('p', 'result__label', 'Open-Set Gate Status'));
      uGate.appendChild(el('p', 'result__confidence-value', 'Declined'));
      diagWrap.appendChild(uGate);

      if (diagWrap.children.length > 0) {
        body.appendChild(diagWrap);
      }

      var uAbout = el('div', 'result__stack');
      var explanation = (g && (g.visual_evidence || g.reason)) ||
        (data.reason ? (REASON_TEXT[data.reason] || data.reason) : null) ||
        'This photograph did not meet the verification thresholds for indexed catalogue monuments (similarity ≥ 0.8500, margin ≥ 0.1000), and external vision fallback did not establish a grounded identification.';
      uAbout.appendChild(el('p', 'result__text', explanation));

      if (g && g.limitations) {
        uAbout.appendChild(field('Limitations', g.limitations));
      }
      if (g && Array.isArray(g.alternatives) && g.alternatives.length) {
        uAbout.appendChild(field('Alternatives considered', g.alternatives.join(', ')));
      }

      body.appendChild(section('Diagnostic Details', uAbout));

      card.appendChild(body);
      resultRegion.innerHTML = '';
      resultRegion.appendChild(card);
      wireGallery(card);
      return;
    }

    /* --- LOCAL --------------------------------------------------------- */
    if (source === 'local') {
      var meta = data.metadata || {};
      var record = catalogueById[data.site_id] || null;

      var frames = galleryFrames(data.site_id);
      var galleryNode = buildGallery(frames, meta.name || 'Heritage photograph');
      if (galleryNode) body.appendChild(galleryNode);

      var lHead = el('div', 'result__headline');
      lHead.appendChild(el('p', 'result__verdict', 'Catalogue Confirmed'));

      var lName = el('h3', 'result__name', meta.name || (record && record.name) || '—');
      lHead.appendChild(lName);

      var place = [meta.location, meta.state, meta.country].filter(Boolean).join(', ');
      if (!place && meta.country) place = meta.country;
      if (!place && record) {
        place = [record.city, record.region, record.country].filter(Boolean).join(', ');
      }
      if (place) lHead.appendChild(el('p', 'result__place', place));
      body.appendChild(lHead);

      /* METRICS -- CLIP Cosine Similarity & Competitor Margin.
         Calibrated probabilities are not displayed because the local catalogue
         dataset size (~40-50 images) is insufficient for cross-validated empirical calibration.
         Instead, transparent raw vector similarity metrics are presented. */
      var metricsWrap = el('div', 'result__metrics');
      metricsWrap.style.display = 'flex';
      metricsWrap.style.flexWrap = 'wrap';
      metricsWrap.style.gap = '1.5rem';
      metricsWrap.style.alignItems = 'flex-start';

      var simVal = typeof data.similarity === 'number' ? data.similarity : data.confidence;
      if (typeof simVal === 'number' && isFinite(simVal)) {
        var simBlock = el('div', 'result__confidence');
        simBlock.appendChild(el('p', 'result__label', 'CLIP Cosine Similarity'));
        simBlock.appendChild(el('p', 'result__confidence-value', simVal.toFixed(4)));
        metricsWrap.appendChild(simBlock);
      }

      if (typeof data.margin === 'number' && isFinite(data.margin)) {
        var mBlock = el('div', 'result__confidence');
        mBlock.appendChild(el('p', 'result__label', 'Competitor Margin'));
        var marginStr = (data.margin >= 0 ? '+' : '') + data.margin.toFixed(4);
        mBlock.appendChild(el('p', 'result__confidence-value', marginStr));
        metricsWrap.appendChild(mBlock);
      }

      var gateBlock = el('div', 'result__confidence');
      gateBlock.appendChild(el('p', 'result__label', 'Decision Boundary'));
      gateBlock.appendChild(el('p', 'result__confidence-value', 'Verified Match'));
      metricsWrap.appendChild(gateBlock);

      if (metricsWrap.children.length > 0) {
        body.appendChild(metricsWrap);
      }

      /* about: catalogue metadata, then enrichment from the local catalogue */
      var about = el('div', 'result__stack');

      var descText = meta.description || (record && record.description) || null;
      if (descText) about.appendChild(field('Description', descText));

      var period = meta.historical_period || (record && record.period) || null;
      if (period) about.appendChild(field('Historical period', period));

      var sig = (record && record.historical_significance) || null;
      if (sig) about.appendChild(field('Historical significance', sig));

      var feats = (record && record.architectural_features) || null;
      if (feats) about.appendChild(field('Architectural features', feats));

      var status = (record && record.heritage_status) || meta.preservation_context || null;
      if (status) about.appendChild(field('Heritage status', status));

      var altName = meta.alternate_name || (record && record.alternate_names && record.alternate_names[0]) || null;
      if (altName) about.appendChild(field('Also known as', altName));

      var aboutSection = section('Recognition Details & Architectural Profile', about.children.length ? about : null);
      if (aboutSection) body.appendChild(aboutSection);

      /* highlights — evidence claims actually returned by the backend */
      var claims = (data.evidence && Array.isArray(data.evidence.relevant_claims) && data.evidence.relevant_claims.length)
        ? data.evidence.relevant_claims
        : (data.evidence && Array.isArray(data.evidence.claims) ? data.evidence.claims : []);
      if (claims && claims.length) {
        var ul = el('ul', 'factlist');
        claims.forEach(function (claim) { ul.appendChild(el('li', null, claim)); });
        body.appendChild(section('Evidence Records & Grounded Claims', ul));
      }

      /* answer, when one was actually grounded */
      if (data.answer && data.is_grounded) {
        body.appendChild(section('Grounded Architectural Synthesis', el('p', 'result__text', data.answer)));
      }

      body.appendChild(section('Evidence Sources & Citations', sourcesBlock(data, record)));

      card.appendChild(body);
      resultRegion.innerHTML = '';
      resultRegion.appendChild(card);
      wireGallery(card);
      return;
    }

    /* --- GOOGLE GEMINI / GLOBAL VISION ---------------------------------------- */
    var g = data.global_identification || {};

    /* The backend deliberately leaves site_id = "unknown" for a global
       identification, so the gallery is keyed off the catalogue instead.  The
       join is an EXACT name match against the record the catalogue already
       holds -- never a fuzzy one, which would attach another monument's
       photographs to this result.  No match means no gallery, not a guess. */
    var gSiteId = matchCatalogueSite(g.site_name);
    var gFrames = galleryFrames(gSiteId);
    var gGallery = buildGallery(gFrames, g.site_name || 'Heritage photograph');
    if (gGallery) body.appendChild(gGallery);

    var gHead = el('div', 'result__headline');
    gHead.appendChild(el('h3', 'result__name', g.site_name || 'Could not identify this monument'));
    var gPlace = [g.city, g.country].filter(Boolean).join(', ') || g.country_or_region || '';
    if (gPlace) gHead.appendChild(el('p', 'result__place', gPlace));
    body.appendChild(gHead);

    /* External Identification: Recognition Score */
    var confBox = el('div', 'result__confidence result__confidence--gemini');

    var confHeader = el('div', 'result__confidence-header');
    confHeader.appendChild(el('p', 'result__label', 'Recognition Score'));

    var rawConf = (typeof g.confidence === 'number' && isFinite(g.confidence) && g.confidence > 0)
      ? g.confidence
      : (typeof data.confidence === 'number' && isFinite(data.confidence) && data.confidence > 0)
      ? data.confidence
      : null;

    if (rawConf != null) {
      // Scale to percentage from actual model estimate; cap at 99% to avoid misleading 100% calibrated certainty claims
      var pctValue = Math.min(99, Math.max(1, Math.round(rawConf * 100)));
      var pctText = pctValue + '%';

      var ratingLabel = 'Low';
      var ratingClass = 'low';
      if (pctValue >= 85) {
        ratingLabel = 'High';
        ratingClass = 'high';
      } else if (pctValue >= 60) {
        ratingLabel = 'Moderate';
        ratingClass = 'moderate';
      }

      confHeader.appendChild(el('span', 'confidence-tag confidence-tag--' + ratingClass, ratingLabel));
      confBox.appendChild(confHeader);

      var confRow = el('div', 'result__confidence-row');
      confRow.appendChild(el('p', 'result__confidence-value', pctText));
      confBox.appendChild(confRow);

      var bar = el('div', 'confidence-bar');
      bar.setAttribute('role', 'progressbar');
      bar.setAttribute('aria-valuenow', String(pctValue));
      bar.setAttribute('aria-valuemin', '0');
      bar.setAttribute('aria-valuemax', '100');

      var barFill = el('div', 'confidence-bar__fill confidence-bar__fill--' + ratingClass);
      barFill.style.width = pctValue + '%';
      bar.appendChild(barFill);
      confBox.appendChild(bar);
    } else {
      confBox.appendChild(confHeader);
      confBox.appendChild(el('p', 'result__confidence-value result__confidence-value--unavailable', 'Score unavailable'));
    }

    var disclaimer = el('p', 'confidence-disclaimer',
      'External visual estimate; not independently verified against the local catalogue.'
    );
    confBox.appendChild(disclaimer);
    body.appendChild(confBox);

    var gAbout = el('div', 'result__stack');
    if (g.significance) gAbout.appendChild(field('Significance', g.significance));
    if (g.historical_period) gAbout.appendChild(field('Historical period', g.historical_period));
    if (g.architectural_style) gAbout.appendChild(field('Architectural style', g.architectural_style));
    if (g.founder_built_by) gAbout.appendChild(field('Built by', g.founder_built_by));
    if (g.uncertainty) gAbout.appendChild(field('Uncertainty', g.uncertainty));
    if (g.limitations) gAbout.appendChild(field('Limitations', g.limitations));
    if (Array.isArray(g.alternatives) && g.alternatives.length) {
      gAbout.appendChild(field('Alternatives considered', g.alternatives.join(', ')));
    }
    var gAboutSection = section('Architectural Profile', gAbout.children.length ? gAbout : null);
    if (gAboutSection) body.appendChild(gAboutSection);

    var visualExp = g.visual_evidence || g.reason;
    if (visualExp) body.appendChild(section('Visual Feature Analysis', el('p', 'result__text', visualExp)));

    if (Array.isArray(g.interesting_facts) && g.interesting_facts.length) {
      var gFacts = el('ul', 'factlist');
      g.interesting_facts.forEach(function (f) {
        if (f) gFacts.appendChild(el('li', null, String(f)));
      });
      if (gFacts.children.length) body.appendChild(section('Additional Heritage Context', gFacts));
    }

    /* Answer to optional question, clearly distinguishing visual answers from grounded answers */
    if (data.answer) {
      var ansWrap = el('div', 'result__stack');
      ansWrap.appendChild(el('p', 'result__text', data.answer));
      ansWrap.appendChild(el('p', 'source__note', 'Model-generated synthesis based on visual identification — not independently verified against catalogue evidence records.'));
      body.appendChild(section('Multimodal Vision Synthesis', ansWrap));
    }

    /* Sources: the backend deliberately returns a label with no URL here. */
    var srcWrap = el('div', 'sources');
    var hasRealSource = false;
    if (Array.isArray(data.citations)) {
      data.citations.forEach(function (citation) {
        if (citation && citation.source_url) hasRealSource = true;
      });
    }
    if (hasRealSource) {
      data.citations.forEach(function (citation) {
        if (!citation) return;
        srcWrap.appendChild(sourceNode(citation));
      });
    } else {
      var note = el('div', 'source');
      note.appendChild(el('span', 'source__name', 'External Recognition'));
      note.appendChild(el('span', 'source__note',
        'This identification was produced by an external service and has not been verified against the local catalogue.'));
      srcWrap.appendChild(note);
    }
    body.appendChild(section('Verification Status', srcWrap));

    card.appendChild(body);
    resultRegion.innerHTML = '';
    resultRegion.appendChild(card);
    wireGallery(card);
  }

  /* Exact catalogue name -> site_id.

     The vision model names a place in its own words, which is not always the
     string the catalogue files it under.  Only renames verified by hand are
     listed here; everything else must match a catalogue name exactly, and an
     unmatched name yields null so the caller renders no gallery.  A fuzzy
     match would happily attach a different monument's photographs to this
     result, which is worse than showing none.

     Verified: the photograph the model reports as "Medina of Algiers" is the
     Casbah -- the old city of Algiers -- which the catalogue files under
     site_id `category_casbah_of_algiers_algeria`.  That site_id is also the
     folder the project's own copy of the photograph lives in. */
  var CATALOGUE_NAME_ALIASES = {
    'medina of algiers': 'category_casbah_of_algiers_algeria'
  };

  function matchCatalogueSite(name) {
    if (!name) return null;
    var wanted = String(name).trim().toLowerCase();
    if (!wanted) return null;

    if (Object.prototype.hasOwnProperty.call(CATALOGUE_NAME_ALIASES, wanted)) {
      return CATALOGUE_NAME_ALIASES[wanted];
    }

    if (!Array.isArray(catalogue)) return null;
    for (var i = 0; i < catalogue.length; i++) {
      var rec = catalogue[i];
      if (rec && rec.site_id && String(rec.name || '').trim().toLowerCase() === wanted) {
        return rec.site_id;
      }
    }
    return null;
  }

  function metric(key, value) {
    var wrap = el('div', 'metric');
    wrap.appendChild(el('span', 'metric__k', key));
    wrap.appendChild(el('span', 'metric__v', value === null || value === undefined || value === '' ? '—' : String(value)));
    return wrap;
  }

  function sourceNode(citation) {
    var wrap = el('div', 'source');
    wrap.appendChild(el('span', 'source__name', citation.source_name || 'Untitled source'));
    if (citation.source_url) {
      var link = el('a', 'source__url', citation.source_url);
      link.href = citation.source_url;
      link.target = '_blank';
      link.rel = 'noopener noreferrer';
      wrap.appendChild(link);
    } else if (citation.note) {
      wrap.appendChild(el('span', 'source__note', citation.note));
    }
    return wrap;
  }

  function sourcesBlock(data, record) {
    var wrap = el('div', 'sources');
    var seenUrl = {};
    var seenName = {};

    function key(value) { return String(value || '').trim().toLowerCase(); }

    function add(name, url, note) {
      var kUrl = key(url);
      var kName = key(name);
      if (kUrl && seenUrl[kUrl]) return;
      if (kName && seenName[kName]) return;
      if (kUrl) seenUrl[kUrl] = true;
      if (kName) seenName[kName] = true;
      wrap.appendChild(sourceNode({ source_name: name, source_url: url, note: note }));
    }

    // catalogue sources for this site, when the record exists
    if (record && Array.isArray(record.sources)) {
      record.sources.forEach(function (source) {
        if (source) add(source.title, source.url);
      });
    }

    // citations returned by the backend
    if (Array.isArray(data.citations)) {
      data.citations.forEach(function (citation) {
        if (citation) add(citation.source_name, citation.source_url);
      });
    }

    // evidence source names that did not arrive with a URL of their own
    if (data.evidence && Array.isArray(data.evidence.source_names)) {
      data.evidence.source_names.forEach(function (name) {
        if (name) add(name, null, 'Cited in the evidence record');
      });
    }

    if (!wrap.children.length) {
      var none = el('div', 'source');
      none.appendChild(el('span', 'source__name', 'No sources recorded'));
      wrap.appendChild(none);
    }
    return wrap;
  }

  /* ── catalogue + explorer ─────────────────────────────────────────────── */

  var catalogue = [];
  var catalogueById = {};
  var catalogueLoading = false;
  var catalogueErrored = false;
  var rendered = 0;

  var searchInput, regionSelect, countrySelect, typeSelect, grid, emptyState, loadMore, countLabel, catError;

  function loadCatalogue() {
    if (catalogueLoading || catalogue.length) return Promise.resolve(catalogue);
    catalogueLoading = true;
    countLabel.textContent = 'Loading catalogue…';

    var chain = CATALOGUE_SOURCES.map(function (path) {
      return function (prev) {
        if (prev) return prev;
        return fetch(path)
          .then(function (res) {
            if (!res.ok) throw new Error('bad status ' + res.status);
            return res.json();
          })
          .catch(function () { return null; });
      };
    });

    return chain.reduce(function (p, step) { return p.then(step); }, Promise.resolve())
      .then(function (data) {
        catalogueLoading = false;
        if (!Array.isArray(data)) {
          catalogueErrored = true;
          countLabel.textContent = 'Catalogue unavailable';
          catError.textContent =
            'The monument catalogue could not be loaded. Serve this folder over HTTP ' +
            '(python -m http.server 8080) rather than opening the file directly, then reload.';
          catError.hidden = false;
          return [];
        }

        catalogue = data;
        catalogue.forEach(function (record) {
          if (record && record.site_id) catalogueById[record.site_id] = record;
        });

        populateFilters();
        // The card image manifest must resolve before the grid paints, or every
        // card would briefly render the architectural placeholder and then swap
        // to a photograph.  Failure here is non-fatal: placeholders simply stay.
        return loadMonumentImages()
          .catch(function () { return null; })
          .then(function () {
            applyFilters();
            setHealthPanel(health);
            return catalogue;
          });
      });
  }

  function populateFilters() {
    var regions = uniq(catalogue.map(function (r) { return r.region; }));
    var countries = uniq(catalogue.map(function (r) { return r.country; }));
    var types = uniq(catalogue.map(function (r) { return r.type; }));

    fillSelect(regionSelect, regions, 'All regions');
    fillSelect(countrySelect, countries, 'All countries');
    fillSelect(typeSelect, types, 'All types');
  }

  function fillSelect(select, values, allLabel) {
    values.sort().forEach(function (value) {
      var option = el('option', null, value);
      option.value = value;
      select.appendChild(option);
    });
    select.options[0].textContent = allLabel;
  }

  function uniq(list) {
    var seen = {};
    var out = [];
    list.forEach(function (value) {
      if (!value) return;
      if (seen[value]) return;
      seen[value] = true;
      out.push(value);
    });
    return out;
  }

  function matchesFilters(record, query, region, country, type) {
    if (region && record.region !== region) return false;
    if (country && record.country !== country) return false;
    if (type && record.type !== type) return false;
    if (!query) return true;

    var haystack = [
      record.name,
      record.city,
      record.country,
      record.type,
      record.region,
      (record.alternate_names || []).join(' ')
    ].filter(Boolean).join(' ').toLowerCase();

    return query.toLowerCase().split(/\s+/).every(function (token) {
      return haystack.indexOf(token) !== -1;
    });
  }

  var debouncedTrackFilter = debounce(function (queryLen, region, country, type) {
    trackEvent('catalogue_filter', {
      query_length: queryLen,
      has_region: Boolean(region),
      has_country: Boolean(country),
      has_type: Boolean(type)
    });
  }, 600);

  function applyFilters() {
    var query = (searchInput.value || '').trim();
    debouncedTrackFilter(query.length, regionSelect.value, countrySelect.value, typeSelect.value);
    var filtered = catalogue.filter(function (record) {
      return matchesFilters(record, query, regionSelect.value, countrySelect.value, typeSelect.value);
    });

    rendered = Math.min(PAGE_SIZE, filtered.length);
    grid.innerHTML = '';
    for (var i = 0; i < rendered; i++) grid.appendChild(card(filtered[i], i));

    emptyState.hidden = filtered.length !== 0;
    loadMore.hidden = filtered.length <= rendered;
    loadMore.dataset.remaining = String(filtered.length - rendered);

    countLabel.textContent =
      filtered.length + ' of ' + catalogue.length + ' monuments';
  }

  /* Real photographs that ship with this project, one thumbnail per site, in
     assets/images/sites/.  Listing them explicitly keeps the grid from firing a
     request (and a 404) for every one of the 455 records.  These are the
     project's own indexed photographs, so they always win over a downloaded
     image. */
  var SITE_IMAGES = {
    ajanta_caves: 1, jama_masjid: 1, konark_sun_temple: 1,
    qutub_minar: 1, red_fort: 1, taj_mahal: 1
  };

  /* site_id -> card image path, from the downloaded-image manifest.  Null until
     the manifest resolves; the resolver returns null in that window and the
     caller paints the architectural placeholder, so nothing flashes a broken
     image while it loads. */
  var monumentImages = null;
  var monumentImagesLoading = false;

  function loadMonumentImages() {
    if (monumentImages || monumentImagesLoading) return Promise.resolve(monumentImages);
    monumentImagesLoading = true;

    var chain = MONUMENT_IMAGE_SOURCES.map(function (path) {
      return function (prev) {
        if (prev) return prev;
        return fetch(path)
          .then(function (res) {
            if (!res.ok) throw new Error('bad status ' + res.status);
            return res.json();
          })
          .catch(function () { return null; });
      };
    });

    return chain.reduce(function (p, step) { return p.then(step); }, Promise.resolve())
      .then(function (data) {
        monumentImagesLoading = false;
        var images = data && data.images && typeof data.images === 'object'
          ? data.images : {};
        // Keep only entries whose file really is on disk per the manifest, so a
        // stale manifest can never produce a 404 in the grid.
        var resolved = {};
        Object.keys(images).forEach(function (siteId) {
          var entry = images[siteId];
          if (entry && entry.card) resolved[siteId] = entry.card;
        });
        if (!Object.keys(resolved).length) {
          // No manifest, or an empty one: every monument without a local
          // photograph keeps its architectural placeholder.
          monumentImages = {};
          return monumentImages;
        }
        monumentImages = resolved;
        return monumentImages;
      })
      .catch(function () {
        monumentImagesLoading = false;
        monumentImages = {};
        return monumentImages;
      });
  }

  /* Local photograph first, then the downloaded image, then null.  Null is a
     real answer: it means "no image", and the caller must draw the
     architectural placeholder rather than a monogram or a broken image. */
  function siteImage(siteId) {
    if (!siteId) return null;
    if (SITE_IMAGES[siteId]) return 'assets/images/sites/' + siteId + '.webp';
    if (monumentImages && monumentImages[siteId]) return monumentImages[siteId];
    return null;
  }

  function card(record, index) {
    // An <article> rather than a <button>: the card contains a heading and
    // paragraphs, which are not valid inside a button. The overlay button
    // below carries the action and the accessible name.
    var node = el('article', 'card');
    node.setAttribute('data-site', record.site_id);

    var media = el('div', 'card__media');
    var src = siteImage(record.site_id);
    if (src) {
      var img = el('img');
      img.src = src;
      img.alt = 'Photograph of ' + (record.name || 'heritage monument');
      img.loading = 'lazy';
      /* A file that fails to load must land on the same architectural
         placeholder as a monument that has no image at all. */
      img.addEventListener('error', function () {
        img.remove();
        if (!media.querySelector('.card__placeholder')) {
          media.appendChild(el('span', 'card__placeholder', ''));
        }
      });
      media.appendChild(img);
    }
    /* No photograph: a clean architectural placeholder, drawn in CSS. Never a
       monogram of the first two letters - it read as a missing asset rather
       than a considered empty state. */
    if (!src) media.appendChild(el('span', 'card__placeholder', ''));
    media.appendChild(el('span', 'card__index', String(index + 1).padStart(2, '0')));
    if (record.type) media.appendChild(el('span', 'card__type', record.type));
    node.appendChild(media);

    var body = el('div', 'card__body');
    body.appendChild(el('h3', 'card__name', record.name || 'Untitled'));
    var place = [record.city, record.country].filter(Boolean).join(', ');
    if (place) body.appendChild(el('p', 'card__place', place));
    if (record.period) body.appendChild(el('p', 'card__period', record.period));
    if (record.description) body.appendChild(el('p', 'card__desc', record.description));

    var cta = el('p', 'card__cta');
    cta.appendChild(el('span', null, 'Explore'));
    cta.appendChild(el('span', null, '→'));
    body.appendChild(cta);
    node.appendChild(body);

    var trigger = el('button', 'card__trigger');
    trigger.type = 'button';
    trigger.setAttribute('aria-label', 'Explore ' + (record.name || 'this monument'));
    trigger.addEventListener('click', function () { openDetail(record.site_id); });
    node.appendChild(trigger);

    // staggered reveal, skipped entirely under reduced motion
    if (!reducedMotion()) {
      node.style.animationDelay = Math.min(index, 12) * 45 + 'ms';
      node.classList.add('is-in');
    } else {
      node.classList.add('is-in');
    }

    return node;
  }

  function initExplorer() {
    searchInput = $('#search');
    regionSelect = $('#filter-region');
    countrySelect = $('#filter-country');
    typeSelect = $('#filter-type');
    grid = $('#monument-grid');
    emptyState = $('#empty-state');
    loadMore = $('#load-more');
    countLabel = $('#her-count');
    catError = $('#catalogue-error');

    [searchInput, regionSelect, countrySelect, typeSelect].forEach(function (control) {
      control.addEventListener('input', applyFilters);
      control.addEventListener('change', applyFilters);
    });

    $('#reset-filters').addEventListener('click', function () {
      searchInput.value = '';
      regionSelect.value = '';
      countrySelect.value = '';
      typeSelect.value = '';
      applyFilters();
      searchInput.focus();
    });

    loadMore.addEventListener('click', function () {
      var remaining = parseInt(loadMore.dataset.remaining || '0', 10);
      if (!remaining) return;
      var query = (searchInput.value || '').trim();
      var filtered = catalogue.filter(function (record) {
        return matchesFilters(record, query, regionSelect.value, countrySelect.value, typeSelect.value);
      });
      var start = rendered;
      var end = Math.min(start + PAGE_SIZE, filtered.length);
      for (var i = start; i < end; i++) grid.appendChild(card(filtered[i], i));
      rendered = end;
      loadMore.hidden = filtered.length <= rendered;
      loadMore.dataset.remaining = String(filtered.length - rendered);
    });

    $('#back-to-heritage').addEventListener('click', function () { showView('heritage'); });

    // catalogue may be deep-linked via #heritage/<site_id>
    var parts = location.hash.slice(1).split('/');
    if (parts[0] === 'heritage' && parts[1]) {
      loadCatalogue().then(function () { openDetail(parts[1]); });
    }
  }

  /* ── monument detail ─────────────────────────────────────────────────── */

  function openDetail(siteId) {
    var record = catalogueById[siteId];
    if (!record) {
      showView('heritage');
      return;
    }

    trackEvent('monument_detail_view', { site_id: siteId, name: record.name });

    var root = $('#detail-root');
    root.innerHTML = '';

    /* hero */
    var hero = el('div', 'detail__hero');
    var src = siteImage(record.site_id);
    if (src) {
      var img = el('img');
      img.src = src;
      img.alt = record.name;
      img.addEventListener('error', function () { img.remove(); });
      hero.appendChild(img);
    }
    var heroBody = el('div', 'detail__hero-body');
    heroBody.appendChild(el('p', 'eyebrow', 'Monument record'));
    heroBody.appendChild(el('h2', 'detail__name', record.name || 'Untitled'));
    var place = [record.city, record.country].filter(Boolean).join(' / ');
    if (place) heroBody.appendChild(el('p', 'detail__place', place));
    hero.appendChild(heroBody);
    root.appendChild(hero);

    /* tags */
    var tags = el('div', 'detail__tags');
    if (record.type) tags.appendChild(el('span', 'tag tag--accent', record.type));
    if (record.region) tags.appendChild(el('span', 'tag', record.region));
    if (record.heritage_status) tags.appendChild(el('span', 'tag', record.heritage_status));
    if (record.country_code) tags.appendChild(el('span', 'tag', record.country_code));
    if (tags.children.length) root.appendChild(tags);

    /* columns — only fields the record actually carries */
    var cols = el('div', 'detail__cols');

    cols.appendChild(detailSection('Description', record.description));
    cols.appendChild(detailSection('Historical period', record.period));
    cols.appendChild(detailSection('Historical significance', record.historical_significance));
    cols.appendChild(detailSection('Architectural features', record.architectural_features));

    var statusWrap = detailSection('Heritage status', record.heritage_status);
    if (statusWrap) {
      var coord = [];
      if (typeof record.latitude === 'number' && typeof record.longitude === 'number') {
        coord.push(record.latitude.toFixed(4) + ', ' + record.longitude.toFixed(4));
      }
      if (coord.length) statusWrap.appendChild(el('p', 'detail__coord', coord.join(' · ')));
      if (record.wikidata_id) statusWrap.appendChild(el('p', 'detail__coord', 'Wikidata: ' + record.wikidata_id));
      if (record.commons_id) statusWrap.appendChild(el('p', 'detail__coord', 'Commons: ' + record.commons_id));
    }
    cols.appendChild(statusWrap);

    if (record.alternate_names && record.alternate_names.length) {
      cols.appendChild(detailSection('Also known as', record.alternate_names.join(', ')));
    }

    // Built directly rather than via detailSection(), which requires a value:
// this section holds a list of links, not a paragraph.
    var sources = el('section', 'detail__section');
    sources.appendChild(el('h3', 'detail__title', 'Sources'));
    var sourceList = el('div', 'sources');
    if (Array.isArray(record.sources) && record.sources.length) {
      record.sources.forEach(function (source) {
        if (source) sourceList.appendChild(sourceNode({ source_name: source.title, source_url: source.url }));
      });
    } else {
      sourceList.appendChild(el('p', 'detail__text', 'No sources recorded in the catalogue for this monument.'));
    }
    sources.appendChild(sourceList);
    cols.appendChild(sources);

    root.appendChild(cols);
    showView('detail');
    if (record.name) {
      document.title = record.name + ' — Architectural Profile | Heritage Discovery';
    }
    history.replaceState(null, '', '#heritage/' + record.site_id);
  }

  function detailSection(title, text) {
    if (!text || !String(text).trim()) return null;
    var wrap = el('section', 'detail__section');
    wrap.appendChild(el('h3', 'detail__title', title));
    wrap.appendChild(el('p', 'detail__text', String(text)));
    return wrap;
  }

  /* ── scroll progress indicator ─────────────────────────────────────────── */

  function initScrollProgress() {
    var progressBar = $('#scroll-progress-bar');
    if (!progressBar) return;

    var ticking = false;

    function update() {
      var winScroll = window.scrollY || document.documentElement.scrollTop || 0;
      var height = document.documentElement.scrollHeight - document.documentElement.clientHeight;
      var scrolled = height > 0 ? (winScroll / height) * 100 : 0;
      if (scrolled > 100) scrolled = 100;
      if (scrolled < 0) scrolled = 0;
      progressBar.style.width = scrolled.toFixed(2) + '%';
      ticking = false;
    }

    window.addEventListener('scroll', function () {
      if (!ticking) {
        window.requestAnimationFrame(update);
        ticking = true;
      }
    }, { passive: true });

    window.addEventListener('resize', function () {
      if (!ticking) {
        window.requestAnimationFrame(update);
        ticking = true;
      }
    }, { passive: true });

    update();
  }

  /* ── cinematic loader ─────────────────────────────────────────────────── */

  var loaderMessages = [
    'Initializing vector index & evidence repository',
    'Calibrating visual feature embeddings',
    'Configuring open-set decision boundaries',
    'Loading architectural monument catalogue'
  ];
  var loaderMessageIndex = 0;
  var loaderMessageTimer = null;
  var loaderElement = null;
  var loaderBar = null;
  var loaderMessageEl = null;

  function initLoader() {
    loaderElement = document.getElementById('loader-overlay');
    loaderBar = document.getElementById('loader-bar');
    loaderMessageEl = document.getElementById('loader-message');
    if (!loaderElement) return;

    // Cycle through loading messages
    loaderMessageTimer = window.setInterval(function () {
      loaderMessageIndex = (loaderMessageIndex + 1) % loaderMessages.length;
      if (loaderMessageEl) {
        loaderMessageEl.style.opacity = '0';
        loaderMessageEl.style.transition = 'opacity 0.4s cubic-bezier(.22, .61, .36, 1)';
        window.setTimeout(function () {
          loaderMessageEl.textContent = loaderMessages[loaderMessageIndex];
          loaderMessageEl.style.opacity = '1';
        }, 400);
      }
    }, 1800);

    // Dynamic progress bar animation
    if (loaderBar) {
      var progress = 0;
      var progressInterval = window.setInterval(function () {
        if (!loaderElement || loaderElement.classList.contains('is-hidden')) {
          window.clearInterval(progressInterval);
          return;
        }
        progress = Math.min(progress + (Math.random() * 12 + 6), 92);
        loaderBar.style.width = progress.toFixed(1) + '%';
      }, 180);
    }
  }

  function hideLoader() {
    if (!loaderElement || loaderElement.classList.contains('is-hidden')) return;
    if (loaderMessageTimer) {
      window.clearInterval(loaderMessageTimer);
      loaderMessageTimer = null;
    }

    // Complete the progress bar smoothly
    if (loaderBar) {
      loaderBar.style.transition = 'width 0.35s cubic-bezier(.22, .61, .36, 1)';
      loaderBar.style.width = '100%';
    }

    // Fade out after a brief delay
    window.setTimeout(function () {
      loaderElement.classList.add('is-hidden');
      loaderElement.setAttribute('aria-hidden', 'true');
    }, 380);
  }

  /* ── privacy, legal & consent management ───────────────────────────────── */

  var LEGAL_DOCS = {
    privacy: {
      eyebrow: 'Institutional Governance',
      title: 'Institutional Privacy Policy',
      content: '<div class="legal-doc">' +
        '<div class="legal-doc__meta"><strong>Governance Framework:</strong> Academic Demonstration · <strong>Effective:</strong> October 2026 · <strong>Scope:</strong> Visual Heritage Recognition & Cultural Discovery Platform</div>' +
        '<p>The Visual Heritage Recognition Platform is an educational and cultural research service dedicated to architectural monument preservation. We operate under a strict philosophy of data minimization and ephemeral in-memory processing.</p>' +
        '<h3>1. Zero-Retention Photographic Processing</h3>' +
        '<p>Photographs submitted via the Identification Console are held ephemerally in volatile memory solely for mathematical vector feature encoding (CLIP 512-dimensional embedding). Uploaded imagery is:</p>' +
        '<ul>' +
        '<li><strong>Never written to persistent storage</strong>, databases, or cloud object stores.</li>' +
        '<li><strong>Never reused for training</strong> or fine-tuning commercial machine learning models without express written institutional consent.</li>' +
        '<li><strong>Discarded immediately</strong> after index similarity comparison completes.</li>' +
        '</ul>' +
        '<h3>2. Local Browser Storage &amp; Cookies</h3>' +
        '<p>The platform does not employ tracking cookies, marketing beacons, or cross-site fingerprinting scripts. We store strictly essential interface preferences (such as your cookie consent selection) in browser <code>localStorage</code> under the key <code>heritage_cookie_consent</code>.</p>' +
        '<h3>3. Anonymous Performance Telemetry</h3>' +
        '<p>If you explicitly grant permission for performance telemetry, anonymous non-identifiable interaction signals (such as view navigation and recognition pipeline latency) are recorded to evaluate retrieval accuracy. These signals contain no IP addresses, geolocation data, personal credentials, or photographic bytes.</p>' +
        '<h3>4. External Inference Disclosures</h3>' +
        '<p>When a query image does not match the verified local catalogue threshold (similarity &ge; 0.85, competitor margin &ge; 0.10), an external vision reasoning service may be queried as an exploratory fallback. Such requests transmit only the ephemeral image bytes; no user identity, session token, or telemetry is shared.</p>' +
        '<h3>5. Preference Updates &amp; Contact</h3>' +
        '<p>You may inspect, modify, or revoke your consent preferences at any time by selecting "Cookie Preferences" in the page footer or by clearing your browser cache. For academic inquiries regarding our privacy standards, contact the project maintainers.</p>' +
        '</div>'
    },
    terms: {
      eyebrow: 'Platform Protocols',
      title: 'Terms & Conditions of Exploration',
      content: '<div class="legal-doc">' +
        '<div class="legal-doc__meta"><strong>Operating Edition:</strong> Academic & Research Demonstration · <strong>Effective:</strong> October 2026</div>' +
        '<p>By accessing the Visual Heritage Recognition Platform, you agree to engage with the system under the ethical research and cultural preservation terms outlined below.</p>' +
        '<h3>1. Purpose &amp; Academic Scope</h3>' +
        '<p>This platform is an open-access cultural discovery engine combining open-clip vision embeddings with official historical records. It is intended for educational, academic, and cultural research purposes.</p>' +
        '<h3>2. Grounded vs. External Verification</h3>' +
        '<p>The platform clearly distinguishes between two levels of certainty:</p>' +
        '<ul>' +
        '<li><strong>Verified Catalogue Identifications:</strong> Rigorously matched against our local FAISS vector catalogue with validated cosine similarity (&ge; 0.85) and competitor margin (&ge; 0.10), grounded in official Archaeological Survey of India (ASI) and UNESCO records.</li>' +
        '<li><strong>External Identifications:</strong> Generated via external vision inference models when no local match meets verified thresholds. External scores represent exploratory assessments and must not be interpreted as certified architectural facts.</li>' +
        '</ul>' +
        '<h3>3. Acceptable Use Policy</h3>' +
        '<p>Users agree not to submit abusive, unlawful, or intentionally deceptive imagery to the recognition engine. Automated scraping or denial-of-service attempts against the inference endpoints are strictly prohibited.</p>' +
        '<h3>4. Intellectual Property &amp; Citations</h3>' +
        '<p>Historical records, architectural descriptions, and reference photographs are curated from public cultural databases, UNESCO World Heritage documentation, and the Archaeological Survey of India under academic fair dealing principles. Proper attribution must accompany any research citation derived from this system.</p>' +
        '<h3>5. Disclaimer of Warranty</h3>' +
        '<p>The platform is provided "as is" without warranty of continuous uptime or definitive architectural certification. Users are encouraged to cross-reference findings with primary archaeological documentation for authoritative research.</p>' +
        '</div>'
    }
  };

  function initLegalAndConsent() {
    var cookieBanner = $('#cookie-banner');
    var cookieModal = $('#cookie-modal');
    var legalModal = $('#legal-modal');
    var analyticsToggle = $('#pref-analytics-toggle');
    var lastModalFocus = null;

    function getConsent() {
      try {
        var raw = localStorage.getItem('heritage_cookie_consent');
        return raw ? JSON.parse(raw) : null;
      } catch (e) {
        return null;
      }
    }

    function saveConsent(analyticsAllowed) {
      try {
        var record = {
          essential: true,
          analytics: Boolean(analyticsAllowed),
          timestamp: new Date().toISOString()
        };
        localStorage.setItem('heritage_cookie_consent', JSON.stringify(record));
        if (analyticsToggle) analyticsToggle.checked = Boolean(analyticsAllowed);
      } catch (e) {}
    }

    // Initialize banner state based on existing consent
    var currentConsent = getConsent();
    if (cookieBanner) {
      if (currentConsent) {
        cookieBanner.hidden = true;
        if (analyticsToggle) analyticsToggle.checked = Boolean(currentConsent.analytics);
      } else {
        cookieBanner.hidden = false;
        if (analyticsToggle) analyticsToggle.checked = false;
      }
    }

    // Modal helpers
    function openModal(modalEl) {
      if (!modalEl) return;
      lastModalFocus = document.activeElement;
      modalEl.hidden = false;
      document.body.style.overflow = 'hidden';
      var focusTarget = modalEl.querySelector('.modal-close') || modalEl.querySelector('button');
      if (focusTarget) focusTarget.focus();
    }

    function closeModal(modalEl) {
      if (!modalEl || modalEl.hidden) return;
      modalEl.hidden = true;
      if (cookieModal.hidden && legalModal.hidden && (!views.detail || views.detail.hidden)) {
        document.body.style.overflow = '';
      }
      if (lastModalFocus && typeof lastModalFocus.focus === 'function') {
        lastModalFocus.focus();
        lastModalFocus = null;
      }
    }

    function openLegalDoc(type) {
      var doc = LEGAL_DOCS[type];
      if (!doc || !legalModal) return;
      var eyebrow = $('#legal-modal-eyebrow');
      var title = $('#legal-modal-title');
      var content = $('#legal-modal-content');
      if (eyebrow) eyebrow.textContent = doc.eyebrow;
      if (title) title.textContent = doc.title;
      if (content) content.innerHTML = doc.content;
      openModal(legalModal);
      trackEvent('legal_document_viewed', { document: type });
    }

    // Banner buttons
    var acceptAllBtn = $('#cookie-accept-all');
    if (acceptAllBtn) {
      acceptAllBtn.addEventListener('click', function () {
        saveConsent(true);
        if (cookieBanner) cookieBanner.hidden = true;
        trackEvent('consent_updated', { analytics: true, mode: 'accept_all' });
      });
    }

    var essentialOnlyBtn = $('#cookie-essential-only');
    if (essentialOnlyBtn) {
      essentialOnlyBtn.addEventListener('click', function () {
        saveConsent(false);
        if (cookieBanner) cookieBanner.hidden = true;
        trackEvent('consent_updated', { analytics: false, mode: 'essential_only' });
      });
    }

    var customizeBtn = $('#cookie-customize');
    if (customizeBtn) {
      customizeBtn.addEventListener('click', function () {
        openModal(cookieModal);
      });
    }

    // Footer buttons
    var footerCookiesBtn = $('#footer-cookies-btn');
    if (footerCookiesBtn) {
      footerCookiesBtn.addEventListener('click', function () {
        openModal(cookieModal);
      });
    }

    var footerPrivacyBtn = $('#footer-privacy-btn');
    if (footerPrivacyBtn) {
      footerPrivacyBtn.addEventListener('click', function () {
        openLegalDoc('privacy');
      });
    }

    var footerTermsBtn = $('#footer-terms-btn');
    if (footerTermsBtn) {
      footerTermsBtn.addEventListener('click', function () {
        openLegalDoc('terms');
      });
    }

    // Save preferences from preferences modal
    var savePrefsBtn = $('#cookie-save-prefs');
    if (savePrefsBtn) {
      savePrefsBtn.addEventListener('click', function () {
        var allowed = analyticsToggle ? analyticsToggle.checked : false;
        saveConsent(allowed);
        closeModal(cookieModal);
        if (cookieBanner) cookieBanner.hidden = true;
        trackEvent('consent_updated', { analytics: allowed, mode: 'custom_preferences' });
      });
    }

    // Close buttons and scrim clicks for both modals
    $$('[data-close-modal="cookie"]').forEach(function (el) {
      el.addEventListener('click', function () {
        closeModal(cookieModal);
      });
    });

    $$('[data-close-modal="legal"]').forEach(function (el) {
      el.addEventListener('click', function () {
        closeModal(legalModal);
      });
    });

    // Global keyboard listener for closing modals with Escape
    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape' || e.key === 'Esc') {
        if (cookieModal && !cookieModal.hidden) {
          closeModal(cookieModal);
        } else if (legalModal && !legalModal.hidden) {
          closeModal(legalModal);
        }
      }
    });

    // Simple accessible focus trapping within modals
    [cookieModal, legalModal].forEach(function (modal) {
      if (!modal) return;
      modal.addEventListener('keydown', function (e) {
        if (e.key !== 'Tab') return;
        var focusables = modal.querySelectorAll('button:not([disabled]), [href], input:not([disabled]), [tabindex]:not([tabindex="-1"])');
        if (focusables.length === 0) return;
        var first = focusables[0];
        var last = focusables[focusables.length - 1];
        if (e.shiftKey && document.activeElement === first) {
          e.preventDefault();
          last.focus();
        } else if (!e.shiftKey && document.activeElement === last) {
          e.preventDefault();
          first.focus();
        }
      });
    });
  }

  function initDockConfig() {
    var dockSystem = $('#dock-system');
    if (!dockSystem) return;
    dockSystem.style.cursor = 'pointer';
    dockSystem.addEventListener('click', function () {
      var current = API_BASE || '';
      var entered = window.prompt(
        'Configure Heritage Backend API URL:\n(e.g., https://your-backend.onrender.com or https://....ngrok-free.app)',
        current
      );
      if (entered !== null) {
        setApiBase(entered.trim());
      }
    });
  }

  /* ── boot ─────────────────────────────────────────────────────────────── */

  function init() {
    document.body.classList.add('js-ready');
    initLoader();
    initScrollProgress();
    initSlideshow();
    initRouter();
    initScrollSpy();
    initMenu();
    initChapters();
    initParallax();
    initCursor();
    initStoryline();
    initUpload();
    initExplorer();
    initLegalAndConsent();
    initDockConfig();

    refreshHealth();
    loadGalleryManifest();
    loadCatalogue();
    booted = true;

    // Smooth reveal timeout allowing architectural line art and grid to render
    window.setTimeout(hideLoader, 1100);
    // Hard ceiling safety timeout to ensure interface is never blocked
    window.setTimeout(hideLoader, 2500);
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init);
  else init();
})();