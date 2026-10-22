/** R6 : rendu des vrais composants/CSS, Chrome par pipe, aucun serveur ni réseau. */
import { createRequire } from 'node:module';
import { readFile, writeFile, mkdir } from 'node:fs/promises';
import { createWriteStream, openSync } from 'node:fs';
import { resolve } from 'node:path';
import { spawn } from 'node:child_process';
import assert from 'node:assert/strict';

const root = resolve(import.meta.dirname, '../../..');
const source = resolve(process.argv[2] || root);
const phase = process.argv[3] || 'apres';
const reglages = process.argv[4] === 'reglages';
const box = resolve(root, '.recette-r6/browser', phase);
await mkdir(box, { recursive: true });
const require = createRequire(resolve(root, 'src/frontend/package.json'));
const { build } = require('esbuild');
const { compile } = require('@tailwindcss/node');
const { Scanner } = require('@tailwindcss/oxide');
const styles = resolve(source, 'src/frontend/src/styles');
const css = await compile(await readFile(resolve(styles, 'globals.css'), 'utf8'), { base: styles, onDependency() {} });
const scanner = new Scanner({ sources: [{ base: resolve(source, 'src/frontend/src'), pattern: '**/*.{tsx,ts}', negated: false }] });
await writeFile(resolve(box, 'style.css'), css.build(scanner.scan()));
await writeFile(resolve(box, 'entry.tsx'), `
import React from '${root}/src/frontend/node_modules/react';
import { createRoot } from '${root}/src/frontend/node_modules/react-dom/client';
import { OnboardingWizard } from '${source}/src/frontend/src/components/onboarding/OnboardingWizard';
import { usePanelStore } from '${source}/src/frontend/src/stores/panelStore';
import { ConversationCanvasPrototype } from '${source}/src/frontend/src/components/prototype/ConversationCanvasPrototype';
window.catalogueTermine = false;
window.fetch = async (url) => {
  const path = new URL(url).pathname;
  let data = {};
  if (path.includes('/llm/models/')) {
    await new Promise(resolve => { window.livrerCatalogue = resolve; });
    window.catalogueTermine = true;
    data = { models: ['claude-opus-5-5'] };
  } else if (path.endsWith('/config/llm')) data = { provider: 'mistral', model: 'mistral-medium-latest', available_models: [], available: true };
  else if (path.endsWith('/processing-tasks')) data = { traitements: [] };
  else if (path.endsWith('/profile')) data = null;
  else if (path.endsWith('/projects') || path.endsWith('/contacts') || path.endsWith('/conversations')) data = [];
  else if (path.endsWith('/ollama/status')) data = { available: false, models: [] };
  else if (path.endsWith('/system-resources')) data = null;
  else if (path.endsWith('/config/')) data = { api_keys: {}, corrupted_keys: [] };
  else return new Response(JSON.stringify({ detail: 'Indisponible dans cette doublure' }), { status: 503 });
  return new Response(JSON.stringify(data), { status: 200 });
};
${reglages ? "usePanelStore.getState().openSettings('profile');" : ''}
createRoot(document.getElementById('root')).render(${reglages ? '<ConversationCanvasPrototype />' : '<OnboardingWizard isOpen onComplete={() => {}} />'});
`);
await build({ entryPoints: [resolve(box, 'entry.tsx')], outfile: resolve(box, 'bundle.js'), bundle: true,
  format: 'iife', platform: 'browser', jsx: 'automatic', nodePaths: [resolve(root, 'src/frontend/node_modules')],
  define: { 'import.meta.env': '{}', 'process.env.NODE_ENV': '"test"' }, loader: { '.png': 'dataurl', '.jpg': 'dataurl', '.webp': 'dataurl', '.svg': 'dataurl' }, logLevel: 'silent' });
await writeFile(resolve(box, 'index.html'), '<!doctype html><meta charset="utf-8"><link rel="stylesheet" href="style.css"><div id="root"></div><script src="bundle.js"></script>');
// Un chemin Unix fait au plus 108 octets : le worktree a un long chemin.
// Ce descripteur garde tous les fichiers temporaires dans le worktree.
const tmpFd = openSync(box, 'r');
const chrome = spawn('/usr/bin/google-chrome', ['--headless', '--no-sandbox', '--disable-gpu', '--disable-dev-shm-usage',
  '--disable-crash-reporter', '--disable-breakpad', '--disable-background-networking', '--disable-component-update', '--disable-sync', '--no-first-run',
  '--host-resolver-rules=MAP * ~NOTFOUND', '--remote-debugging-pipe', `--user-data-dir=${box}/profile`, 'about:blank'],
  { env: { ...process.env, TMPDIR: `/proc/${process.pid}/fd/${tmpFd}` }, stdio: ['ignore', 'ignore', 'pipe', 'pipe', 'pipe'] });
chrome.on('exit', (code, signal) => console.log('Chrome terminé', code, signal));
chrome.stderr.pipe(createWriteStream(resolve(box, 'chrome.log')));
chrome.stdio[3].on('error', () => {});
let seq = 0, buffer = '';
const erreurs = [];
const pending = new Map();
chrome.stdio[4].on('error', () => {});
chrome.stdio[4].on('data', (chunk) => {
  buffer += chunk.toString();
  while (buffer.includes('\0')) {
    const index = buffer.indexOf('\0');
    const event = JSON.parse(buffer.slice(0, index)); buffer = buffer.slice(index + 1);
    if (event.method === 'Runtime.exceptionThrown') erreurs.push({ erreur: event.params.exceptionDetails.exception?.description || event.params.exceptionDetails.text, trace: event.params.exceptionDetails.stackTrace });
    if (event.method === 'Runtime.consoleAPICalled' && event.params.type === 'error') erreurs.push(event.params.args.map(a => a.description || a.value).join(' '));
    if (event.id && pending.has(event.id)) {
      const { resolve, reject, timer } = pending.get(event.id); pending.delete(event.id); clearTimeout(timer);
      if (event.error) reject(new Error(JSON.stringify(event.error))); else resolve(event.result);
    }
  }
});
function cdp(method, params = {}, sessionId) {
  return new Promise((resolve, reject) => {
    const id = ++seq;
    const timer = setTimeout(() => reject(new Error(`Délai CDP : ${method}`)), 15000);
    pending.set(id, { resolve, reject, timer });
    chrome.stdio[3].write(JSON.stringify({ id, method, params, sessionId }) + '\0');
  });
}
const results = [];
try {
  const { targetId } = await cdp('Target.createTarget', { url: 'about:blank' });
  const { sessionId } = await cdp('Target.attachToTarget', { targetId, flatten: true });
  await cdp('Runtime.enable', {}, sessionId);
  const evaluate = async (expression) => {
    const result = await cdp('Runtime.evaluate', { expression, returnByValue: true, awaitPromise: true }, sessionId);
    if (result.exceptionDetails) throw new Error(JSON.stringify(result.exceptionDetails));
    return result.result.value;
  };
  // Les pauses courtes permettent au navigateur de peindre et aux animations de finir.
  const pause = (ms) => new Promise(resolve => setTimeout(resolve, ms));
  for (const [width, height] of [[1238, 792], [800, 600], [480, 520]]) {
    await cdp('Emulation.setDeviceMetricsOverride', { width, height, deviceScaleFactor: 1, mobile: false }, sessionId);
    await cdp('Page.navigate', { url: `file://${box}/index.html` }, sessionId);
    if (reglages) {
      for (let i = 0; i < 80; i++) {
        if (await evaluate('Boolean(document.getElementById("settings-profile-name"))')) break;
        await pause(100);
      }
      await evaluate('document.getElementById("settings-profile-name").focus()');
      await cdp('Input.insertText', { text: 'Camille brouillon' }, sessionId);
      await cdp('Input.dispatchKeyEvent', { type: 'keyDown', key: 'k', code: 'KeyK', modifiers: 2 }, sessionId);
      await cdp('Input.dispatchKeyEvent', { type: 'keyUp', key: 'k', code: 'KeyK', modifiers: 2 }, sessionId);
      await pause(600);
      const paletteActive = await evaluate(`(() => {
        const c = document.querySelector('[role=combobox]');
        return Boolean(c && document.activeElement === c && !c.closest('[inert]'));
      })()`);
      await cdp('Input.dispatchKeyEvent', { type: 'keyDown', key: 'Escape', code: 'Escape', windowsVirtualKeyCode: 27 }, sessionId);
      await cdp('Input.dispatchKeyEvent', { type: 'keyUp', key: 'Escape', code: 'Escape', windowsVirtualKeyCode: 27 }, sessionId);
      await pause(600);
      const retour = await evaluate(`(() => {
        const c = document.getElementById('settings-profile-name');
        return Boolean(c && document.activeElement === c && !c.closest('[inert]') && c.value === 'Camille brouillon');
      })()`);
      await cdp('Input.dispatchKeyEvent', { type: 'keyDown', key: 'k', code: 'KeyK', modifiers: 2 }, sessionId);
      await cdp('Input.dispatchKeyEvent', { type: 'keyUp', key: 'k', code: 'KeyK', modifiers: 2 }, sessionId);
      await pause(400);
      await cdp('Input.insertText', { text: 'devis et factures' }, sessionId);
      await pause(200);
      await evaluate(`[...document.querySelectorAll('[role=option]')].find(e => e.textContent.includes('Ouvrir les Devis et factures')).click()`);
      await pause(600);
      const destinationVisible = await evaluate(`(() => {
        const c = document.querySelector('[data-testid=conversation-canvas-prototype]');
        return c?.dataset.embeddedView === 'invoices' && !c.closest('[inert]') && !document.querySelector('[data-testid=settings-modal]');
      })()`);
      results.push({ width, height, paletteActive, retour, destinationVisible });
      continue;
    }
    for (let i = 0; i < 50; i++) {
      if (await evaluate('Boolean(document.querySelector("[data-testid=onboarding-next-btn]"))')) break;
      await pause(100);
    }
    await evaluate('document.querySelector("[data-testid=onboarding-next-btn]").click()');
    await pause(850);
    // Agrandir le formulaire comme un dirigeant qui choisit la facturation.
    await evaluate('[...document.querySelectorAll("button")].find(b => b.textContent.includes("Je facture avec")).click()');
    await pause(100);
    const footer = await evaluate(`(() => {
      const ids = ['prev', 'skip', 'next'];
      const buttons = ids.map(id => document.querySelector('[data-testid=onboarding-' + id + '-btn]'));
      const rects = buttons.map(b => { const r = b.getBoundingClientRect(); return { top: r.top, bottom: r.bottom, left: r.left, right: r.right }; });
      const visible = buttons.every(b => { const r = b.getBoundingClientRect(); const hit = document.elementFromPoint(r.left + r.width/2, r.top + r.height/2); return r.top >= 0 && r.bottom <= innerHeight && (hit === b || b.contains(hit)); });
      return { visible, rects };
    })()`);
    results.push({ width, height, footer });
    // Le clic DOM permet de poursuivre le diagnostic même sur le code rouge.
    await evaluate('document.querySelector("[data-testid=onboarding-skip-btn]").click()');
    await pause(850);
    const attente = await evaluate(`(() => {
      const el = [...document.querySelectorAll('[role=status]')].find(e => e.textContent.includes('Actualisation de la liste'));
      if (!el) return false;
      const r = el.getBoundingClientRect();
      return r.height > 0 && r.top >= 0 && r.bottom <= innerHeight && getComputedStyle(el).opacity !== '0' && !window.catalogueTermine;
    })()`);
    await pause(2100);
    const attentePersistante = await evaluate("[...document.querySelectorAll('[role=status]')].some(e => e.textContent.includes('Actualisation de la liste')) && !window.catalogueTermine");
    await evaluate('window.livrerCatalogue()');
    await pause(300);
    const termine = await evaluate("window.catalogueTermine && ![...document.querySelectorAll('[role=status]')].some(e => e.textContent.includes('Actualisation de la liste'))");
    Object.assign(results.at(-1), { attente, attentePersistante, termine });
    const screenshot = await cdp('Page.captureScreenshot', { format: 'png' }, sessionId);
    await writeFile(resolve(box, `${width}x${height}.png`), Buffer.from(screenshot.data, 'base64'));
  }
  await writeFile(resolve(box, 'resultats.json'), JSON.stringify(results, null, 2));
  console.log(JSON.stringify(results, null, 2));
  if (reglages) {
    assert(results.every(r => r.paletteActive && r.retour && r.destinationVisible), 'Ctrl+K doit conserver le brouillon à Échap et montrer la destination choisie');
  } else {
  const mode = process.argv[4] || 'tout';
  if (mode !== 'catalogue') assert(results.every(r => r.footer.visible), 'Les trois boutons doivent rester visibles sans défilement');
  assert(results.every(r => r.attente && r.attentePersistante && r.termine), 'Le catalogue lent doit afficher un indicateur jusqu’à sa réponse');
  }
} finally {
  await writeFile(resolve(box, 'erreurs-rendu.json'), JSON.stringify(erreurs, null, 2));
  chrome.kill('SIGTERM');
}
