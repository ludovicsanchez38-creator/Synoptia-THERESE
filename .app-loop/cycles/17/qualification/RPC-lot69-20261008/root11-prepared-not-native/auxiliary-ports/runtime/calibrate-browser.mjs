// Calibrage runtime_ui, visual_capture et network_capture sur la pile réelle jetable.
import { createHash } from 'node:crypto';
import {gitHead, connectOwnedChrome} from 'file:///private/tmp/therese-c17-wrapper-canary-eff7b4e4f24649dd8628503bc7bfc8b3/auxiliary-ports/runtime/aux_node.mjs';
import { mkdir, readFile, writeFile } from 'node:fs/promises';
import { dirname, resolve } from 'node:path';
import { pathToFileURL, fileURLToPath } from 'node:url';

const here = dirname(fileURLToPath(import.meta.url));
const repo = '/private/tmp/therese-c17-wrapper-source-kGvU1hdx/source';
const { chromium } = await import(pathToFileURL("/private/tmp/therese-c17-wrapper-source-kGvU1hdx/source/node_modules/playwright/index.mjs").href);
const { verifierPileJetable, installerGardeReseau } = await import(pathToFileURL(resolve(here, 'couverture-ecran-c17.mjs')).href);
const manifest = JSON.parse(await readFile('/private/tmp/therese-c17-wrapper-canary-eff7b4e4f24649dd8628503bc7bfc8b3/runtime/pile-reprise.json', 'utf8'));
const base = 'http://127.0.0.1:5173/?port=17593';
const out = '/private/tmp/therese-c17-wrapper-canary-eff7b4e4f24649dd8628503bc7bfc8b3/runtime/calibration/browser-rpc';
await mkdir(out);
const hash = async (path) => createHash('sha256').update(await readFile(path)).digest('hex');
const witness = [resolve(repo, 'src/frontend/index.html'), '/private/tmp/therese-c17-wrapper-canary-eff7b4e4f24649dd8628503bc7bfc8b3/campaign-sentinel.txt'];
const snapshot = Object.fromEntries(await Promise.all(witness.map(async (path) => [path, await hash(path)])));
const proof = {cycle: 17, status: 'running', repo,
  head: gitHead(JSON.parse(process.env.C17_AUX_GIT_SNAPSHOT_REF), repo),
  nodeVersion: process.version, playwrightVersion: JSON.parse(await readFile("/private/tmp/therese-c17-wrapper-source-kGvU1hdx/source/node_modules/playwright/package.json", 'utf8')).version,
  environment: {base, data_dir: manifest.data_dir, viewport: {width: 1280, height: 800},
    dpr: 1, locale: 'fr-FR', timezoneId: 'Europe/Paris', theme: 'light', reducedMotion: 'reduce', headless: false, channel: 'chrome', chromiumSandbox: true},
};
let browser, page;
const errors = [], captured = [], consoleErrors = [], requestFailures = [];
try {
  proof.stack = await verifierPileJetable(base, manifest.data_dir);
  browser = await connectOwnedChrome(chromium, {headless: false, channel: 'chrome', chromiumSandbox: true});
  proof.chromiumVersion = browser.version();
  const context = await browser.newContext({viewport: proof.environment.viewport, deviceScaleFactor: 1,
    locale: 'fr-FR', timezoneId: 'Europe/Paris', colorScheme: 'light', reducedMotion: 'reduce',
    serviceWorkers: 'block', acceptDownloads: false});
  const guard = {bloquees: [], websockets_bloques: [], telechargements: [], popups: [], portReel: false};
  await installerGardeReseau(context, guard);
  // Témoin réseau synthétique sur une adresse locale, traité sans appel backend.
  await context.route('http://127.0.0.1:17593/api/calibration/c17-fault', (route) => route.fulfill({status: 503,
    contentType: 'application/json', headers: {'access-control-allow-origin': 'http://127.0.0.1:5173'},
    body: JSON.stringify({detail: 'TEMOIN-C17-PANNE'})}));
  page = await context.newPage();
  page.on('pageerror', (error) => errors.push(String(error)));
  page.on('console', (message) => { if (message.type() === 'error') consoleErrors.push(message.text().replace(/([?&](?:token|api_key|key|secret)=)[^&\s]+/gi, '$1[REDACTED]').slice(0, 500)); });
  page.on('requestfailed', (request) => { const url = new URL(request.url()); requestFailures.push({method: request.method(), origin: url.origin, path: url.pathname, error: request.failure()?.errorText}); });
  page.on('response', (response) => {
    const url = new URL(response.url());
    if (['/health', '/api/calibration/c17-fault'].includes(url.pathname)) captured.push({url: response.url(), status: response.status()});
  });
  page.on('popup', (popup) => {guard.popups.push(new URL(popup.url()).origin); void popup.close();});
  page.on('download', (download) => {guard.telechargements.push(new URL(download.url()).origin); void download.cancel();});
  await page.goto(base, {waitUntil: 'domcontentloaded'});
  await page.evaluate(async () => {
    localStorage.clear(); sessionStorage.clear();
    if (indexedDB.databases) await Promise.all((await indexedDB.databases()).filter((db) => db.name).map((db) => new Promise((done, fail) => {
      const request = indexedDB.deleteDatabase(db.name); request.onsuccess = () => done(); request.onerror = () => fail(request.error);
    })));
  });
  await page.reload({waitUntil: 'domcontentloaded'});
  await page.waitForFunction(() => window.__thereseMonte && window.__therese?.runAction, undefined, {timeout: 45000});
  const identity = await page.evaluate(async () => { const response = await fetch('http://127.0.0.1:17593/api/auth/token'); const payload = await response.json(); return {status: response.status, tokenPresent: Boolean(payload.token)}; });
  proof.identity = identity;
  if (identity.status !== 200 || !identity.tokenPresent) throw new Error('Identité HTTP QA absente après montage');
  await page.bringToFront();
  await page.evaluate(() => document.fonts.ready);
  const before = await page.locator('[role=dialog],[role=alertdialog]').count();
  await page.evaluate(() => window.__therese.runAction('shortcuts.open'));
  await page.waitForFunction((initial) => document.querySelectorAll('[role=dialog],[role=alertdialog]').length > initial, before);
  const action = await page.locator('[role=dialog],[role=alertdialog]').last().isVisible();
  const negative = await page.evaluate(() => ({visible: document.visibilityState,
    timeline: document.timeline.currentTime, mounted: window.__thereseMonte,
    dialogBox: (() => {const box = document.querySelector('[role=dialog],[role=alertdialog]')?.getBoundingClientRect(); return box ? {width: box.width, height: box.height} : null;})()}));
  negative.actionWorked = action;
  const negativeOk = negative.visible === 'visible' && negative.timeline > 0 && negative.mounted
    && action && negative.dialogBox.width > 0 && negative.dialogBox.height > 0 && errors.length === 0;
  await page.keyboard.press('Escape');
  await page.waitForTimeout(500);
  const positive = await page.evaluate(() => {
    const element = document.createElement('div'); element.dataset.testid = 'temoin-c17-cache'; element.hidden = true;
    element.textContent = 'Témoin caché dont l’opacité reste 1'; document.body.appendChild(element);
    const box = element.getBoundingClientRect(); return {hidden: element.hidden, opacity: getComputedStyle(element).opacity,
      width: box.width, height: box.height};
  });
  positive.locatorVisible = await page.getByTestId('temoin-c17-cache').isVisible();
  const positiveOk = positive.hidden && positive.opacity === '1' && positive.width === 0 && positive.height === 0 && !positive.locatorVisible;
  proof.runtime_ui = {negative, negativeOk, positive, positiveOk};
  const aPath = resolve(out, 'visual-negative-a.png'), bPath = resolve(out, 'visual-negative-b.png'), cPath = resolve(out, 'visual-positive.png');
  let a, b, attempts = 0;
  for (let index = 0; index < 10; index += 1) {
    attempts = index + 1;
    await page.screenshot({path: aPath, animations: 'disabled'});
    await page.waitForTimeout(300);
    await page.screenshot({path: bPath, animations: 'disabled'});
    a = await hash(aPath); b = await hash(bPath); if (a === b) break;
  }
  await page.evaluate(() => {
    const element = document.createElement('div'); element.dataset.testid = 'temoin-c17-visuel'; element.textContent = 'DÉFAUT VISUEL TÉMOIN C17';
    Object.assign(element.style, {position: 'fixed', inset: '16px', zIndex: '2147483647', display: 'grid', placeItems: 'center',
      background: '#dc2626', color: '#fff', border: '12px solid #facc17', fontSize: '40px'}); document.body.appendChild(element);
  });
  const visible = await page.getByTestId('temoin-c17-visuel').isVisible();
  await page.screenshot({path: cPath, animations: 'disabled'});
  const c = await hash(cPath);
  proof.visual_capture = {negative: {a, b, identical: a === b, attempts, files: [aPath, bPath]},
    positive: {c, differs: c !== a, visible, file: cPath}};
  await page.getByTestId('temoin-c17-visuel').evaluate((element) => element.remove());
  const result = await page.evaluate(async () => ({healthy: (await fetch('http://127.0.0.1:17593/health')).status,
    fault: (await fetch('http://127.0.0.1:17593/api/calibration/c17-fault')).status}));
  const networkNegativeOk = result.healthy === 200 && captured.some((response) => response.status === 200 && response.url.endsWith('/health'));
  const networkPositiveOk = result.fault === 503 && captured.some((response) => response.status === 503 && response.url.endsWith('/api/calibration/c17-fault'));
  proof.network_capture = {negative: {status: result.healthy, detected: networkNegativeOk},
    positive: {status: result.fault, detected: networkPositiveOk}, captured, guard};
  proof.pageErrors = errors;
  proof.status = negativeOk && positiveOk && a === b && c !== a && visible && networkNegativeOk && networkPositiveOk
    && !guard.bloquees.length && !guard.websockets_bloques.length && !guard.telechargements.length && !guard.popups.length && errors.length === 0 ? 'passed' : 'failed';
  await context.close();
} catch (error) {
  proof.status = 'blocked'; proof.error = String(error);
  if (page && !page.isClosed()) {
    try {
      proof.failureDom = await page.evaluate(() => ({url: location.origin + location.pathname, title: document.title, readyState: document.readyState, mounted: Boolean(window.__thereseMonte), bridge: Boolean(window.__therese?.runAction), bodyText: document.body?.innerText.slice(0, 600)}));
      const failurePath = resolve(out, 'failure-page.png');
      await page.screenshot({path: failurePath, animations: 'disabled'});
      proof.failureScreenshot = {path: failurePath, sha256: await hash(failurePath)};
    } catch (diagnosticError) { proof.failureDiagnosticError = String(diagnosticError); }
  }
} finally {
  proof.pageErrors = errors; proof.consoleErrors = consoleErrors; proof.requestFailures = requestFailures;
  if (browser) await browser.close();
  proof.sourcePreserved = Object.fromEntries(await Promise.all(witness.map(async (path) => [path, {before: snapshot[path], after: await hash(path)}])));
  if (Object.values(proof.sourcePreserved).some((entry) => entry.before !== entry.after)) {proof.status = 'failed'; proof.error = 'Source ou verrou préexistant modifié';}
  await writeFile(resolve(out, 'browser-controls.json'), `${JSON.stringify(proof, null, 2)}\n`);
}
console.log(JSON.stringify({status: proof.status, error: proof.error, proof: resolve(out, 'browser-controls.json')}));
process.exitCode = proof.status === 'passed' ? 0 : proof.status === 'blocked' ? 2 : 1;
