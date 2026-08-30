import { chromium } from 'playwright';
import { writeFileSync, mkdirSync } from 'node:fs';
import { join } from 'node:path';

const OUT = '/tmp/therese-audit-da';
mkdirSync(OUT, { recursive: true });

const browser = await chromium.launch({ headless: true, channel: 'chrome' });
const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });

await page.goto('http://localhost:1420/?port=18500', { waitUntil: 'domcontentloaded' });
await page.waitForSelector('[data-testid="conversation-canvas-prototype"]', { timeout: 20000 });
await page.waitForTimeout(600);

async function shot(name) {
  await page.screenshot({ path: join(OUT, name + '.png') });
}

async function setTheme(t) {
  await page.evaluate((theme) => {
    document.documentElement.setAttribute('data-theme', theme);
    document.querySelectorAll('[data-theme]').forEach(el => el.setAttribute('data-theme', theme));
  }, t);
  await page.waitForTimeout(200);
}

// Brancher mes mails
await page.getByRole('button', { name: /Brancher mes mails/i }).click().catch(()=>{});
await page.waitForTimeout(800);
await shot('20-email-clair');
await setTheme('dark');
await shot('21-email-sombre');
await setTheme('light');

// Accueil then open contacts full
await page.getByLabel('Accueil').click().catch(()=>{});
await page.waitForTimeout(300);
await page.getByRole('button', { name: 'Retrouver' }).click().catch(()=>{});
await page.waitForTimeout(400);
await page.getByRole('button', { name: 'Ouvrir Contacts' }).first().click().catch(()=>{});
await page.waitForTimeout(800);
await shot('22-contacts-clair');
await setTheme('dark');
await shot('23-contacts-sombre');
await setTheme('light');

// Agenda full
await page.getByLabel('Accueil').click().catch(()=>{});
await page.waitForTimeout(300);
await page.getByRole('button', { name: 'Préparer' }).click().catch(()=>{});
await page.waitForTimeout(400);
await page.getByRole('button', { name: 'Ouvrir Agenda' }).first().click().catch(()=>{});
await page.waitForTimeout(800);
await shot('24-agenda-clair');
await setTheme('dark');
await shot('25-agenda-sombre');
await setTheme('light');

// Plus d'outils -> Activité (pipeline)
await page.getByLabel('Accueil').click().catch(()=>{});
await page.waitForTimeout(300);
await page.getByLabel("Plus d’outils").click().catch(async () => {
  await page.getByLabel("Plus d'outils").click().catch(()=>{});
});
await page.waitForTimeout(400);
await page.getByText('Activité', { exact: true }).click().catch(()=>{});
await page.waitForTimeout(300);
await shot('26-tiroir-activite-clair');
await page.getByText('Pipeline', { exact: true }).click().catch(()=>{});
await page.waitForTimeout(800);
await shot('27-pipeline-clair');
await setTheme('dark');
await shot('28-pipeline-sombre');
await setTheme('light');

// Factures via activité / création
await page.getByLabel('Accueil').click().catch(()=>{});
await page.waitForTimeout(300);
await page.getByLabel("Plus d’outils").click().catch(async () => {
  await page.getByLabel("Plus d'outils").click().catch(()=>{});
});
await page.waitForTimeout(400);
await page.getByText('Création', { exact: true }).click().catch(()=>{});
await page.waitForTimeout(300);
await shot('29-tiroir-creation-clair');
await page.getByText('Devis et factures', { exact: false }).first().click().catch(()=>{});
await page.waitForTimeout(800);
await shot('30-factures-clair');
await setTheme('dark');
await shot('31-factures-sombre');
await setTheme('light');

// Atelier
await page.getByLabel('Accueil').click().catch(()=>{});
await page.waitForTimeout(300);
await page.getByLabel("Plus d’outils").click().catch(async () => {
  await page.getByLabel("Plus d'outils").click().catch(()=>{});
});
await page.waitForTimeout(400);
await page.getByText('Décision', { exact: true }).click().catch(()=>{});
await page.waitForTimeout(300);
await shot('32-tiroir-decision-clair');
await page.getByText(/Améliorer|Atelier|agents/i).first().click().catch(()=>{});
await page.waitForTimeout(800);
await shot('33-atelier-clair');
await setTheme('dark');
await shot('34-atelier-sombre');
await setTheme('light');

// Settings > Accessibilité + IA
await page.getByLabel('Paramètres').click().catch(()=>{});
await page.waitForTimeout(500);
await page.getByRole('button', { name: 'Accessibilité' }).click().catch(()=>{});
await page.waitForTimeout(500);
await shot('35-accessibilite-clair');
await page.getByRole('button', { name: 'IA' }).click().catch(()=>{});
await page.waitForTimeout(500);
await shot('36-ia-clair');
await setTheme('dark');
await shot('37-ia-sombre');
await setTheme('light');

// Focus ring: tab from body
await page.keyboard.press('Escape');
await page.waitForTimeout(300);
await page.keyboard.press('Tab');
await page.keyboard.press('Tab');
await page.keyboard.press('Tab');
await page.waitForTimeout(200);
await shot('38-focus-clair');
await setTheme('dark');
await shot('39-focus-sombre');

// Nouveau projet button close-up via projets
await setTheme('light');
await page.getByLabel('Projets').click().catch(()=>{});
await page.waitForTimeout(500);
const btn = page.getByRole('button', { name: /Nouveau projet/i });
if (await btn.count()) {
  await btn.hover();
  await shot('40-nouveau-projet-hover-clair');
}

writeFileSync(join(OUT, 'pass2.txt'), 'ok');
console.log('done pass2');
await browser.close();
