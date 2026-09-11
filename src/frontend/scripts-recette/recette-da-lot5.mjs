/**
 * Recette visuelle DA lot 5 : écran Devis et factures.
 *
 * Ne pas lancer ici : l'orchestrateur la joue sur pile jetable (uvicorn 17393,
 * Vite 1420, jamais 17293). Captures et mesures dans
 * `.cartography-work/validation/da-lot5/`.
 *
 *   FRONTEND_URL=http://localhost:1420 node src/frontend/scripts-recette/recette-da-lot5.mjs
 */
import { chromium } from 'playwright';
import { mkdirSync, writeFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const FRONTEND = process.env.FRONTEND_URL || 'http://localhost:1420';
const ICI = dirname(fileURLToPath(import.meta.url));
const SORTIE = process.env.RECETTE_SORTIE
  || join(ICI, '../../../.cartography-work/validation/da-lot5');

const PIECE = (patch) => ({
  id: 'inv-1',
  invoice_number: 'FACT-2026-002',
  contact_id: 'c-claire',
  contact_name: 'Claire Roux',
  document_type: 'facture',
  tva_applicable: true,
  currency: 'EUR',
  issue_date: '2026-07-28T00:00:00Z',
  due_date: '2026-08-25T00:00:00Z',
  status: 'overdue',
  subtotal_ht: 1200,
  total_tax: 240,
  total_ttc: 1440,
  notes: null,
  payment_terms: null,
  payment_method: null,
  late_penalty_rate: null,
  legal_mentions: null,
  converted_from_id: null,
  validite_jours: null,
  payment_date: null,
  created_at: '2026-07-28T00:00:00Z',
  updated_at: '2026-07-28T00:00:00Z',
  lines: [],
  ...patch,
});

const QUATRE = [
  PIECE({}),
  PIECE({
    id: 'd-003',
    invoice_number: 'DEV-2026-003',
    contact_id: 'c-paul',
    contact_name: 'Paul Durand',
    document_type: 'devis',
    status: 'sent',
    issue_date: '2026-09-01T00:00:00Z',
    due_date: '2026-10-01T00:00:00Z',
    total_ttc: 1260,
  }),
  PIECE({
    id: 'd-004',
    invoice_number: 'DEV-2026-004',
    contact_id: 'c-nadia',
    contact_name: 'Garage Benali',
    document_type: 'devis',
    status: 'draft',
    validite_jours: 30,
    issue_date: '2026-09-05T00:00:00Z',
    due_date: '2026-10-05T00:00:00Z',
    total_ttc: 840,
  }),
  PIECE({
    id: 'f-001',
    invoice_number: 'FACT-2026-001',
    status: 'paid',
    payment_date: '2026-07-12T00:00:00Z',
    issue_date: '2026-06-30T00:00:00Z',
    due_date: '2026-07-30T00:00:00Z',
    total_ttc: 3240,
  }),
];

const CONTACT = {
  id: 'contact-1',
  first_name: 'Jean',
  last_name: 'Dupont',
  email: 'jean@example.com',
  company: null,
};

// Les motifs sont des prédicats sur le chemin : le glob `**/api/invoices**` attrapait aussi le
// module Vite `/src/services/api/invoices.ts` et la coque ne démarrait jamais (11/09/2026).
async function intercepter(page, { pieces = QUATRE, profil = { is_complete: true, missing: [] }, delayMs = 0, status = 200 } = {}) {
  await page.unrouteAll({ behavior: 'ignoreErrors' });
  return Promise.all([
    page.route((u) => u.pathname === '/api/config/onboarding-complete', async (route) => {
      if (route.request().method() === 'GET') {
        await route.fulfill({ json: { completed: true } });
        return;
      }
      await route.continue();
    }),
    page.route((u) => u.pathname === '/api/invoices/billing/profile-status', async (route) => {
      await route.fulfill({ json: profil });
    }),
    page.route((u) => u.pathname.startsWith('/api/invoices'), async (route) => {
      const url = route.request().url();
      if (url.includes('billing/profile-status')) {
        await route.fulfill({ json: profil });
        return;
      }
      if (route.request().method() !== 'GET') {
        await route.continue();
        return;
      }
      if (delayMs) await new Promise((r) => setTimeout(r, delayMs));
      if (status >= 400) {
        await route.fulfill({ status, json: { detail: 'Impossible de charger les factures pour le moment.' } });
        return;
      }
      await route.fulfill({ json: pieces });
    }),
    page.route((u) => u.pathname.startsWith('/api/memory/contacts'), async (route) => {
      await route.fulfill({ json: [CONTACT] });
    }),
  ]);
}

async function ouvrirDevis(page) {
  await page.goto(`${FRONTEND}/?prototype=conversation-canvas&scenario=today`, { waitUntil: 'domcontentloaded' });
  await page.waitForFunction(() => Boolean(window.__therese?.runAction), null, { timeout: 20000 });
  await page.evaluate(() => window.__therese.runAction('invoices.open'));
  await page.waitForSelector('[data-testid="invoices-panel"]', { timeout: 15000 });
}

async function poserApparence(page, { theme = 'light', hc = false, fontPx = 16 } = {}) {
  await page.evaluate(({ theme, hc, fontPx }) => {
    const html = document.documentElement;
    html.setAttribute('data-theme', theme);
    if (hc) html.setAttribute('data-high-contrast', 'true');
    else html.removeAttribute('data-high-contrast');
    html.style.fontSize = `${fontPx}px`;
    html.style.setProperty('--therese-root-font-size', `${fontPx}px`);
  }, { theme, hc, fontPx });
}

async function mesurer(page) {
  return page.evaluate(() => {
    const racine = document.querySelector('[data-testid="invoices-panel"]')
      || document.querySelector('[role="dialog"]')
      || document.body;
    const textesSous12 = [];
    const interactifsSous14 = [];
    const hauteursBoutons = [];
    const visiter = (n) => {
      if (n.nodeType !== 1) return;
      const el = n;
      const style = getComputedStyle(el);
      const px = parseFloat(style.fontSize);
      if (el.childNodes.length && [...el.childNodes].some((c) => c.nodeType === 3 && c.textContent.trim()) && px < 12 - 0.05) {
        textesSous12.push({ texte: el.textContent.trim().slice(0, 40), px: Math.round(px * 10) / 10 });
      }
      if (el.matches('button, input, select, textarea, a, [role="button"]')) {
        if (px < 14 - 0.05 && !el.closest('[role="group"]')) {
          interactifsSous14.push({ texte: (el.textContent || el.getAttribute('aria-label') || '').trim().slice(0, 40), px });
        }
        if (el.tagName === 'BUTTON' && !el.closest('[role="group"]')) {
          const r = el.getBoundingClientRect();
          hauteursBoutons.push({
            nom: (el.getAttribute('aria-label') || el.textContent || '').trim().slice(0, 40),
            h: Math.round(r.height),
          });
        }
      }
      for (const enfant of el.children) visiter(enfant);
    };
    visiter(racine);
    const geste = [...racine.querySelectorAll('button')].find((b) => /Nouveau devis|Nouvelle facture/.test(b.textContent || ''));
    const carte = racine.querySelector('section');
    return {
      textesSous12: textesSous12.length,
      interactifsSous14: interactifsSous14.length,
      hauteursBoutons,
      hauteurGeste: geste ? Math.round(geste.getBoundingClientRect().height) : null,
      largeurCarte: carte ? Math.round(carte.getBoundingClientRect().width) : null,
      largeurPanneau: Math.round(racine.getBoundingClientRect().width),
      compteur: document.querySelector('[data-testid="invoices-compteur"]')?.textContent ?? null,
      reessayer: [...racine.querySelectorAll('button')].filter((b) => b.textContent.trim() === 'Réessayer').length,
      etiquettes: racine.querySelectorAll('[data-etiquette]').length,
      avoirs: [...racine.querySelectorAll('button')].some((b) => b.textContent.trim() === 'Avoirs'),
    };
  });
}

async function capturer(page, nom) {
  const chemin = join(SORTIE, `${nom}.png`);
  await page.screenshot({ path: chemin, fullPage: true });
  return chemin;
}

async function casListe(page, { largeur, theme, hc, fontPx, suffixe }) {
  await page.setViewportSize({ width: largeur, height: 900 });
  await intercepter(page, { pieces: QUATRE });
  await ouvrirDevis(page);
  await poserApparence(page, { theme, hc, fontPx });
  await page.waitForSelector('[data-testid="invoice-item"]');
  const nom = `liste-${largeur}-${theme}${hc ? '-hc' : ''}-${fontPx}px${suffixe || ''}`;
  await capturer(page, nom);
  const mesures = await mesurer(page);
  return { nom, ...mesures };
}

async function main() {
  mkdirSync(SORTIE, { recursive: true });
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({ locale: 'fr-FR' });
  const page = await context.newPage();
  const rapport = [];

  try {
    rapport.push(await casListe(page, { largeur: 1280, theme: 'light', hc: false, fontPx: 16 }));
    rapport.push(await casListe(page, { largeur: 1280, theme: 'dark', hc: false, fontPx: 16 }));
    rapport.push(await casListe(page, { largeur: 1280, theme: 'light', hc: true, fontPx: 16 }));
    rapport.push(await casListe(page, { largeur: 1024, theme: 'light', hc: false, fontPx: 16 }));
    rapport.push(await casListe(page, { largeur: 840, theme: 'light', hc: false, fontPx: 16 }));
    rapport.push(await casListe(page, { largeur: 800, theme: 'light', hc: false, fontPx: 16 }));
    rapport.push(await casListe(page, { largeur: 1280, theme: 'light', hc: false, fontPx: 14 }));
    rapport.push(await casListe(page, { largeur: 1280, theme: 'light', hc: false, fontPx: 18 }));

    // Focus sur le bouton client
    await page.setViewportSize({ width: 1280, height: 900 });
    await intercepter(page, { pieces: QUATRE });
    await ouvrirDevis(page);
    await poserApparence(page, { theme: 'light', fontPx: 16 });
    await page.locator('[data-testid="invoice-item"] button').first().focus();
    await capturer(page, 'focus-client-1280-light-16px');
    rapport.push({ nom: 'focus-client', focus: await page.evaluate(() => document.activeElement?.textContent?.trim()) });

    // Vide sans filtre
    await intercepter(page, { pieces: [] });
    await ouvrirDevis(page);
    await page.waitForSelector('[data-testid="invoices-empty"]');
    await capturer(page, 'vide-1280-light-16px');
    rapport.push({ nom: 'vide', ...(await mesurer(page)) });

    // Vide overdue
    await intercepter(page, { pieces: [] });
    await ouvrirDevis(page);
    await page.getByRole('button', { name: 'En retard' }).click();
    await page.waitForSelector('[data-testid="invoices-empty-overdue"]');
    await capturer(page, 'vide-overdue-1280-light-16px');
    rapport.push({ nom: 'vide-overdue', ...(await mesurer(page)) });

    // Vide autre filtre (payée)
    await page.getByRole('button', { name: 'Toutes' }).click();
    await page.getByRole('button', { name: 'Payée' }).click();
    await page.waitForSelector('[data-testid="invoices-empty-filtre"]');
    await capturer(page, 'vide-paid-1280-light-16px');
    rapport.push({ nom: 'vide-paid', ...(await mesurer(page)) });

    // Chargement lent
    await intercepter(page, { pieces: QUATRE, delayMs: 8000 });
    const attente = ouvrirDevis(page);
    await page.waitForSelector('[role="status"]', { timeout: 5000 }).catch(() => {});
    await capturer(page, 'chargement-1280-light-16px');
    rapport.push({ nom: 'chargement', statut: await page.locator('[role="status"]').count() });
    await attente.catch(() => {});

    // 500
    await intercepter(page, { status: 500 });
    await ouvrirDevis(page);
    await page.waitForSelector('[data-testid="invoices-load-error"]');
    await capturer(page, 'erreur-1280-light-16px');
    rapport.push({ nom: 'erreur', ...(await mesurer(page)) });

    // Formulaire nouveau, ligne 2 vide
    await intercepter(page, { pieces: QUATRE });
    await ouvrirDevis(page);
    await page.getByRole('button', { name: /Nouveau devis|Nouvelle facture/ }).click();
    await page.waitForSelector('#invoice-form');
    await page.getByLabel('Client *').selectOption('contact-1');
    await page.getByRole('button', { name: /Ajouter une ligne/ }).click();
    await page.getByLabel('Description ligne 1').fill('Conception et plans');
    await page.locator('#invoice-form').evaluate((form) => form.requestSubmit());
    await page.waitForSelector('#invoiceform-description-1-erreur');
    await capturer(page, 'formulaire-ligne2-vide-1280-light-16px');
    const focusId = await page.evaluate(() => document.activeElement?.id);
    rapport.push({
      nom: 'formulaire-ligne2',
      erreurLigne2: await page.locator('#invoiceform-description-1-erreur').textContent(),
      focusId,
    });

    // Profil incomplet
    await intercepter(page, { pieces: QUATRE, profil: { is_complete: false, missing: ['SIRET', 'adresse'] } });
    await ouvrirDevis(page);
    await page.getByRole('button', { name: /Nouveau devis|Nouvelle facture/ }).click();
    await page.waitForSelector('#invoice-form');
    await page.getByText(/Infos de ta société incomplètes/).waitFor();
    await capturer(page, 'profil-incomplet-1280-light-16px');
    rapport.push({ nom: 'profil-incomplet', bandeau: true });

    writeFileSync(join(SORTIE, 'apres-mesures.json'), JSON.stringify(rapport, null, 2));
    console.log(JSON.stringify({ sortie: SORTIE, cas: rapport.length }, null, 2));
  } finally {
    await browser.close();
  }
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
