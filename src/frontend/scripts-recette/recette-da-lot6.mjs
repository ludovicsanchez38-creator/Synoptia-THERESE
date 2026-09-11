/**
 * Recette visuelle DA lot 6 : écran Projets et tâches.
 *
 * Ne pas lancer ici : l'orchestrateur la joue sur pile jetable (uvicorn 17393,
 * Vite 1420, jamais 17293). Captures et mesures dans
 * `.cartography-work/validation/da-lot6/`.
 *
 *   FRONTEND_URL=http://localhost:1420 node src/frontend/scripts-recette/recette-da-lot6.mjs
 */
import { chromium } from 'playwright';
import { mkdirSync, writeFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const FRONTEND = process.env.FRONTEND_URL || 'http://localhost:1420';
const ICI = dirname(fileURLToPath(import.meta.url));
const SORTIE = process.env.RECETTE_SORTIE
  || join(ICI, '../../../.cartography-work/validation/da-lot6');

const TACHE = (patch) => ({
  id: 't-1',
  title: 'Relancer Claire Roux pour la facture de juillet',
  description: null,
  status: 'todo',
  priority: 'high',
  due_date: '2026-09-03T00:00:00Z',
  project_id: null,
  contact_id: null,
  tags: [],
  completed_at: null,
  created_at: '2026-09-01T00:00:00Z',
  updated_at: '2026-09-01T00:00:00Z',
  ...patch,
});

/** Cinq tâches : deux en retard, une terminée, les quatre priorités. */
const CINQ = [
  TACHE({}),
  TACHE({
    id: 't-2',
    title: 'Relancer Paul Durand pour le devis',
    priority: 'urgent',
    due_date: '2026-09-04T00:00:00Z',
    tags: ['facturation'],
  }),
  TACHE({
    id: 't-3',
    title: 'Préparer la séance 2 du Garage Benali',
    description: 'Reprendre les plans de l’accueil et la liste des accès.',
    priority: 'medium',
    due_date: '2026-12-18T00:00:00Z',
  }),
  TACHE({
    id: 't-4',
    title: 'Plans de l’accueil, version 2',
    status: 'in_progress',
    priority: 'low',
    due_date: '2026-12-12T00:00:00Z',
  }),
  TACHE({
    id: 't-5',
    title: 'Prise de mesures chez Paul Durand',
    status: 'done',
    priority: 'medium',
    due_date: '2026-08-28T00:00:00Z',
    completed_at: '2026-08-28T00:00:00Z',
  }),
];

const PROJET = (i) => ({
  id: `p-${i}`,
  name: `Projet ${i}`,
  description: i % 2 === 0 ? 'Aménagement de l’accueil' : null,
  status: ['active', 'on_hold', 'completed', 'cancelled'][i % 4],
  contact_id: null,
  budget: i % 3 === 0 ? 1440 : null,
  notes: null,
  tags: null,
  created_at: '2026-08-01T00:00:00Z',
  updated_at: '2026-08-01T00:00:00Z',
});

const TROIS_PROJETS = [PROJET(0), PROJET(1), PROJET(2)];
const DEUX_CENTS = Array.from({ length: 200 }, (_, i) => PROJET(i));

async function intercepter(page, {
  taches = CINQ,
  projets = TROIS_PROJETS,
  statutTaches = 200,
  statutProjets = 200,
  delaiMs = 0,
} = {}) {
  await page.unrouteAll({ behavior: 'ignoreErrors' });
  return Promise.all([
    page.route('**/api/config/onboarding-complete', async (route) => {
      if (route.request().method() === 'GET') {
        await route.fulfill({ json: { completed: true } });
        return;
      }
      await route.continue();
    }),
    page.route('**/api/tasks**', async (route) => {
      if (route.request().method() !== 'GET') {
        await route.continue();
        return;
      }
      if (delaiMs) await new Promise((r) => setTimeout(r, delaiMs));
      if (statutTaches >= 400) {
        await route.fulfill({ status: statutTaches, json: { detail: 'Panne simulée' } });
        return;
      }
      await route.fulfill({ json: taches });
    }),
    page.route('**/api/memory/projects**', async (route) => {
      if (route.request().method() !== 'GET') {
        await route.continue();
        return;
      }
      if (delaiMs) await new Promise((r) => setTimeout(r, delaiMs));
      if (statutProjets >= 400) {
        await route.fulfill({ status: statutProjets, json: { detail: 'Panne simulée' } });
        return;
      }
      await route.fulfill({ json: projets });
    }),
    page.route('**/api/memory/contacts**', async (route) => {
      await route.fulfill({ json: [] });
    }),
  ]);
}

async function ouvrir(page, action, selecteur) {
  await page.goto(FRONTEND, { waitUntil: 'domcontentloaded' });
  await page.waitForFunction(() => Boolean(window.__therese?.runAction), null, { timeout: 20000 });
  await page.evaluate((a) => window.__therese.runAction(a), action);
  if (selecteur) await page.waitForSelector(selecteur, { timeout: 15000 });
}

const ouvrirTaches = (page) => ouvrir(page, 'tasks.open', '[data-testid="tasks-panel"]');
const ouvrirProjets = (page) => ouvrir(page, 'projects.open', 'text=Nouveau projet');

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

async function mesurer(page, racineSelecteur) {
  return page.evaluate((selecteur) => {
    const racine = document.querySelector(selecteur)
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
        // Les segments sont un groupe compact : ils suivent leur primitive.
        if (px < 14 - 0.05 && !el.closest('[role="group"]')) {
          interactifsSous14.push({ texte: (el.textContent || el.getAttribute('aria-label') || '').trim().slice(0, 40), px });
        }
        if (el.tagName === 'BUTTON' && !el.closest('[role="group"]')) {
          const r = el.getBoundingClientRect();
          if (r.height > 0) {
            hauteursBoutons.push({
              nom: (el.getAttribute('aria-label') || el.textContent || '').trim().slice(0, 40),
              h: Math.round(r.height),
            });
          }
        }
      }
      for (const enfant of el.children) visiter(enfant);
    };
    visiter(racine);

    const grille = racine.querySelector('[class*="grid-cols-3"]');
    const colonnes = grille
      ? getComputedStyle(grille).gridTemplateColumns.trim().split(/\s+/).length
      : null;
    const rangees = grille
      ? getComputedStyle(grille).gridTemplateRows.trim().split(/\s+/).length
      : null;
    const listesDefilantes = grille
      ? [...grille.querySelectorAll('[class*="overflow-y-auto"]')].map((l) => ({
          hauteur: Math.round(l.getBoundingClientRect().height),
          debordement: l.scrollHeight > l.clientHeight,
        }))
      : [];
    const derniereTete = [...racine.querySelectorAll('h3')].pop();

    return {
      textesSous12,
      interactifsSous14,
      hauteursBoutons,
      colonnesDeLaGrille: colonnes,
      rangeesDeLaGrille: rangees,
      listesDefilantes,
      basDeLaDerniereTete: derniereTete ? Math.round(derniereTete.getBoundingClientRect().bottom) : null,
      hauteurFenetre: window.innerHeight,
      largeurRacine: Math.round(racine.getBoundingClientRect().width),
      taches: racine.querySelectorAll('[data-testid="task-item"]').length,
      etiquettes: racine.querySelectorAll('[data-etiquette]').length,
      barresDePriorite: racine.querySelectorAll('[role="img"][aria-label^="Priorité"]').length,
      reessayer: [...racine.querySelectorAll('button')].filter((b) => b.textContent.trim() === 'Réessayer').length,
      alertes: racine.querySelectorAll('[role="alert"]').length,
      compteur: racine.querySelector('p.text-sm.text-text-muted')?.textContent?.trim() ?? null,
      // B-217 : dnd-kit sert ses consignes par notre bloc français.
      consignesFrancaises: [...document.querySelectorAll('[id^="DndDescribedBy"]')]
        .every((n) => /barre d’espace/.test(n.textContent || '')),
    };
  }, racineSelecteur);
}

async function capturer(page, nom) {
  const chemin = join(SORTIE, `${nom}.png`);
  await page.screenshot({ path: chemin, fullPage: true });
  return chemin;
}

const RACINE_TACHES = '[data-testid="tasks-panel"]';
// La vue Projets n'a pas de racine propre (le design n'en invente pas) : on
// mesure la région de la coque, dont l'en-tête « Retour » + titre a déjà été
// recetté au lot 1. Un repli sur `document.body` mesurerait toute l'appli.
const RACINE_PROJETS = '[data-testid="prototype-unified-view"][data-view="projects"]';

async function casTaches(page, { largeur, theme, hc, fontPx, vue = 'kanban' }) {
  await page.setViewportSize({ width: largeur, height: 900 });
  await intercepter(page);
  await ouvrirTaches(page);
  await poserApparence(page, { theme, hc, fontPx });
  await page.getByRole('button', { name: vue === 'kanban' ? 'Colonnes' : 'Liste' }).click();
  await page.waitForSelector('[data-testid="task-item"]');
  const nom = `taches-${vue}-${largeur}-${theme}${hc ? '-hc' : ''}-${fontPx}px`;
  await capturer(page, nom);
  return { nom, ...(await mesurer(page, RACINE_TACHES)) };
}

async function main() {
  mkdirSync(SORTIE, { recursive: true });
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({ locale: 'fr-FR' });
  const page = await context.newPage();
  const rapport = [];

  try {
    // --- Colonnes, les trois apparences puis les quatre largeurs
    rapport.push(await casTaches(page, { largeur: 1280, theme: 'light', hc: false, fontPx: 16 }));
    rapport.push(await casTaches(page, { largeur: 1280, theme: 'dark', hc: false, fontPx: 16 }));
    rapport.push(await casTaches(page, { largeur: 1280, theme: 'light', hc: true, fontPx: 16 }));
    rapport.push(await casTaches(page, { largeur: 1024, theme: 'light', hc: false, fontPx: 16 }));
    rapport.push(await casTaches(page, { largeur: 840, theme: 'light', hc: false, fontPx: 16 }));
    rapport.push(await casTaches(page, { largeur: 800, theme: 'light', hc: false, fontPx: 16 }));
    rapport.push(await casTaches(page, { largeur: 1280, theme: 'light', hc: false, fontPx: 14 }));
    rapport.push(await casTaches(page, { largeur: 1280, theme: 'light', hc: false, fontPx: 18 }));

    // --- Liste
    rapport.push(await casTaches(page, { largeur: 1280, theme: 'light', hc: false, fontPx: 16, vue: 'liste' }));
    rapport.push(await casTaches(page, { largeur: 1280, theme: 'dark', hc: false, fontPx: 16, vue: 'liste' }));
    rapport.push(await casTaches(page, { largeur: 800, theme: 'light', hc: false, fontPx: 16, vue: 'liste' }));

    // --- Focus : un segment, puis une carte (anneau du socle, 3 px)
    await page.setViewportSize({ width: 1280, height: 900 });
    await intercepter(page);
    await ouvrirTaches(page);
    await poserApparence(page, { theme: 'light', fontPx: 16 });
    await page.getByRole('button', { name: 'Colonnes' }).focus();
    await capturer(page, 'focus-segment-1280-light-16px');
    const anneauSegment = await page.evaluate(() => {
      const el = document.activeElement;
      const s = getComputedStyle(el);
      return { nom: el.textContent.trim(), outline: s.outlineWidth, style: s.outlineStyle };
    });
    await page.locator('[data-testid="task-item"]').first().evaluate((el) => el.parentElement.focus());
    await capturer(page, 'focus-carte-1280-light-16px');
    const anneauCarte = await page.evaluate(() => {
      const s = getComputedStyle(document.activeElement);
      return { outline: s.outlineWidth, style: s.outlineStyle };
    });
    rapport.push({ nom: 'focus', anneauSegment, anneauCarte });

    // --- Liste vide
    await intercepter(page, { taches: [] });
    await ouvrirTaches(page);
    await page.getByRole('button', { name: 'Liste' }).click();
    await page.getByRole('heading', { name: 'Aucune tâche pour l’instant' }).waitFor();
    await capturer(page, 'taches-vide-1280-light-16px');
    rapport.push({ nom: 'taches-vide', ...(await mesurer(page, RACINE_TACHES)) });

    // --- Titre manquant (état « nouvelle » de la maquette)
    await intercepter(page);
    await ouvrirTaches(page);
    await page.getByRole('button', { name: 'Nouvelle tâche' }).click();
    await page.waitForSelector('#taskform-titre');
    await page.getByRole('button', { name: 'Enregistrer' }).click();
    await page.waitForSelector('#taskform-titre-error');
    await capturer(page, 'taches-titre-manquant-1280-light-16px');
    rapport.push({
      nom: 'taches-titre-manquant',
      message: await page.locator('#taskform-titre-error').textContent(),
      invalide: await page.locator('#taskform-titre').getAttribute('aria-invalid'),
      bandeaux: await page.locator('div[role="alert"]').count(),
    });

    // --- Panne des tâches : zéro Réessayer
    await intercepter(page, { statutTaches: 500 });
    await ouvrirTaches(page);
    await page.locator('[role="alert"]').first().waitFor();
    await capturer(page, 'taches-panne-1280-light-16px');
    rapport.push({ nom: 'taches-panne', ...(await mesurer(page, RACINE_TACHES)) });

    // --- Projets : trois, puis vide, puis le plafond
    for (const [nom, projets] of [['projets-3', TROIS_PROJETS], ['projets-0', []], ['projets-200', DEUX_CENTS]]) {
      for (const theme of nom === 'projets-3' ? ['light', 'dark'] : ['light']) {
        await page.setViewportSize({ width: 1280, height: 900 });
        await intercepter(page, { projets });
        await ouvrirProjets(page);
        await poserApparence(page, { theme, fontPx: 16 });
        await capturer(page, `${nom}-1280-${theme}-16px`);
        rapport.push({ nom: `${nom}-${theme}`, ...(await mesurer(page, RACINE_PROJETS)) });
      }
    }

    // --- Projets à 800 px
    await page.setViewportSize({ width: 800, height: 900 });
    await intercepter(page, { projets: TROIS_PROJETS });
    await ouvrirProjets(page);
    await capturer(page, 'projets-3-800-light-16px');
    rapport.push({ nom: 'projets-3-800', ...(await mesurer(page, RACINE_PROJETS)) });

    // --- Panne des projets : un seul Réessayer
    await page.setViewportSize({ width: 1280, height: 900 });
    await intercepter(page, { statutProjets: 500 });
    await ouvrir(page, 'projets.open', '[role="alert"]');
    await capturer(page, 'projets-panne-1280-light-16px');
    rapport.push({ nom: 'projets-panne', ...(await mesurer(page, RACINE_PROJETS)) });

    // --- Chargement lent des projets : l'attente s'annonce
    await intercepter(page, { projets: TROIS_PROJETS, delaiMs: 8000 });
    const attente = ouvrir(page, 'projets.open', null);
    await page.waitForSelector('[role="status"]', { timeout: 5000 }).catch(() => {});
    await capturer(page, 'projets-chargement-1280-light-16px');
    rapport.push({
      nom: 'projets-chargement',
      annonce: await page.locator('[role="status"]').first().textContent().catch(() => null),
    });
    await attente.catch(() => {});

    // --- Le glisser reste armé à 8 px (BUG-041 / jumeau tâches)
    await intercepter(page);
    await ouvrirTaches(page);
    const carte = page.locator('[data-testid="task-item"]').first();
    const boite = await carte.boundingBox();
    await page.mouse.move(boite.x + 40, boite.y + 12);
    await page.mouse.down();
    await page.mouse.move(boite.x + 40, boite.y + 16);
    // `task-item` est retiré de la carte du glisser : il vaut 1 dans les deux
    // cas et ne prouve rien. C'est le TITRE qui se dédouble quand l'overlay
    // apparaît (même signal que TaskKanban.test.tsx).
    const titre = page.getByText(CINQ[0].title, { exact: true });
    const avant8px = await titre.count();
    await page.mouse.move(boite.x + 40, boite.y + 60);
    const apres8px = await titre.count();
    await capturer(page, 'taches-glisser-1280-light-16px');
    await page.mouse.up();
    rapport.push({ nom: 'glisser', avant8px, apres8px });

    // --- Entrée sur « Marquer terminé » : le KeyboardSensor de dnd-kit écoute
    // tout le sous-arbre du wrapper sortable (pas de setActivatorNodeRef). Si
    // Entrée démarre un glisser au lieu d'activer le bouton, la commande
    // révélée au focus n'est pas activable au clavier. Défaut PRÉ-EXISTANT le
    // cas échéant (même structure avant le lot) : on le mesure, on ne le
    // corrige pas ici.
    const misesAJour = [];
    const espion = (req) => {
      if (/\/api\/tasks\//.test(req.url()) && req.method() !== 'GET') misesAJour.push(req.method());
    };
    await intercepter(page);
    await ouvrirTaches(page);
    page.on('request', espion);
    const commande = page.getByRole('button', { name: 'Marquer terminé' }).first();
    await page.locator('[data-testid="task-item"]').first().evaluate((el) => el.parentElement.focus());
    await commande.focus();
    const titreAvantEntree = await page.getByText(CINQ[0].title, { exact: true }).count();
    await page.keyboard.press('Enter');
    await page.waitForTimeout(500);
    const titreApresEntree = await page.getByText(CINQ[0].title, { exact: true }).count();
    page.off('request', espion);
    await page.keyboard.press('Escape');
    await capturer(page, 'taches-entree-sur-commande-1280-light-16px');
    rapport.push({
      nom: 'entree-sur-commande',
      misesAJour: misesAJour.length,
      titreAvantEntree,
      titreApresEntree,
      focus: await page.evaluate(() => document.activeElement?.getAttribute('aria-label') ?? document.activeElement?.tagName),
    });

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
