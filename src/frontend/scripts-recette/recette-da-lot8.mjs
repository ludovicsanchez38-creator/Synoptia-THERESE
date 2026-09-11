/**
 * Recette visuelle DA lot 8 : l'écran Agenda.
 *
 * Ne pas lancer ici : l'orchestrateur la joue sur pile jetable (uvicorn 17393,
 * Vite 1420, jamais 17293). Captures et mesures dans
 * `.cartography-work/validation/da-lot8/`.
 *
 *   FRONTEND_URL=http://localhost:1420 node src/frontend/scripts-recette/recette-da-lot8.mjs
 */
import { chromium } from 'playwright';
import { mkdirSync, writeFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const FRONTEND = process.env.FRONTEND_URL || 'http://localhost:1420';
const ICI = dirname(fileURLToPath(import.meta.url));
const SORTIE = process.env.RECETTE_SORTIE
  || join(ICI, '../../../.cartography-work/validation/da-lot8');

/** La semaine de la maquette : mercredi 2 septembre 2026 est « aujourd'hui ». */
const LUNDI = '2026-08-31';
const AUJOURDHUI = '2026-09-02';

const AGENDA_LOCAL = {
  id: 'cal-local',
  account_id: null,
  summary: 'Agenda Atelier Exemple',
  description: null,
  timezone: 'Europe/Paris',
  primary: true,
  provider: 'local',
  synced_at: null,
};
const AGENDA_CALDAV = { ...AGENDA_LOCAL, id: 'cal-dav', summary: 'Agenda CalDAV', provider: 'caldav', primary: false };

const RDV = (patch) => ({
  id: 'evt',
  calendar_id: 'cal-local',
  summary: 'Rendez-vous',
  description: null,
  location: null,
  start_datetime: null,
  end_datetime: null,
  start_date: null,
  end_date: null,
  all_day: false,
  attendees: null,
  recurrence: null,
  status: 'confirmed',
  synced_at: null,
  ...patch,
});

/**
 * Six rendez-vous : un long avec lieu, deux qui se CHEVAUCHENT, un de
 * 45 minutes (le seuil chiffré du § 3 : l'horaire doit y rester lisible), un
 * « toute la journée » pour la rangée « Journée », un hors de la colonne du
 * jour courant.
 */
const SEMAINE = [
  RDV({
    id: 'evt-1',
    summary: 'Séance 1 · Garage Benali',
    location: 'sur place',
    start_datetime: `${AUJOURDHUI}T09:00:00`,
    end_datetime: `${AUJOURDHUI}T10:30:00`,
  }),
  RDV({
    id: 'evt-2',
    summary: 'Point chantier Roux',
    location: 'visio',
    start_datetime: `${AUJOURDHUI}T14:00:00`,
    end_datetime: `${AUJOURDHUI}T15:00:00`,
  }),
  RDV({
    id: 'evt-3',
    summary: 'Lucie Fabre, découverte',
    location: 'téléphone',
    start_datetime: `${AUJOURDHUI}T14:30:00`,
    end_datetime: `${AUJOURDHUI}T15:30:00`,
  }),
  RDV({
    id: 'evt-4',
    summary: 'Appel éclair, quarante-cinq minutes',
    location: 'atelier',
    start_datetime: `${AUJOURDHUI}T16:00:00`,
    end_datetime: `${AUJOURDHUI}T16:45:00`,
  }),
  RDV({
    id: 'evt-5',
    summary: 'Salon pro',
    all_day: true,
    start_date: AUJOURDHUI,
    end_date: AUJOURDHUI,
  }),
  RDV({
    id: 'evt-6',
    summary: 'Devis Paul Durand',
    start_datetime: `${LUNDI}T10:00:00`,
    end_datetime: `${LUNDI}T11:00:00`,
  }),
];

/**
 * Prédicats sur le chemin plutôt que globs : `**\/api/calendar**` attraperait
 * le module Vite `/src/services/api/calendar.ts` et la coque ne démarrerait
 * jamais (défaut constaté aux lots 5 et 6).
 */
async function intercepter(page, {
  agendas = [AGENDA_LOCAL],
  evenements = SEMAINE,
  statutAgendas = 200,
  messageAgendas = 'Panne simulée',
  statutEvenements = 200,
  delaiMs = 0,
} = {}) {
  await page.unrouteAll({ behavior: 'ignoreErrors' });
  return Promise.all([
    page.route((u) => u.pathname === '/api/config/onboarding-complete', async (route) => {
      if (route.request().method() === 'GET') {
        await route.fulfill({ json: { completed: true } });
        return;
      }
      await route.continue();
    }),
    page.route((u) => u.pathname === '/api/email/auth/status', async (route) => {
      await route.fulfill({ json: { connected: false, accounts: [] } });
    }),
    page.route((u) => u.pathname === '/api/calendar/calendars', async (route) => {
      if (route.request().method() !== 'GET') {
        await route.continue();
        return;
      }
      if (delaiMs) await new Promise((r) => setTimeout(r, delaiMs));
      if (statutAgendas >= 400) {
        await route.fulfill({ status: statutAgendas, json: { detail: messageAgendas } });
        return;
      }
      await route.fulfill({ json: agendas });
    }),
    page.route((u) => u.pathname === '/api/calendar/sync', async (route) => {
      await route.fulfill({ json: { synced_at: `${AUJOURDHUI}T11:48:00Z`, events_synced: 0 } });
    }),
    page.route((u) => u.pathname === '/api/calendar/events', async (route) => {
      if (route.request().method() !== 'GET') {
        await route.continue();
        return;
      }
      if (delaiMs) await new Promise((r) => setTimeout(r, delaiMs));
      if (statutEvenements >= 400) {
        await route.fulfill({ status: statutEvenements, json: { detail: 'Panne simulée' } });
        return;
      }
      await route.fulfill({ json: evenements });
    }),
  ]);
}

const RACINE = '[data-testid="calendar-panel"]';

async function ouvrir(page, { attendre = RACINE } = {}) {
  await page.goto(`${FRONTEND}/?prototype=conversation-canvas&scenario=today`, { waitUntil: 'domcontentloaded' });
  await page.waitForFunction(() => Boolean(window.__therese?.runAction), null, { timeout: 20000 });
  await page.evaluate(() => window.__therese.runAction('calendar.open'));
  if (attendre) await page.waitForSelector(attendre, { timeout: 15000 });
}

async function choisirVue(page, libelle) {
  await page.getByRole('group', { name: "Vue de l'agenda" }).getByRole('button', { name: libelle, exact: true }).click();
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
  return page.evaluate((selecteur) => {
    const racine = document.querySelector(selecteur) || document.body;
    const textesSous12 = [];
    const interactifsSous14 = [];
    const hauteursBoutons = [];
    // Les segments suivent leur primitive (28 px) : on les mesure à part
    // plutôt que de les effacer du rapport.
    const segments = [];
    const visiter = (el) => {
      if (el.nodeType !== 1) return;
      const style = getComputedStyle(el);
      const px = parseFloat(style.fontSize);
      const porteDuTexte = el.childNodes.length
        && [...el.childNodes].some((c) => c.nodeType === 3 && c.textContent.trim());
      if (porteDuTexte && px < 12 - 0.05) {
        textesSous12.push({ texte: el.textContent.trim().slice(0, 40), px: Math.round(px * 10) / 10 });
      }
      if (el.matches('button, input, select, textarea, a, [role="button"]')) {
        const dansUnGroupe = Boolean(el.closest('[role="group"]'));
        if (px < 14 - 0.05 && !dansUnGroupe) {
          interactifsSous14.push({
            texte: (el.textContent || el.getAttribute('aria-label') || '').trim().slice(0, 40),
            px: Math.round(px * 10) / 10,
          });
        }
        if (el.tagName === 'BUTTON') {
          const r = el.getBoundingClientRect();
          if (r.height > 0) {
            const mesure = { nom: (el.getAttribute('aria-label') || el.textContent || '').trim().slice(0, 40), h: Math.round(r.height) };
            if (dansUnGroupe) segments.push({ ...mesure, px: Math.round(px * 10) / 10 });
            else hauteursBoutons.push(mesure);
          }
        }
      }
      for (const enfant of el.children) visiter(enfant);
    };
    visiter(racine);

    const gabarits = [...racine.querySelectorAll('div')].filter((d) =>
      /grid-cols-\[3\.5rem_repeat\(7,1fr\)\]/.test(d.className || ''));
    // Le décalage que la gouttière de barre de défilement provoque : sur macOS
    // les barres sont en surcouche et l'écart est nul ; ailleurs il vaut la
    // largeur de la barre, et c'est exactement ce qu'on cherche à voir.
    const largeursDesGabarits = gabarits.map((g) => Math.round(g.getBoundingClientRect().width));
    const xDesTraits = gabarits.slice(0, 2).map((g) =>
      [...g.children].slice(1).map((c) => Math.round(c.getBoundingClientRect().left)));
    const piste = racine.querySelector('[class*="overflow-y-auto"][class*="scrollbar-gutter"]');

    const grilleMois = racine.querySelector('div.grid-cols-7');
    const carteDefilante = racine.querySelector('section[class*="overflow-y-auto"]');
    const pied = [...racine.querySelectorAll('p')].find((p) => /Agenda local|aucun agenda en ligne/.test(p.textContent || ''));
    const gouttiereJournee = gabarits[1]?.firstElementChild;

    return {
      textesSous12,
      interactifsSous14,
      hauteursBoutons,
      segments,
      gabarits: gabarits.length,
      largeursDesGabarits,
      xDesTraits,
      // Les traits des trois gabarits doivent tomber au même x : sinon la
      // gouttière n'est pas réservée pareil (§ 3.1).
      traitsAlignes: xDesTraits.length === 2 && xDesTraits[0].every((x, i) => x === xDesTraits[1][i]),
      pisteDefile: piste ? piste.scrollHeight > piste.clientHeight : null,
      pisteScrollTop: piste ? Math.round(piste.scrollTop) : null,
      repereDeLHeure: (() => {
        const r = racine.querySelector('[role="img"]');
        return r ? { nom: r.getAttribute('aria-label'), gauche: Math.round(r.getBoundingClientRect().left) } : null;
      })(),
      gouttiereDesHeures: (() => {
        const g = gabarits[2]?.firstElementChild;
        return g ? Math.round(g.getBoundingClientRect().right) : null;
      })(),
      libelleJournee: gouttiereJournee
        ? {
            texte: gouttiereJournee.textContent.trim(),
            px: Math.round(parseFloat(getComputedStyle(gouttiereJournee).fontSize) * 10) / 10,
            // Tronqué ? La largeur du contenu dépasse-t-elle les 3,5 rem ?
            deborde: gouttiereJournee.scrollWidth > gouttiereJournee.clientWidth + 1,
          }
        : null,
      mois: grilleMois
        ? {
            enfants: grilleMois.children.length,
            rangees: getComputedStyle(grilleMois).gridTemplateRows.trim().split(/\s+/).length,
            carteDefile: carteDefilante ? carteDefilante.scrollHeight > carteDefilante.clientHeight : null,
            hautDesEntetes: Math.round(grilleMois.children[0].getBoundingClientRect().top),
            basDeLaGrille: Math.round(grilleMois.getBoundingClientRect().bottom),
            basDeLaCarte: carteDefilante ? Math.round(carteDefilante.getBoundingClientRect().bottom) : null,
          }
        : null,
      pied: pied
        ? {
            texte: pied.textContent.trim(),
            bas: Math.round(pied.getBoundingClientRect().bottom),
            hauteur: Math.round(pied.getBoundingClientRect().height),
          }
        : null,
      blocs: [...racine.querySelectorAll('section button[style*="top"]')].map((b) => ({
        nom: b.textContent.trim().slice(0, 48),
        gauche: b.style.left,
        largeur: b.style.width,
        h: Math.round(b.getBoundingClientRect().height),
        // Deux lignes tiennent-elles encore ? Le § 3 les chiffre à 44 px.
        rogne: b.scrollHeight > b.clientHeight + 1,
      })),
      reessayer: [...racine.querySelectorAll('button')].filter((b) => b.textContent.trim() === 'Réessayer').length,
      synchroniser: racine.querySelectorAll('button[aria-label="Synchroniser l\'agenda"]').length,
      alertes: racine.querySelectorAll('[role="alert"]').length,
      bandeauPerime: racine.querySelector('[data-testid="calendar-stale-warning"]')?.textContent?.trim() ?? null,
      periode: racine.querySelector('#agenda-periode')?.textContent?.trim() ?? null,
      sectionsNommees: [...racine.querySelectorAll('section')].map((s) => s.getAttribute('aria-labelledby')),
      nomDuSelecteur: racine.querySelector('select')?.getAttribute('aria-label') ?? null,
      optionsDuSelecteur: racine.querySelectorAll('select option').length,
      creationDAgenda: /[Cc]réer un (agenda|calendrier)/.test(racine.textContent || ''),
      hauteurFenetre: window.innerHeight,
      largeurRacine: Math.round(racine.getBoundingClientRect().width),
    };
  }, RACINE);
}

async function capturer(page, nom) {
  const chemin = join(SORTIE, `${nom}.png`);
  await page.screenshot({ path: chemin, fullPage: true });
  return chemin;
}

async function cas(page, { nom, largeur, hauteur = 900, theme = 'light', hc = false, fontPx = 16, vue = 'Semaine', options = {} }) {
  await page.setViewportSize({ width: largeur, height: hauteur });
  await intercepter(page, options);
  await ouvrir(page);
  await poserApparence(page, { theme, hc, fontPx });
  await choisirVue(page, vue);
  await page.waitForTimeout(300);
  const etiquette = `${nom}-${largeur}x${hauteur}-${theme}${hc ? '-hc' : ''}-${fontPx}px`;
  await capturer(page, etiquette);
  return { nom: etiquette, ...(await mesurer(page)) };
}

async function main() {
  mkdirSync(SORTIE, { recursive: true });
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({ locale: 'fr-FR', timezoneId: 'Europe/Paris' });
  // L'horloge est posée sur l'instant de la maquette : sans elle, « aujourd'hui »
  // serait le jour du run, la colonne teintée changerait de place et le repère
  // de l'heure sortirait de la fenêtre 8-20 la moitié du temps.
  await context.clock.install({ time: new Date(`${AUJOURDHUI}T11:48:00`) });
  const page = await context.newPage();
  const rapport = [];

  try {
    // --- Semaine : trois apparences, quatre largeurs, deux hauteurs, trois polices
    rapport.push(await cas(page, { nom: 'semaine', largeur: 1280, theme: 'light' }));
    rapport.push(await cas(page, { nom: 'semaine', largeur: 1280, theme: 'dark' }));
    rapport.push(await cas(page, { nom: 'semaine', largeur: 1280, theme: 'light', hc: true }));
    rapport.push(await cas(page, { nom: 'semaine', largeur: 1024 }));
    rapport.push(await cas(page, { nom: 'semaine', largeur: 840 }));
    rapport.push(await cas(page, { nom: 'semaine', largeur: 800 }));
    rapport.push(await cas(page, { nom: 'semaine', largeur: 1280, hauteur: 640 }));
    rapport.push(await cas(page, { nom: 'semaine', largeur: 1280, fontPx: 14 }));
    rapport.push(await cas(page, { nom: 'semaine', largeur: 1280, fontPx: 18 }));

    // --- Mois : les deux hauteurs décident si la sixième semaine est atteignable
    rapport.push(await cas(page, { nom: 'mois', largeur: 1280, vue: 'Mois', theme: 'light' }));
    rapport.push(await cas(page, { nom: 'mois', largeur: 1280, vue: 'Mois', theme: 'dark' }));
    rapport.push(await cas(page, { nom: 'mois', largeur: 1280, hauteur: 640, vue: 'Mois' }));
    rapport.push(await cas(page, { nom: 'mois', largeur: 800, vue: 'Mois' }));

    // --- Jour et Liste
    rapport.push(await cas(page, { nom: 'jour', largeur: 1280, vue: 'Jour' }));
    rapport.push(await cas(page, { nom: 'jour', largeur: 1280, hauteur: 640, vue: 'Jour' }));
    rapport.push(await cas(page, { nom: 'liste', largeur: 1280, vue: 'Liste' }));
    rapport.push(await cas(page, { nom: 'liste-vide', largeur: 1280, vue: 'Liste', options: { evenements: [] } }));

    // --- Libellé de semaine à cheval sur deux mois (la semaine de la maquette
    //     commence le 31 août et finit le 6 septembre)
    rapport.push({
      nom: 'libelle-semaine-a-cheval',
      periode: await page.locator('#agenda-periode').textContent().catch(() => null),
    });

    // --- Cache périmé : 500 sur les événements, du cache déjà là
    await page.setViewportSize({ width: 1280, height: 900 });
    await intercepter(page);
    await ouvrir(page);
    await page.waitForSelector('section[aria-labelledby="agenda-periode"]');
    await intercepter(page, { statutEvenements: 500 });
    await page.getByRole('button', { name: "Synchroniser l'agenda" }).click();
    await page.waitForSelector('[data-testid="calendar-stale-warning"]', { timeout: 10000 }).catch(() => {});
    await capturer(page, 'perime-1280x900-light-16px');
    rapport.push({ nom: 'perime', ...(await mesurer(page)) });

    // --- 403 Google sur les agendas, cache présent
    await intercepter(page, {
      statutAgendas: 403,
      messageAgendas: 'Google Calendar API has not been used in project 42 before or it is disabled.',
    });
    await page.getByRole('button', { name: "Synchroniser l'agenda" }).click();
    await page.waitForTimeout(800);
    await capturer(page, 'google-403-1280x900-light-16px');
    rapport.push({ nom: 'google-403', ...(await mesurer(page)) });

    // --- 403 agendas PUIS échec des événements : UN SEUL bandeau qui dit les deux
    await intercepter(page, {
      statutAgendas: 403,
      messageAgendas: 'Google Calendar API has not been used in project 42 before or it is disabled.',
      statutEvenements: 500,
    });
    await page.getByRole('button', { name: "Synchroniser l'agenda" }).click();
    await page.waitForTimeout(800);
    await capturer(page, 'fusionne-1280x900-light-16px');
    rapport.push({ nom: 'fusionne', ...(await mesurer(page)) });

    // --- Reconnexion : « Reconnecter », jamais « Réessayer »
    await intercepter(page, {
      statutAgendas: 401,
      messageAgendas: 'OAuth credentials not found. Please reconnect your account.',
    });
    await ouvrir(page);
    await page.waitForTimeout(800);
    await capturer(page, 'reconnexion-1280x900-light-16px');
    rapport.push({ nom: 'reconnexion', ...(await mesurer(page)) });

    // --- Chargement lent : squelettes, et l'attente s'annonce
    await intercepter(page, { delaiMs: 8000 });
    const attente = ouvrir(page, { attendre: null });
    await page.waitForSelector('[role="status"]', { timeout: 6000 }).catch(() => {});
    await capturer(page, 'chargement-1280x900-light-16px');
    rapport.push({
      nom: 'chargement',
      annonce: await page.locator('[role="status"]').first().textContent().catch(() => null),
      barres: await page.locator(`${RACINE} [aria-hidden="true"] > div`).count().catch(() => 0),
      largeursDesBarres: await page.evaluate((sel) =>
        [...document.querySelectorAll(`${sel} [aria-hidden="true"]`)]
          .map((s) => Math.round(s.getBoundingClientRect().width)), RACINE),
    });
    await attente.catch(() => {});

    // --- Aucun agenda du tout (BUG-143) : pas de pied, pas de création
    await intercepter(page, { agendas: [], evenements: [] });
    await ouvrir(page);
    await page.waitForTimeout(500);
    await capturer(page, 'aucun-agenda-1280x900-light-16px');
    rapport.push({ nom: 'aucun-agenda', ...(await mesurer(page)) });

    // --- Un CalDAV branché : le suffixe « aucun agenda en ligne » disparaît
    await intercepter(page, { agendas: [AGENDA_LOCAL, AGENDA_CALDAV] });
    await ouvrir(page);
    await page.waitForTimeout(500);
    await capturer(page, 'caldav-1280x900-light-16px');
    rapport.push({ nom: 'caldav', ...(await mesurer(page)) });

    // --- Ouverture de « Nouveau rendez-vous » : le formulaire remplace la grille
    await intercepter(page);
    await ouvrir(page);
    await page.getByRole('button', { name: 'Nouveau rendez-vous' }).click();
    await page.waitForSelector('#eventform-titre');
    await capturer(page, 'nouveau-1280x900-light-16px');
    rapport.push({
      nom: 'nouveau',
      agenda: await page.locator('#eventform-agenda').inputValue(),
      lectureSeule: await page.locator('#eventform-agenda').getAttribute('aria-readonly'),
      requis: await page.evaluate(() =>
        ['titre', 'date-de-debut', 'heure-de-debut', 'date-de-fin', 'heure-de-fin']
          .map((id) => document.getElementById(`eventform-${id}`)?.required ?? null)),
      grilleEncoreLa: await page.locator('section[aria-labelledby="agenda-periode"]').count(),
      pied: await page.locator(`${RACINE} p:text-matches("Agenda local")`).count(),
    });

    // --- Focus : un bloc de la grille, puis un segment (anneau 3 px, rentrant)
    await intercepter(page);
    await ouvrir(page);
    await choisirVue(page, 'Semaine');
    await page.locator('section button[style*="top"]').first().focus();
    await capturer(page, 'focus-bloc-1280x900-light-16px');
    const anneauBloc = await page.evaluate(() => {
      const s = getComputedStyle(document.activeElement);
      return { outline: s.outlineWidth, style: s.outlineStyle, offset: s.outlineOffset, nom: document.activeElement.textContent.trim().slice(0, 40) };
    });
    await page.getByRole('group', { name: "Vue de l'agenda" }).getByRole('button', { name: 'Mois', exact: true }).focus();
    await capturer(page, 'focus-segment-1280x900-light-16px');
    const anneauSegment = await page.evaluate(() => {
      const s = getComputedStyle(document.activeElement);
      return { outline: s.outlineWidth, style: s.outlineStyle, offset: s.outlineOffset };
    });
    rapport.push({ nom: 'focus', anneauBloc, anneauSegment });

    // --- Le quadrillage survit au fond opaque de la colonne du jour (z-[1])
    rapport.push({
      nom: 'empilement',
      lignesDHeure: await page.evaluate(() =>
        [...document.querySelectorAll('section [class*="border-t"][class*="absolute"]')]
          .slice(0, 3)
          .map((l) => getComputedStyle(l).zIndex)),
      colonneDuJour: await page.evaluate(() => {
        const c = document.querySelector('section [class*="bg-surface-2"]');
        return c ? { zIndex: getComputedStyle(c).zIndex, fond: getComputedStyle(c).backgroundColor } : null;
      }),
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
