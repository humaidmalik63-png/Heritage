// Comprehensive End-to-End Validation Script for Pause Functionality & Mobile Responsiveness
const http = require('http');

async function getWsUrl() {
  const res = await fetch('http://127.0.0.1:9222/json');
  const targets = await res.json();
  const page = targets.find(t => t.type === 'page' && t.url.includes('8080'));
  if (!page) throw new Error('Heritage page not found');
  return page.webSocketDebuggerUrl;
}

function cdpClient(wsUrl) {
  const ws = new WebSocket(wsUrl);
  let id = 1;
  const callbacks = new Map();
  const consoleErrors = [];

  ws.onmessage = (event) => {
    const msg = JSON.parse(event.data);
    if (msg.method === 'Runtime.consoleAPICalled' && msg.params.type === 'error') {
      consoleErrors.push(msg.params.args.map(a => a.value || a.description).join(' '));
    }
    if (msg.id && callbacks.has(msg.id)) {
      const cb = callbacks.get(msg.id);
      callbacks.delete(msg.id);
      if (msg.error) cb.reject(msg.error);
      else cb.resolve(msg.result);
    }
  };

  const send = (method, params = {}) => new Promise((resolve, reject) => {
    const msgId = id++;
    callbacks.set(msgId, { resolve, reject });
    ws.send(JSON.stringify({ id: msgId, method, params }));
  });

  return new Promise((resolve, reject) => {
    ws.onopen = async () => {
      await send('Runtime.enable');
      resolve({ send, close: () => ws.close(), getErrors: () => consoleErrors });
    };
    ws.onerror = reject;
  });
}

async function run() {
  console.log('='.repeat(70));
  console.log('STARTING E2E VALIDATION: 7-SCREEN PAUSE + 10-VIEWPORT RESPONSIVENESS');
  console.log('='.repeat(70));

  const wsUrl = await getWsUrl();
  const client = await cdpClient(wsUrl);

  // 1. Dismiss loader overlay
  await client.send('Runtime.evaluate', {
    expression: `(() => {
      const l = document.querySelector('#loader-overlay');
      if (l) { l.classList.add('is-hidden'); l.style.display = 'none'; }
    })()`
  });

  // ── PART 1: 10-VIEWPORT RESPONSIVE VALIDATION ────────────────────────────
  const requestedViewports = [
    { name: 'iPhone SE (1st gen)', w: 320, h: 568 },
    { name: 'Galaxy S20 / Android standard', w: 360, h: 800 },
    { name: 'iPhone X / 11 / 12 mini', w: 375, h: 812 },
    { name: 'iPhone 12 / 13 / 14', w: 390, h: 844 },
    { name: 'Google Pixel 7 / Galaxy S24', w: 412, h: 915 },
    { name: 'iPhone 14/15/16 Pro Max', w: 430, h: 932 },
    { name: 'iPad Portrait', w: 768, h: 1024 },
    { name: 'iPad Landscape', w: 1024, h: 768 },
    { name: 'HD Laptop', w: 1366, h: 768 },
    { name: 'Full HD Desktop', w: 1920, h: 1080 }
  ];

  console.log('\n[1/3] Testing All 10 Target Viewports Across All Views:');
  const views = ['home', 'recognition', 'heritage', 'about'];
  let allViewportsPassed = true;

  for (const vp of requestedViewports) {
    await client.send('Emulation.setDeviceMetricsOverride', {
      width: vp.w,
      height: vp.h,
      deviceScaleFactor: 1,
      mobile: vp.w <= 768
    });
    await new Promise(r => setTimeout(r, 60));

    let vpClean = true;
    for (const view of views) {
      await client.send('Runtime.evaluate', { expression: `window.location.hash = '#${view}';` });
      await new Promise(r => setTimeout(r, 50));

      const res = await client.send('Runtime.evaluate', {
        expression: `(() => {
          const docW = document.documentElement.clientWidth;
          const scrollW = document.documentElement.scrollWidth;
          const hasHScroll = scrollW > docW;
          const overflows = [];
          document.querySelectorAll('body *:not(script):not(style):not([hidden])').forEach(el => {
            if (el.id === 'loader-overlay' || el.closest('#loader-overlay')) return;
            const style = window.getComputedStyle(el);
            if (style.display === 'none' || style.visibility === 'hidden') return;
            // Ignore intentional parallax overflow layers
            if (el.id === 'hero-bg' || el.classList.contains('hero__slide')) return;
            const r = el.getBoundingClientRect();
            if (r.width > docW + 1.5 || r.right > docW + 1.5) {
              overflows.push({ tag: el.tagName, id: el.id, cls: el.className });
            }
          });
          return { hasHScroll, scrollW, docW, count: overflows.length };
        })()`,
        returnByValue: true
      });

      const { hasHScroll, count } = res.result.value;
      if (hasHScroll || count > 0) {
        vpClean = false;
        allViewportsPassed = false;
        console.log(`   [FAIL] ${vp.w}x${vp.h} (${vp.name}) on #${view} - hasHScroll=${hasHScroll}, overflowCount=${count}`);
      }
    }
    if (vpClean) {
      console.log(`   [PASS] ${vp.w}x${vp.h} (${vp.name}) - Clean on all 4 views`);
    }
  }

  // ── PART 2: SEVEN-SCREEN PAUSE & RESUME TESTING ─────────────────────────
  console.log('\n[2/3] Testing Seven-Screen Pause & Resume Precision:');
  // Reset viewport to mobile 375x812 for testing button and touch
  await client.send('Emulation.setDeviceMetricsOverride', {
    width: 375,
    height: 812,
    deviceScaleFactor: 1,
    mobile: true
  });
  await client.send('Runtime.evaluate', {
    expression: `(() => {
      window.location.hash = '#home';
      window.scrollTo(0, 0);
      const home = document.querySelector('#view-home');
      if (home) home.scrollIntoView();
    })()`
  });
  await new Promise(r => setTimeout(r, 600));

  const pauseSuite = await client.send('Runtime.evaluate', {
    expression: `(async () => {
      const toggle = document.querySelector('#chapter-play-toggle');
      const btnPrev = document.querySelector('#chapter-prev');
      const btnNext = document.querySelector('#chapter-next');
      const dockChapter = document.querySelector('#dock-chapter');
      const heroMonument = document.querySelector('#hero-eyebrow-monument');
      const hero = document.querySelector('#hero');
      const progress = document.querySelector('#dock-chapter-progress');

      // Test 1: Initial state is playing
      const initPauseHidden = toggle.querySelector('.icon-pause').hasAttribute('hidden');
      const initPlayHidden = toggle.querySelector('.icon-play').hasAttribute('hidden');
      const initAria = toggle.getAttribute('aria-label');

      // Test 2: Trigger Pause
      toggle.click();
      const afterPausePauseHidden = toggle.querySelector('.icon-pause').hasAttribute('hidden');
      const afterPausePlayHidden = toggle.querySelector('.icon-play').hasAttribute('hidden');
      const afterPauseAria = toggle.getAttribute('aria-label');
      const heroHasPausedClass = hero.classList.contains('is-paused');
      const toggleHasPausedClass = toggle.classList.contains('is-paused');
      const activeSlide = document.querySelector('.hero__slide.is-active');
      const animStateWhilePaused = activeSlide ? window.getComputedStyle(activeSlide).animationPlayState : null;

      const pausedChapterText = dockChapter.textContent;
      const pausedMonumentText = heroMonument.textContent;

      // Test 3: Wait 6 seconds while paused
      await new Promise(r => setTimeout(r, 6000));
      const afterWaitChapterText = dockChapter.textContent;
      const afterWaitMonumentText = heroMonument.textContent;

      // Test 4: Manual navigation while paused (Next chapter)
      btnNext.click();
      await new Promise(r => setTimeout(r, 100));
      const cuedChapterText = dockChapter.textContent;
      const cuedMonumentText = heroMonument.textContent;
      const stillPausedAfterNext = toggle.querySelector('.icon-pause').hasAttribute('hidden');

      // Test 5: Trigger Resume
      toggle.click();
      const resumedPauseHidden = toggle.querySelector('.icon-pause').hasAttribute('hidden');
      const resumedPlayHidden = toggle.querySelector('.icon-play').hasAttribute('hidden');
      const resumedAria = toggle.getAttribute('aria-label');
      const heroHasPausedClassResumed = hero.classList.contains('is-paused');
      const animStateResumed = activeSlide ? window.getComputedStyle(activeSlide).animationPlayState : null;

      return {
        initOk: (!initPauseHidden && initPlayHidden && initAria.includes('Pause')),
        pauseUiOk: (afterPausePauseHidden && !afterPausePlayHidden && afterPauseAria.includes('Resume')),
        heroPausedClassOk: heroHasPausedClass && toggleHasPausedClass,
        kenBurnsPaused: animStateWhilePaused === 'paused',
        pausedChapterText,
        afterWaitChapterText,
        cuedChapterText,
        chapterDidNotChangeWhilePaused: (pausedChapterText === afterWaitChapterText),
        monumentDidNotChangeWhilePaused: (pausedMonumentText === afterWaitMonumentText),
        manualNavWorkedWhilePaused: (cuedChapterText !== pausedChapterText),
        stillPausedAfterManualNav: stillPausedAfterNext,
        resumeUiOk: (!resumedPauseHidden && resumedPlayHidden && resumedAria.includes('Pause')),
        heroResumedClassOk: !heroHasPausedClassResumed,
        kenBurnsResumed: animStateResumed === 'running'
      };
    })()`,
    awaitPromise: true,
    returnByValue: true
  });

  const p = pauseSuite.result.value;
  console.log(`   [${p.initOk ? 'PASS' : 'FAIL'}] Initial State: Playing with pause icon and 'Pause' label`);
  console.log(`   [${p.pauseUiOk ? 'PASS' : 'FAIL'}] Pause Click: Play icon shown and 'Resume' label displayed`);
  console.log(`   [${p.heroPausedClassOk ? 'PASS' : 'FAIL'}] Hero & Button: .is-paused class applied`);
  console.log(`   [${p.kenBurnsPaused ? 'PASS' : 'FAIL'}] Ken Burns Animation: Play state frozen to 'paused'`);
  console.log(`   [${p.chapterDidNotChangeWhilePaused ? 'PASS' : 'FAIL'}] Chapter Progression: '${p.pausedChapterText}' === '${p.afterWaitChapterText}'`);
  console.log(`   [${p.monumentDidNotChangeWhilePaused ? 'PASS' : 'FAIL'}] Slideshow Progression: 0 background image changes in 6s while paused`);
  console.log(`   [${p.manualNavWorkedWhilePaused ? 'PASS' : 'FAIL'}] Manual Navigation: Manual next (${p.pausedChapterText} -> ${p.cuedChapterText})`);
  console.log(`   [${p.stillPausedAfterManualNav ? 'PASS' : 'FAIL'}] Pause State Preserved: Experience stays paused after manual navigation`);
  console.log(`   [${p.resumeUiOk ? 'PASS' : 'FAIL'}] Resume Click: Pause icon restored and 'Pause' label active`);
  console.log(`   [${p.kenBurnsResumed ? 'PASS' : 'FAIL'}] Ken Burns Animation: Resumed to 'running' smoothly`);

  // ── PART 3: CONSOLE ERRORS & TOUCH TARGETS ────────────────────────────────
  console.log('\n[3/3] Testing Touch Targets & Console Stability:');
  const touchCheck = await client.send('Runtime.evaluate', {
    expression: `(() => {
      const btn = document.querySelector('#chapter-play-toggle');
      const r = btn.getBoundingClientRect();
      return {
        w: r.width,
        h: r.height,
        touchAreaAdequate: r.width >= 30 && r.height >= 30
      };
    })()`,
    returnByValue: true
  });
  console.log(`   [${touchCheck.result.value.touchAreaAdequate ? 'PASS' : 'FAIL'}] Touch Button: Size ${touchCheck.result.value.w}x${touchCheck.result.value.h}px (meets mobile touchscreen accessibility standards)`);

  const errors = client.getErrors();
  console.log(`   [${errors.length === 0 ? 'PASS' : 'FAIL'}] Browser Console: ${errors.length} error(s) logged`);
  if (errors.length > 0) {
    console.log('      Errors:', errors);
  }

  const allPassed = allViewportsPassed &&
    p.initOk && p.pauseUiOk && p.heroPausedClassOk && p.kenBurnsPaused &&
    p.chapterDidNotChangeWhilePaused && p.monumentDidNotChangeWhilePaused &&
    p.manualNavWorkedWhilePaused && p.stillPausedAfterManualNav &&
    p.resumeUiOk && p.kenBurnsResumed &&
    touchCheck.result.value.touchAreaAdequate &&
    errors.length === 0;

  console.log('\n' + '='.repeat(70));
  if (allPassed) {
    console.log('ALL FRONTEND PAUSE & RESPONSIVE VALIDATION CHECKS PASSED (100%)');
  } else {
    console.log('SOME CHECKS FAILED — REVIEW DETAILED LOGS ABOVE');
  }
  console.log('='.repeat(70));

  client.close();
}

run().catch(console.error);
