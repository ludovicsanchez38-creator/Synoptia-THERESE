// Recette browser B-937/B-942 sur composants réels et données jetables.
// node scripts-recette/recette-attente-chat.mjs
import assert from 'node:assert/strict';
import { chromium } from 'playwright';
import { build } from 'esbuild';
import { readFile } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';

const frontend = fileURLToPath(new URL('../', import.meta.url));
const css = await readFile(new URL('../src/styles/globals.css', import.meta.url), 'utf8');
const reductionCss = css.slice(css.indexOf('@media (prefers-reduced-motion: reduce)'), css.indexOf('/* Animations */'));
const bundle = await build({
  absWorkingDir: frontend, bundle: true, write: false, format: 'iife', platform: 'browser', jsx: 'automatic',
  define: { 'process.env.NODE_ENV': '"production"', 'import.meta.env': '{"DEV":false,"VITE_THERESE_BACKEND_PORT":1}' },
  stdin: { loader: 'tsx', resolveDir: frontend, contents: `
    import { createRoot } from 'react-dom/client';
    import { MotionConfig } from 'framer-motion';
    import { MessageList } from './src/components/chat/MessageList';
    import { useChatStore } from './src/stores/chatStore';
    import { useAccessibilityStore } from './src/stores/accessibilityStore';
    useAccessibilityStore.setState({ reduceMotion: window.fixtureMode === 'always' });
    useChatStore.setState({ currentConversationId: 'fixture', fournisseurCourant: 'ollama', conversations: [{
      id: 'fixture', title: 'Recherche jetable', createdAt: new Date(), updatedAt: new Date(), synced: true,
      messages: [{ id: 'u', role: 'user', content: 'Question jetable', timestamp: new Date() }]
    }] });
    const store = useChatStore.getState();
    store.setStreaming(true);
    const assistantId = store.addMessage({ role: 'assistant', content: '', isStreaming: true });
    window.fixtureFirstResearchChunk = () => store.updateMessage(assistantId, 'Premier extrait du rapport');
    window.fixtureFinish = () => { store.updateMessage(assistantId, 'Rapport terminé'); store.setStreaming(false); };
    window.fixtureReduceMotion = reduce => useAccessibilityStore.getState().setReduceMotion(reduce);
    createRoot(document.getElementById('root')).render(
      <MotionConfig reducedMotion={window.fixtureMode}><MessageList /></MotionConfig>
    );
  ` },
});

const browser = await chromium.launch({ headless: true });
const results = [];
try {
  for (const scenario of [
    { mode: 'always', system: 'no-preference', application: true },
    { mode: 'user', system: 'reduce', application: false },
    { mode: 'user', system: 'no-preference', application: false },
  ]) {
    const context = await browser.newContext({ reducedMotion: scenario.system, viewport: { width: 1000, height: 700 } });
    const page = await context.newPage();
    const errors = [];
    page.on('pageerror', error => errors.push(error.message));
    await page.route('**/*', route => route.request().isNavigationRequest()
      ? route.fulfill({ contentType: 'text/html', body: '<!doctype html><title>Fixture chat</title>' })
      : route.abort());
    await page.goto('http://127.0.0.1:14299/');
    await page.setContent(`<!doctype html><html${scenario.application ? ' data-reduce-motion="true"' : ''}><head><style>
      html,body,#root { height: 100%; margin: 0; } body { font: 16px sans-serif; }
      .h-full { height: 100%; } .flex { display: flex; } .flex-col { flex-direction: column; } .flex-1 { flex: 1; } .min-h-0 { min-height: 0; }
      .w-2 { width: 8px; } .h-2 { height: 8px; } .bg-accent-cyan { background: cyan; }
      ${reductionCss}
    </style></head><body><div id="root"></div></body></html>`);
    await page.evaluate(mode => { window.fixtureMode = mode; }, scenario.mode);
    await page.addScriptTag({ content: bundle.outputFiles[0].text });
    await page.getByText(/Avec un modèle local/).waitFor();
    assert.equal(await page.getByText(/plusieurs minutes/).count(), 1);
    assert.equal(await page.getByText('Réflexion...', { exact: true }).count(), 0);
    await page.evaluate(() => window.fixtureFirstResearchChunk());
    await page.getByText('Réflexion...', { exact: true }).waitFor();
    assert.equal(await page.getByText(/plusieurs minutes/).count(), 1);

    const sample = () => page.evaluate(() => [...document.querySelectorAll('.w-2.h-2')].map(point => ({
      transform: getComputedStyle(point).transform,
      opacity: getComputedStyle(point).opacity,
      animations: point.getAnimations().filter(animation => animation.playState === 'running').length,
    })));
    await page.waitForTimeout(900);
    const samples = [];
    for (let index = 0; index < 5; index++) {
      samples.push(await sample());
      await page.waitForTimeout(270);
    }
    const reduced = scenario.application || scenario.system === 'reduce';
    const opacities = samples.map(points => Number(points[0]?.opacity));
    assert.equal(samples.every(points => points.length === 3), true);
    if (reduced) {
      assert.ok(samples.flat().every(point => point.transform === 'none' && point.opacity === '1' && point.animations === 0));
    } else {
      assert.ok(Math.max(...opacities) - Math.min(...opacities) > .1, 'le témoin normal doit vraiment être animé');
      assert.ok(new Set(samples.map(points => points[0].transform)).size > 1);
      // Changement de préférence système pendant l'attente, sans remontage.
      await page.emulateMedia({ reducedMotion: 'reduce' });
      await page.waitForTimeout(100);
      assert.ok((await sample()).every(point => point.transform === 'none' && point.opacity === '1' && point.animations === 0));
      await page.emulateMedia({ reducedMotion: 'no-preference' });
      await page.waitForTimeout(100);
      // Même garantie lors du changement du réglage applicatif.
      await page.evaluate(() => window.fixtureReduceMotion(true));
      await page.waitForTimeout(100);
      assert.ok((await sample()).every(point => point.transform === 'none' && point.opacity === '1' && point.animations === 0));
    }
    await page.evaluate(() => window.fixtureFinish());
    await page.getByText(/plusieurs minutes/).waitFor({ state: 'detached' });
    assert.deepEqual(errors, []);
    results.push({ scenario, samples, passed: true });
    await context.close();
  }
  console.log(JSON.stringify({ passed: true, browser: browser.version(), results }, null, 2));
} finally {
  await browser.close();
}
