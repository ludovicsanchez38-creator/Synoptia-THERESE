/**
 * B-761 (cycle 9) : sous 840 px, le bouton de recherche de l'en-tête doit garder
 * un nom accessible qui commence par « Rechercher » (le mot passait en
 * display:none et le nom devenait « ⌘K »). jsdom n'applique pas les media
 * queries : la preuve se joue en navigateur réel, sur pile jetable
 * (uvicorn 17393 + Vite 1420, jamais 17293). Lancer depuis la racine du dépôt :
 *   node src/frontend/scripts-recette/recette-rechercher-800.mjs
 */
import { chromium } from 'playwright';
const FRONT = process.env.FRONTEND_URL || 'http://127.0.0.1:1420';
const browser = await chromium.launch({ headless: true });
const resultats = [];
for (const width of [800, 840, 1024]) {
  const page = await browser.newPage({ viewport: { width, height: 760 } });
  await page.goto(`${FRONT}/?prototype=conversation-canvas&scenario=today`, { waitUntil: 'domcontentloaded' });
  await page.getByRole('button', { name: 'Contrôle des données' }).waitFor();
  const bouton = page.getByRole('button', { name: /^Rechercher/ });
  const present = await bouton.count();
  resultats.push({ width, boutonNommeRechercher: present === 1 });
  await page.close();
}
await browser.close();
console.log(JSON.stringify(resultats));
if (!resultats.every((r) => r.boutonNommeRechercher)) process.exit(1);
