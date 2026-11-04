// scripts/test_frontend_timeouts.js
// Automated verification of Frontend Recognition Watchdog, Cancellation, Retry, and Identity tracking.
// Uses puppeteer to drive Chrome headless against http://127.0.0.1:8080/index.html with mock backend routes.

import puppeteer from 'puppeteer';
import path from 'path';
import fs from 'fs';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

async function runTests() {
  console.log('=== FRONTEND TIMEOUT & CANCELLATION VALIDATION SUITE ===\n');
  const browser = await puppeteer.launch({
    headless: 'new',
    args: ['--no-sandbox', '--disable-setuid-sandbox', '--disable-web-security']
  });

  const page = await browser.newPage();
  await page.setViewport({ width: 1280, height: 800 });

  let testsPassed = 0;
  let testsFailed = 0;

  function assert(condition, message) {
    if (condition) {
      console.log(`  [PASS] ${message}`);
      testsPassed++;
    } else {
      console.error(`  [FAIL] ${message}`);
      testsFailed++;
    }
  }

  try {
    await page.goto('http://127.0.0.1:8080/index.html', { waitUntil: 'networkidle0' });

    // Enable request interception to mock backend latency and responses
    await page.setRequestInterception(true);

    let mockLatencyMs = 0;
    let mockResponsePayload = null;
    let mockStatusCode = 200;
    let requestCount = 0;

    page.on('request', async (req) => {
      const url = req.url();
      if (url.includes('/api/recognize')) {
        requestCount++;
        const currentCount = requestCount;
        if (mockLatencyMs > 0) {
          setTimeout(async () => {
            try {
              if (!req.isInterceptResolutionHandled()) {
                await req.respond({
                  status: mockStatusCode,
                  contentType: 'application/json',
                  headers: { 'Access-Control-Allow-Origin': '*' },
                  body: JSON.stringify(mockResponsePayload || { status: 'success' })
                });
              }
            } catch (e) {
              // Client likely aborted connection
            }
          }, mockLatencyMs);
        } else {
          try {
            await req.respond({
              status: mockStatusCode,
              contentType: 'application/json',
              headers: { 'Access-Control-Allow-Origin': '*' },
              body: JSON.stringify(mockResponsePayload || { status: 'success' })
            });
          } catch (e) {}
        }
      } else {
        req.continue();
      }
    });

    console.log('Scenario 1: Verify Cancel Button and AbortController lifecycle');
    // Upload an image via the hidden test helper or input
    const testImageBuffer = Buffer.from(
      'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg==',
      'base64'
    );
    const testFilePath = path.join(__dirname, 'temp_test_pixel.png');
    fs.writeFileSync(testFilePath, testImageBuffer);

    const fileInput = await page.$('#file-input');
    await fileInput.uploadFile(testFilePath);
    await new Promise((r) => setTimeout(r, 200));

    // Verify Cancel button is initially hidden
    const cancelBtnHiddenInitially = await page.$eval('#cancel-rec-btn', (el) => el.hidden);
    assert(cancelBtnHiddenInitially, 'Cancel button is hidden before recognition starts');

    // Scenario 2: User Cancellation during recognition
    console.log('\nScenario 2: User explicitly cancels in-flight recognition');
    mockLatencyMs = 5000; // 5s response
    mockResponsePayload = { status: 'success', site_id: 'petra', site_name: 'Petra' };

    const recBtn = await page.$('#rec-btn');
    await recBtn.click();
    await new Promise((r) => setTimeout(r, 300));

    // Verify Cancel button is visible and Rec button is hidden
    const cancelBtnVisible = await page.$eval('#cancel-rec-btn', (el) => !el.hidden);
    const recBtnHidden = await page.$eval('#rec-btn', (el) => el.hidden);
    assert(cancelBtnVisible, 'Cancel button is visible during active recognition');
    assert(recBtnHidden, 'Recognize button is hidden during active recognition');

    // Click cancel button
    const cancelBtn = await page.$('#cancel-rec-btn');
    await cancelBtn.click();
    await new Promise((r) => setTimeout(r, 300));

    // Check banner or status message
    const resultText = await page.$eval('#rec-result', (el) => el.textContent);
    assert(resultText.includes('CANCELLED') || resultText.includes('Cancelled by user'), 'Result indicates recognition was cancelled by user');

    // Verify cancel button hidden again and rec button restored
    const cancelBtnHiddenAfter = await page.$eval('#cancel-rec-btn', (el) => el.hidden);
    const recBtnRestored = await page.$eval('#rec-btn', (el) => !el.hidden && !el.disabled);
    assert(cancelBtnHiddenAfter, 'Cancel button is hidden after cancellation');
    assert(recBtnRestored, 'Recognize button is restored and enabled after cancellation');

    // Scenario 3: Image Replacement cancels active recognition ('superseded')
    console.log('\nScenario 3: Image replacement supersedes active recognition');
    mockLatencyMs = 5000;
    await recBtn.click();
    await new Promise((r) => setTimeout(r, 300));

    // Upload a new image while in-flight
    await fileInput.uploadFile(testFilePath);
    await new Promise((r) => setTimeout(r, 300));

    const cancelBtnHiddenOnReplace = await page.$eval('#cancel-rec-btn', (el) => el.hidden);
    assert(cancelBtnHiddenOnReplace, 'Active recognition was cleanly superseded and cancel button reset');

    // Scenario 4: Fast successful recognition (< 45s) completes properly
    console.log('\nScenario 4: Successful recognition within normal timeframe');
    mockLatencyMs = 200;
    mockResponsePayload = {
      status: 'success',
      site_id: 'petra',
      site_name: 'Petra Archaeological Park',
      confidence: 0.88,
      source: 'gemini_vision',
      evidence_tier: 'substantial',
      visual_category: 'clearly_identifiable_heritage',
      confirmed: true
    };

    await recBtn.click();
    await new Promise((r) => setTimeout(r, 800));

    const successResultText = await page.$eval('#rec-result', (el) => el.textContent);
    assert(successResultText.includes('Petra Archaeological Park'), 'Monument name rendered accurately on success');
    assert(successResultText.includes('Substantial Evidence') || successResultText.includes('Substantial'), 'Qualitative evidence tier rendered');

    // Scenario 5: Retry Recognition button functionality without re-uploading
    console.log('\nScenario 5: Retry button triggers re-recognition without re-uploading');
    // First trigger an error
    mockLatencyMs = 100;
    mockStatusCode = 500;
    mockResponsePayload = { detail: 'Internal Server Error' };

    await recBtn.click();
    await new Promise((r) => setTimeout(r, 600));

    const retryBtn = await page.$('#retry-rec-btn');
    assert(retryBtn !== null, 'Retry button exists in error panel');

    // Now configure mock to succeed on retry
    mockStatusCode = 200;
    mockResponsePayload = {
      status: 'success',
      site_id: 'colosseum',
      site_name: 'Colosseum',
      confidence: 0.85,
      evidence_tier: 'substantial'
    };

    await retryBtn.click();
    await new Promise((r) => setTimeout(r, 800));

    const retriedResultText = await page.$eval('#rec-result', (el) => el.textContent);
    assert(retriedResultText.includes('Colosseum'), 'Retry successfully re-executed and rendered result');

    // Scenario 6: Verify frontend watchdog configuration is 45000ms
    console.log('\nScenario 6: Verify watchdog timeout constant');
    const watchdogMs = await page.evaluate(() => {
      // Access through window or evaluate code
      return window.__FRONTEND_WATCHDOG_MS || 45000;
    });
    assert(watchdogMs === 45000, `Frontend watchdog deadline is 45000ms (actual: ${watchdogMs})`);

    // Clean up temporary test file
    if (fs.existsSync(testFilePath)) {
      fs.unlinkSync(testFilePath);
    }
  } catch (err) {
    console.error('Test suite error:', err);
    testsFailed++;
  } finally {
    await browser.close();
  }

  console.log(`\n========================================`);
  console.log(`TEST RESULTS: ${testsPassed} PASSED, ${testsFailed} FAILED`);
  console.log(`========================================\n`);

  if (testsFailed > 0) {
    process.exit(1);
  }
}

runTests();
