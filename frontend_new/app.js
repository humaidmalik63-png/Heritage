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

  var API_BASE =
    (document.documentElement.getAttribute('data-api-base') || '').replace(/\/$/, '') ||
    (location.protocol === 'file:' ? 'http://localhost:8000' : location.protocol + '//' + location.hostname + ':8000');

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
    low_similarity: 'No indexed image was similar enough to accept.',
    no_evidence: 'The site was matched, but no evidence record is stored for it.',
    non_heritage: 'The place identified does not appear to be a heritage monument.',
    answer_declined: 'The grounded answer was declined.',
    ungrounded_answer: 'The generated answer was not grounded in the evidence.'
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

  /* Render the confidence the API actually returned.
     Returns null when the backend sent no numeric confidence, so the caller
     can hide the block.  There is deliberately no fallback: a successful
     identification is NOT 100%, and a qualitative verdict is never converted
     into a percentage.

     One decimal at most, with a bare trailing ".0" dropped -- 0.923 reads as
     92.3%, 0.684 as 68.4%, 0.41 as 41%. */
  function formatConfidence(value) {
    if (typeof value !== 'number' || !isFinite(value)) return null;
    var pctValue = value * 100;
    if (pctValue >= 99.95) return '100%';
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

  /* ── router ───────────────────────────────────────────────────────────── */

  var views = {};
  var current = 'home';
  var lastFocus = null;
  var booted = false;          // set once init() has finished wiring the DOM

  function showView(name, opts) {
    var target = views[name] ? name : 'home';
    Object.keys(views).forEach(function (key) {
      var active = key === target;
      views[key].classList.toggle('is-active', active);
      views[key].hidden = !active;
    });

    current = target;

    $$('.nav__link').forEach(function (link) {
      var isCurrent = link.getAttribute('data-nav') === target ||
                      (target === 'detail' && link.getAttribute('data-nav') === 'heritage');
      if (isCurrent) link.setAttribute('aria-current', 'page');
      else link.removeAttribute('aria-current');
    });

    if (target !== 'home') window.scrollTo({ top: 0, behavior: reducedMotion() ? 'auto' : 'smooth' });

    // Guarded: on a cold start routed straight to #heritage, showView() runs
    // before initExplorer() has bound these elements. init() kicks the load off
    // once everything is wired.
    if (booted && target === 'heritage' && catalogue.length === 0 && !catalogueLoading) loadCatalogue();
    if (target === 'about') refreshHealth();

    if (!opts || opts.focus !== false) {
      var main = $('#main');
      if (main) main.focus({ preventScroll: true });
    }
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

    window.addEventListener('hashchange', function () {
      var name = location.hash.slice(1).split('/')[0];
      if (views[name]) showView(name);
    });

    var initial = location.hash.slice(1).split('/')[0];
    showView(views[initial] ? initial : 'home', { focus: false });
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

  var CHAPTERS = [
    { eyebrow: 'Heritage Discovery', title: ['Recognise the', 'stories of place'],
      desc: 'Identify monuments from photographs using visual AI, explore their history, and discover the architectural stories behind remarkable places.' },
    { eyebrow: 'Chapter 02 — Recognise', title: ['Every monument', 'begins as a photograph'],
      desc: 'Upload a photograph and the system embeds it with CLIP, then searches the indexed catalogue for visually similar monuments.' },
    { eyebrow: 'Chapter 03 — Match', title: ['Similarity alone', 'is not identification'],
      desc: 'An open-set gate measures how far the best match stands above the field. A weak or ambiguous result is rejected rather than guessed.' },
    { eyebrow: 'Chapter 04 — Verify', title: ['A match is only', 'accepted when it separates'],
      desc: 'Acceptance requires both a similarity threshold and a calibrated margin over the nearest competing site.' },
    { eyebrow: 'Chapter 05 — Explore', title: ['The catalogue', 'is the context'],
      desc: 'Explore 455 monuments by name, city, country, region or type, with the historical record attached to each one.' },
    { eyebrow: 'Chapter 06 — Evidence', title: ['Every claim', 'carries its source'],
      desc: 'Local identifications are reported with the catalogue metadata and the evidence records held with them, each with its named source.' }
  ];

  function initChapters() {
    var items = $$('.rail__item');
    var dockChapter = $('#dock-chapter');

    items.forEach(function (btn) {
      btn.addEventListener('click', function () {
        var index = parseInt(btn.getAttribute('data-chapter'), 10);
        setChapter(index);
      });
    });

    function setChapter(index) {
      var chapter = CHAPTERS[index];
      if (!chapter) return;

      items.forEach(function (item, i) {
        item.classList.toggle('is-active', i === index);
        item.setAttribute('aria-current', i === index ? 'true' : 'false');
      });

      var eyebrow = $('.hero__eyebrow .eyebrow__text');
      var lines = $$('.hero__title .line__in');
      var desc = $('.hero__desc');

      eyebrow.textContent = chapter.eyebrow;
      if (lines[0]) lines[0].textContent = chapter.title[0];
      if (lines[1]) lines[1].textContent = chapter.title[1];
      desc.textContent = chapter.desc;
      dockChapter.textContent =
        String(index + 1).padStart(2, '0') + ' — ' + chapter.eyebrow.replace(/^Chapter \d+ — /, '');

      // restart the mask reveal so the headline re-enters on each chapter
      if (!reducedMotion()) {
        lines.forEach(function (line, i) {
          line.style.animation = 'none';
          void line.offsetWidth;
          line.style.animation = '';
          line.style.animationDelay = (i * 0.1) + 's';
        });
      }
    }

    setChapter(0);
  }

  /* ── pointer parallax (desktop pointer only) ──────────────────────────── */

  function initParallax() {
    if (reducedMotion() || coarsePointer()) return;

    var bg = $('#hero-bg');
    var rail = $('.rail');
    var hero = $('#hero');
    var raf = null;
    var tx = 0, ty = 0;

    hero.addEventListener('pointermove', function (ev) {
      if (ev.pointerType !== 'mouse') return;
      var rect = hero.getBoundingClientRect();
      tx = (ev.clientX - rect.left) / rect.width - 0.5;
      ty = (ev.clientY - rect.top) / rect.height - 0.5;
      if (raf === null) raf = window.requestAnimationFrame(apply);
    });

    hero.addEventListener('pointerleave', function () { tx = 0; ty = 0; if (raf === null) raf = window.requestAnimationFrame(apply); });

    function apply() {
      bg.style.transform = 'scale(1.06) translate(' + (-tx * 14).toFixed(2) + 'px,' + (-ty * 10).toFixed(2) + 'px)';
      if (rail) rail.style.transform = 'translateY(-50%) translateX(' + (tx * 6).toFixed(2) + 'px)';
      raf = null;
    }
  }

  /* ── health ───────────────────────────────────────────────────────────── */

  var health = null;

  function refreshHealth() {
    return fetch(API_BASE + '/health')
      .then(function (res) { return res.ok ? res.json() : null; })
      .then(function (data) {
        health = data;
        paintHealth();
        return data;
      })
      .catch(function () {
        health = null;
        paintHealth();
        return null;
      });
  }

  function paintHealth() {
    var dockSystem = $('#dock-system');
    var dockIndex = $('#dock-index');

    if (!health) {
      dockSystem.textContent = 'Backend offline';
      dockSystem.className = 'dock__v is-err';
      dockIndex.textContent = '—';
      setHealthPanel(null);
      return;
    }

    var ok = health.service_ready && health.status === 'ok';
    dockSystem.textContent = ok ? 'Ready' : (health.status || 'Degraded');
    dockSystem.className = 'dock__v ' + (ok ? 'is-ok' : 'is-warn');
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
  var recognizeBtn, recStatus, uploadError, resultRegion, questionInput;
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
    questionInput = $('#question');

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
      node.classList.toggle('is-active', i === index);
      node.classList.toggle('is-done', i < index);
    });
  }

  function completePipeline() {
    $$('.pipeline__stage').forEach(function (node) {
      node.classList.remove('is-active');
      node.classList.add('is-done');
    });
  }

  function resetPipeline() {
    clearStageTimers();
    $$('.pipeline__stage').forEach(function (node) {
      node.classList.remove('is-active', 'is-done');
    });
  }

  /* ── recognition ──────────────────────────────────────────────────────── */

  function runRecognition() {
    if (!selected || busy) return;

    busy = true;
    recognizeBtn.disabled = true;
    uploadZone.classList.add('is-busy');
    recStatus.className = 'recognition-actions__status is-busy';
    resultRegion.innerHTML = '';

    resetPipeline();
    setStage('image');
    stageTimers.push(window.setTimeout(function () { setStage('analysis'); }, 450));
    stageTimers.push(window.setTimeout(function () { setStage('match'); }, 1400));

    var payload = { image_base64: selected.dataUrl, question: questionInput.value || '', top_k: 5 };

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
        recStatus.textContent = data.recognition_source === 'unknown' ? 'Not confirmed' : 'Complete';
        recStatus.className = 'recognition-actions__status';
      })
      .catch(function (err) {
        clearStageTimers();
        resetPipeline();
        var code = err && err.code;
        // A fetch() network failure rejects with a TypeError and carries no
        // status, so it is matched by type rather than by status code.
        var offline = err instanceof TypeError || (err && err.status === 0);
        var message = ERROR_MESSAGES[code] ||
          (offline
            ? 'The recognition service could not be reached. Is the backend running on port 8000?'
            : 'Recognition could not be completed. Please try again.');
        recStatus.textContent = 'Failed';
        recStatus.className = 'recognition-actions__status is-err';
        resultRegion.innerHTML = '';
        resultRegion.appendChild(errorPanel(message));
      })
      .then(function () {
        busy = false;
        recognizeBtn.disabled = !selected;
        uploadZone.classList.remove('is-busy');
      });
  }

  function errorPanel(message) {
    var card = el('div', 'result result--unknown');
    var body = el('div', 'result__body');
    body.appendChild(el('p', 'result__label', 'Recognition unavailable'));
    body.appendChild(el('p', 'result__text', message));
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

    card.classList.add(
      source === 'local' ? 'result--local' : source === 'ollama' ? 'result--global' : 'result--unknown'
    );

    /* banner */
    var banner = el('div', 'result__banner');
    var badgeText =
      source === 'local' ? 'Local visual recognition'
      : source === 'ollama' ? 'Identified through global vision'
      : 'Identification not confirmed';
    banner.appendChild(el('span', 'result__badge', badgeText));
    card.appendChild(banner);

    var body = el('div', 'result__body');

    /* --- UNKNOWN ------------------------------------------------------- */
    if (source === 'unknown') {
      /* No gallery: showing photographs of a monument the backend refused to
         confirm would be presenting an unconfirmed guess as an archive view. */

      var uHead = el('div', 'result__headline');
      uHead.appendChild(el('p', 'result__verdict', 'Not confirmed'));
      uHead.appendChild(el('h3', 'result__name', 'No monument identified'));
      body.appendChild(uHead);

      var uAbout = el('div', 'result__stack');
      uAbout.appendChild(el('p', 'result__text',
        'This photograph could not be matched confidently to a heritage site. ' +
        'No monument, location or historical information is shown, because none was established.'));

      var reasonText = data.reason ? (REASON_TEXT[data.reason] || data.reason) : null;
      if (reasonText) uAbout.appendChild(field('Why', reasonText));

      body.appendChild(section('About', uAbout));

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
      lHead.appendChild(el('p', 'result__verdict', 'Identified'));

      var lName = el('h3', 'result__name', meta.name || (record && record.name) || '—');
      lHead.appendChild(lName);

      var place = [meta.location, meta.state, meta.country].filter(Boolean).join(', ');
      if (!place && meta.country) place = meta.country;
      if (!place && record) {
        place = [record.city, record.region, record.country].filter(Boolean).join(', ');
      }
      if (place) lHead.appendChild(el('p', 'result__place', place));
      body.appendChild(lHead);

      /* CONFIDENCE -- the value the API returned, or nothing at all.  There is
         no fallback: an accepted match is not 100% by definition. */
      var localConfidence = confidenceMetric(data.confidence, null);
      if (localConfidence) {
        var cBlock = el('div', 'result__confidence');
        cBlock.appendChild(el('p', 'result__label', 'Confidence'));
        cBlock.appendChild(el('p', 'result__confidence-value', localConfidence));
        body.appendChild(cBlock);
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

      var aboutSection = section('About', about.children.length ? about : null);
      if (aboutSection) body.appendChild(aboutSection);

      /* highlights — evidence claims actually returned by the backend */
      var claims = (data.evidence && Array.isArray(data.evidence.relevant_claims) && data.evidence.relevant_claims.length)
        ? data.evidence.relevant_claims
        : (data.evidence && Array.isArray(data.evidence.claims) ? data.evidence.claims : []);
      if (claims && claims.length) {
        var ul = el('ul', 'factlist');
        claims.forEach(function (claim) { ul.appendChild(el('li', null, claim)); });
        body.appendChild(section('Highlights', ul));
      }

      /* answer, when one was actually grounded */
      if (data.answer && data.is_grounded) {
        body.appendChild(section('Grounded answer', el('p', 'result__text', data.answer)));
      }

      body.appendChild(section('Sources', sourcesBlock(data, record)));

      card.appendChild(body);
      resultRegion.innerHTML = '';
      resultRegion.appendChild(card);
      wireGallery(card);
      return;
    }

    /* --- OLLAMA / GLOBAL VISION ---------------------------------------- */
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
    gHead.appendChild(el('p', 'result__verdict', 'Identified'));
    gHead.appendChild(el('h3', 'result__name', g.site_name || 'Global vision identification'));
    var gPlace = [g.city, g.country].filter(Boolean).join(', ');
    if (gPlace) gHead.appendChild(el('p', 'result__place', gPlace));
    body.appendChild(gHead);

    /* Confidence from the vision model, or nothing.  A missing value is never
       promoted to 100%. */
    var globalConfidence = confidenceMetric(
      typeof g.confidence === 'number' ? g.confidence : data.confidence,
      g.uncertain ? 'Uncertain' : null
    );
    if (globalConfidence) {
      var gConf = el('div', 'result__confidence');
      gConf.appendChild(el('p', 'result__label', 'Confidence'));
      gConf.appendChild(el('p', 'result__confidence-value', globalConfidence));
      body.appendChild(gConf);
    }

    var gAbout = el('div', 'result__stack');
    if (g.significance) gAbout.appendChild(field('Significance', g.significance));
    if (g.historical_period) gAbout.appendChild(field('Historical period', g.historical_period));
    if (g.architectural_style) gAbout.appendChild(field('Architectural style', g.architectural_style));
    if (g.founder_built_by) gAbout.appendChild(field('Built by', g.founder_built_by));
    var gAboutSection = section('About', gAbout.children.length ? gAbout : null);
    if (gAboutSection) body.appendChild(gAboutSection);

    if (g.reason) body.appendChild(section('Reason', el('p', 'result__text', g.reason)));

    if (Array.isArray(g.interesting_facts) && g.interesting_facts.length) {
      var gFacts = el('ul', 'factlist');
      g.interesting_facts.forEach(function (f) {
        if (f) gFacts.appendChild(el('li', null, String(f)));
      });
      if (gFacts.children.length) body.appendChild(section('Additional information', gFacts));
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
      note.appendChild(el('span', 'source__name', 'Global vision identification'));
      note.appendChild(el('span', 'source__note',
        'No external source accompanies this identification. It is the vision model’s own assessment.'));
      srcWrap.appendChild(note);
    }
    body.appendChild(section('Sources', srcWrap));

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

  function applyFilters() {
    var query = (searchInput.value || '').trim();
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
      img.alt = '';
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
    history.replaceState(null, '', '#heritage/' + record.site_id);
  }

  function detailSection(title, text) {
    if (!text || !String(text).trim()) return null;
    var wrap = el('section', 'detail__section');
    wrap.appendChild(el('h3', 'detail__title', title));
    wrap.appendChild(el('p', 'detail__text', String(text)));
    return wrap;
  }

  /* ── boot ─────────────────────────────────────────────────────────────── */

  function init() {
    initRouter();
    initMenu();
    initChapters();
    initParallax();
    initUpload();
    initExplorer();

    refreshHealth();
    loadGalleryManifest();
    loadCatalogue();
    booted = true;
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init);
  else init();
})();