// Mesure partielle de la vue Mémoire sur la pile jetable (Vite 1420 + moteur
// 17393, contacts présents). Un cas indéterminé exige une inspection : il ne
// suffit pas d'avoir sousAA=0 pour déclarer la recette conforme.
import { chromium } from 'playwright';
import { mesurerContrasteTexte } from './mesurer-contraste-texte.mjs';
const FRONT = 'http://127.0.0.1:1420';
const b = await chromium.launch({ headless: true });
const res = {};
for (const theme of ['light', 'dark']) {
  const ctx = await b.newContext({ viewport: { width: 1280, height: 900 }, colorScheme: theme });
  const p = await ctx.newPage();
  await p.goto(`${FRONT}/?prototype=conversation-canvas&scenario=today`, { waitUntil: 'domcontentloaded' });
  await p.waitForTimeout(1500);
  await p.evaluate(() => window.__therese.runAction('memory.open'));
  await p.getByTestId('memory-panel').waitFor();
  await p.waitForTimeout(2000);
  res[theme] = await p.evaluate(mesurerContrasteTexte, { selector: '[data-testid="memory-panel"]' });
  await ctx.close();
}
await b.close();
console.log(JSON.stringify(res, null, 1));
if (Object.values(res).some(result => result.sousAA > 0)) process.exitCode = 1;
else if (Object.values(res).some(result => result.verdict === 'indetermine')) process.exitCode = 2;
