/**
 * Recette visuelle DA lot 7 : l'écran Décision (Board).
 *
 * Ne pas lancer ici : l'orchestrateur la joue sur pile jetable (uvicorn 17393,
 * Vite 1420, jamais 17293). Captures et mesures dans
 * `.cartography-work/validation/da-lot7/`.
 *
 *   FRONTEND_URL=http://localhost:1420 node src/frontend/scripts-recette/recette-da-lot7.mjs
 *
 * États forcés par interception : `**\/api/board/decisions*` et
 * `**\/api/board/advisors` par `page.route`, le flux SSE de
 * `**\/api/board/deliberate` par un `window.fetch` de recette posé en
 * `addInitScript`.
 *
 * POURQUOI un fetch de recette et pas `route.fulfill` pour le SSE : `fulfill`
 * envoie un corps complet et ferme la connexion ; le `for await` de
 * `streamDeliberation` se termine, et sans événement `done` le hook bascule en
 * `error` (« Flux interrompu », `usePrototypeBoardData.ts`). On capturerait
 * `partiel` en croyant capturer `encours`. Le stub rend une `Response` dont le
 * `ReadableStream` n'est JAMAIS fermé quand l'état voulu est `running` : la
 * délibération reste en cours tant que la page vit. Le même stub sert l'état
 * `partiel`, en fermant le flux après les avis rendus et sans `done`.
 *
 * CE SCRIPT N'A PAS ÉTÉ EXÉCUTÉ (pas de pile dans l'arbre de travail du lot) :
 * si l'état `encours` ne se fige pas, lire d'abord la console de la page, le
 * stub de `fetch` étant le seul point mobile.
 */
import { chromium } from 'playwright';
import { mkdirSync, writeFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const FRONTEND = process.env.FRONTEND_URL || 'http://localhost:1420';
const ICI = dirname(fileURLToPath(import.meta.url));
const SORTIE = process.env.RECETTE_SORTIE
  || join(ICI, '../../../.cartography-work/validation/da-lot7');

const QUESTION = 'Faut-il accepter la mission du Garage Benali à 840 € avec un délai de trois semaines ?';

/**
 * La question de la délibération lancée par la recette est DIFFÉRENTE de
 * celle de la décision enregistrée : pendant un run, la carte porte deux
 * rangées (le run en cours, puis la liste), et deux rangées de même libellé
 * rendraient le clic ambigu — on ouvrirait le run en croyant ouvrir le détail.
 */
const QUESTION_RUN = 'Faut-il ouvrir un second créneau de pose le samedi matin en septembre ?';

const CONSEILLERS = [
  { role: 'analyst', name: "L'Analyste", emoji: '', color: '', personality: 'Données et mesures' },
  { role: 'strategist', name: 'Le Stratège', emoji: '', color: '', personality: 'Vision et positionnement' },
  { role: 'devil', name: "L'Avocat du Diable", emoji: '', color: '', personality: 'Ce qui peut mal tourner' },
  { role: 'pragmatic', name: 'Le Pragmatique', emoji: '', color: '', personality: 'Charge et calendrier' },
  { role: 'visionary', name: 'Le Visionnaire', emoji: '', color: '', personality: 'Attentes et relation' },
];

const SYNTHESE = {
  consensus_points: [
    'Un acompte de 30 % sécurise la trésorerie pendant que Claire Roux tarde à payer.',
    'Une date écrite vaut mieux qu’un délai annoncé.',
  ],
  divergence_points: [
    'Le délai : accepté tel quel par le Stratège, conditionné par le Pragmatique.',
    'Le prix : suffisant pour trois conseillers, juste pour l’Analyste.',
  ],
  recommendation: 'Accepter, à deux conditions.',
  confidence: 'high',
  next_steps: [
    'Confirmer l’acompte avant de bloquer l’agenda.',
    'Déplacer la séance 2 au 10 septembre.',
  ],
};

const AVIS = (role, name) => ({
  role,
  name,
  emoji: '',
  content: `### Ce que je retiens\n\n- **${name}** : le montant couvre la conception et deux journées de pose.\n- Il laisse peu de marge si le chantier déborde.`,
  provider: 'ollama',
  model: 'mistral-small',
  cost_eur: 0.0021,
});

const DECISION = {
  id: 'decision-1',
  question: QUESTION,
  context: 'Agenda déjà chargé la semaine du 22, Claire Roux n’a pas réglé la facture de juillet.',
  opinions: CONSEILLERS.map((c) => AVIS(c.role, c.name)),
  synthesis: SYNTHESE,
  mode: 'sovereign',
  created_at: '2026-09-04T17:12:00Z',
  web_sources: [{ title: 'Barème de pose 2026', url: 'https://exemple.test/bareme', snippet: 'Les tarifs de pose observés en 2026 vont de 45 à 70 € de l’heure selon la région.' }],
  synthesis_usage: { provider: 'ollama', model: 'mistral-small', cost_eur: 0.0009 },
};

/** Une question longue (90 caractères) : la coupe des rangées se prouve là. */
const LISTE = [
  { id: 'decision-1', question: QUESTION, context: DECISION.context, recommendation: SYNTHESE.recommendation, confidence: 'high', mode: 'sovereign', created_at: '2026-09-04T17:12:00Z' },
  { id: 'decision-2', question: 'Faut-il embaucher un apprenti à la rentrée plutôt que sous-traiter la pose ?', recommendation: 'Sous-traiter cette saison, embaucher au printemps.', confidence: 'medium', mode: 'cloud', created_at: '2026-08-28T09:30:00Z' },
  { id: 'decision-3', question: 'Faut-il refuser les chantiers à plus de 40 km ?', recommendation: 'Non, mais facturer le déplacement.', confidence: 'low', created_at: '2026-08-12T11:05:00Z' },
  { id: 'decision-4', question: 'Faut-il passer le devis type de 15 à 30 jours de validité ?', recommendation: 'Oui, 30 jours.', confidence: 'high', mode: 'cloud', created_at: '2026-07-30T16:40:00Z' },
  { id: 'decision-5', question: 'Faut-il reprendre la facturation au forfait ?', recommendation: 'Au forfait pour la conception, au temps passé pour la pose.', confidence: 'medium', mode: 'sovereign', created_at: '2026-07-02T08:15:00Z' },
];

/** Les événements SSE d'une délibération, dans l'ordre du backend. */
function evenementsDuFlux({ rendus, cinquiemeAvecTexte = false }) {
  const flux = [{ type: 'task', content: 'tache-1' }, { type: 'web_search_start' }, { type: 'web_search_done' }];
  CONSEILLERS.slice(0, rendus).forEach((c) => {
    flux.push({ type: 'advisor_start', role: c.role, name: c.name, provider: 'ollama' });
    flux.push({ type: 'advisor_chunk', role: c.role, content: AVIS(c.role, c.name).content });
    flux.push({ type: 'advisor_done', role: c.role });
  });
  if (cinquiemeAvecTexte) {
    const c = CONSEILLERS[4];
    flux.push({ type: 'advisor_start', role: c.role, name: c.name, provider: 'ollama' });
    flux.push({ type: 'advisor_chunk', role: c.role, content: 'Je commençais à peine à répondre quand le' });
  }
  return flux;
}

/**
 * Le stub de `window.fetch` pour le seul `/api/board/deliberate`.
 * `ferme: false` laisse la délibération en cours (état `encours`).
 */
async function poserLeFluxSSE(page, { evenements, ferme }) {
  await page.addInitScript(({ evenements, ferme }) => {
    const vrai = window.fetch.bind(window);
    window.fetch = (entree, init) => {
      const url = typeof entree === 'string' ? entree : entree?.url ?? '';
      if (!url.includes('/api/board/deliberate')) return vrai(entree, init);
      const encodeur = new TextEncoder();
      const flux = new ReadableStream({
        start(controleur) {
          for (const evenement of evenements) {
            controleur.enqueue(encodeur.encode(`data: ${JSON.stringify(evenement)}\n\n`));
          }
          // Pas de `close()` quand la délibération doit rester en cours.
          if (ferme) controleur.close();
        },
      });
      return Promise.resolve(new Response(flux, {
        status: 200,
        headers: { 'Content-Type': 'text/event-stream' },
      }));
    };
  }, { evenements, ferme });
}

async function intercepter(page, { liste = LISTE, detail = DECISION, status = 200, delaiMs = 0 } = {}) {
  await page.route('**/api/board/advisors', (route) => route.fulfill({ json: CONSEILLERS }));
  await page.route('**/api/board/decisions*', async (route) => {
    if (delaiMs) await new Promise((ok) => setTimeout(ok, delaiMs));
    if (status >= 400) {
      await route.fulfill({ status, json: { detail: 'La base locale des décisions est illisible.' } });
      return;
    }
    const url = new URL(route.request().url());
    const estUnDetail = /\/api\/board\/decisions\/[^/]+$/.test(url.pathname);
    await route.fulfill({ json: estUnDetail ? detail : liste });
  });
}

async function ouvrirDecision(page) {
  await page.goto(`${FRONTEND}/?prototype=conversation-canvas&scenario=board`, { waitUntil: 'domcontentloaded' });
  await page.getByTestId('conversation-canvas-prototype').waitFor({ timeout: 20000 });
}

async function poserApparence(page, { theme = 'light', hc = false, fontPx = 16 } = {}) {
  await page.evaluate(({ theme, hc, fontPx }) => {
    const html = document.documentElement;
    if (theme === 'dark' || hc) html.setAttribute('data-theme', 'dark');
    else html.removeAttribute('data-theme');
    if (hc) html.setAttribute('data-high-contrast', 'true');
    else html.removeAttribute('data-high-contrast');
    const coque = document.querySelector('[data-testid="conversation-canvas-prototype"]');
    if (coque) {
      if (hc) coque.setAttribute('data-high-contrast', 'true');
      else coque.removeAttribute('data-high-contrast');
    }
    html.style.fontSize = `${fontPx}px`;
  }, { theme, hc, fontPx });
}

/**
 * Les mesures que jsdom ne peut pas rendre. Le nombre de colonnes de la
 * grille des avis est LA mesure du lot : le design l'annonce à une colonne à
 * 1280 px (panneau à 43 %) et à deux en dessous (calque plafonné à 620 px).
 */
async function mesurer(page) {
  return page.evaluate(() => {
    const cs = (el) => (el ? getComputedStyle(el) : null);
    const r = (el) => (el ? el.getBoundingClientRect() : null);
    const carte = document.querySelector('[data-testid="board-history-card"]');
    const canevas = document.querySelector('[data-testid="board-run-view"]')
      || document.querySelector('[data-testid="board-decision-detail"]')
      || document.querySelector('[data-testid="board-new-form"]');
    const racine = canevas || carte || document.body;
    const panneau = document.querySelector('[role="region"]');

    const textesSous12 = [];
    const interactifsSous14 = [];
    const boutons = [];
    const visiter = (el) => {
      if (!el || el.nodeType !== 1) return;
      const px = parseFloat(cs(el).fontSize);
      const aDuTexte = [...el.childNodes].some((n) => n.nodeType === 3 && n.textContent.trim());
      if (aDuTexte && px < 12 - 0.05) textesSous12.push({ texte: el.textContent.trim().slice(0, 40), px });
      if (el.matches('button, input, select, textarea, a, [role="radio"]')) {
        if (px < 14 - 0.05) interactifsSous14.push({ texte: (el.textContent || el.getAttribute('aria-label') || '').trim().slice(0, 40), px });
        if (el.tagName === 'BUTTON') boutons.push({ nom: (el.getAttribute('aria-label') || el.textContent || '').trim().slice(0, 40), h: Math.round(r(el).height) });
      }
      for (const enfant of el.children) visiter(enfant);
    };
    visiter(racine);
    if (canevas && carte) visiter(carte);

    // Colonnes de la grille des avis : compté sur les positions réelles.
    const grille = document.querySelector('[class*="minmax(16rem,1fr)"]');
    const cartesAvis = grille ? [...grille.children] : [];
    const gauches = new Set(cartesAvis.map((c) => Math.round(r(c).left)));
    const largeursAvis = cartesAvis.map((c) => Math.round(r(c).width));

    // La dernière rangée d'historique doit rester dans les coins arrondis.
    const rangees = carte ? [...carte.querySelectorAll('[class*="grid-cols-[2rem_1fr_auto]"]')] : [];
    const derniere = rangees[rangees.length - 1];

    // Le bouton destructeur doit se distinguer du fond de son bloc.
    const blocAnnulation = document.querySelector('[data-testid="board-cancel-confirmation"]');
    const confirmer = blocAnnulation
      ? [...blocAnnulation.querySelectorAll('button')].find((b) => /Confirmer/.test(b.textContent))
      : null;

    const metaAvis = cartesAvis[0]?.querySelector('p');
    const barre = document.querySelector('[role="progressbar"]');
    const statut = racine.querySelector('[data-etiquette]');
    const question = racine.querySelector('h3');
    const synthese = document.querySelector('[data-testid="board-synthesis"]');
    const squelettes = [...document.querySelectorAll('[aria-hidden="true"] > div[class*="animate-"]')].map((b) => Math.round(r(b).width));

    return {
      textesSous12: textesSous12.length,
      detailTextesSous12: textesSous12.slice(0, 4),
      interactifsSous14: interactifsSous14.length,
      detailInteractifsSous14: interactifsSous14.slice(0, 4),
      hauteursBoutons: boutons,
      largeurPanneau: panneau ? Math.round(r(panneau).width) : null,
      largeurCarteHistorique: carte ? Math.round(r(carte).width) : null,
      colonnesAvis: gauches.size,
      largeursAvis,
      carteOverflow: carte ? cs(carte).overflow : null,
      derniereRangeeDansLaCarte: derniere && carte
        ? Math.round(r(derniere).bottom) <= Math.round(r(carte).bottom)
        : null,
      fondDeLaRangeeDuRun: (() => {
        const enveloppe = document.querySelector('[data-testid="board-current-run"]');
        const rangee = enveloppe?.querySelector('[class*="grid-cols-[2rem_1fr_auto]"]');
        return rangee ? cs(rangee).backgroundColor : null;
      })(),
      annulation: blocAnnulation && confirmer
        ? {
            fondDuBloc: cs(blocAnnulation).backgroundColor,
            fondDuBouton: cs(confirmer).backgroundColor,
            distincts: cs(blocAnnulation).backgroundColor !== cs(confirmer).backgroundColor,
          }
        : null,
      metaAvisCoupee: metaAvis ? metaAvis.scrollWidth > metaAvis.clientWidth && cs(metaAvis).textOverflow === 'ellipsis' : null,
      barreVisibleSansDefiler: barre ? Math.round(r(barre).top) < window.innerHeight : null,
      etiquettesDeStatut: racine.querySelectorAll('[data-etiquette]').length,
      statut: statut?.textContent ?? null,
      tailleQuestion: question ? cs(question).fontSize : null,
      metaSynthese: synthese?.querySelector('p')?.textContent ?? null,
      iconePhase: (() => {
        const zone = barre?.parentElement;
        if (!zone) return null;
        if (zone.querySelector('.animate-pulse')) return 'globe';
        if (zone.querySelector('.animate-spin')) return 'roue';
        return null;
      })(),
      compteurSousLaBarre: /conseillers terminés/.test(racine.textContent || ''),
      reessayer: [...document.querySelectorAll('button')].filter((b) => b.textContent.trim() === 'Réessayer').length,
      nouvelleQuestion: [...document.querySelectorAll('button')].some((b) => b.textContent.trim() === 'Nouvelle question'),
      divergences: [...document.querySelectorAll('h3')].some((h) => /Où les avis divergent/.test(h.textContent)),
      largeursSquelettes: squelettes,
      margeQuestion: question ? cs(question.closest('section')).padding : null,
      margeAvis: cartesAvis[0] ? cs(cartesAvis[0]).padding : null,
      margeSynthese: synthese ? cs(synthese.querySelector('[class*="pb-4"]')).padding : null,
    };
  });
}

async function capturer(page, nom) {
  await page.screenshot({ path: join(SORTIE, `${nom}.png`), fullPage: true });
}

async function cas(navigateur, nom, preparer, { largeur = 1280, theme = 'light', hc = false, fontPx = 16 } = {}) {
  const contexte = await navigateur.newContext({ viewport: { width: largeur, height: 900 }, locale: 'fr-FR' });
  const page = await contexte.newPage();
  const journal = [];
  page.on('console', (m) => { if (m.type() === 'error') journal.push(m.text().slice(0, 120)); });
  try {
    await preparer(page);
    await poserApparence(page, { theme, hc, fontPx });
    await page.waitForTimeout(400);
    const cle = `${nom}-${largeur}-${hc ? 'hc' : theme}-${fontPx}px`;
    await capturer(page, cle);
    return { nom: cle, ...(await mesurer(page)), erreursConsole: journal };
  } finally {
    await contexte.close();
  }
}

/** Ouvre le détail d'une décision enregistrée depuis la liste. */
async function ouvrirLeDetail(page) {
  await intercepter(page);
  await ouvrirDecision(page);
  await page.getByTestId('board-history-card').waitFor({ timeout: 15000 });
  await page.getByRole('button', { name: QUESTION }).click();
  await page.getByTestId('board-decision-detail').waitFor({ timeout: 15000 });
}

/** Lance une délibération depuis le formulaire, avec le flux demandé. */
async function lancerUneDeliberation(page, flux) {
  await poserLeFluxSSE(page, flux);
  await intercepter(page);
  await ouvrirDecision(page);
  await page.getByTestId('board-history-card').waitFor({ timeout: 15000 });
  await page.getByRole('button', { name: 'Nouvelle question' }).first().click();
  await page.getByTestId('board-new-form').waitFor({ timeout: 15000 });
  await page.getByLabel('Question stratégique').fill(QUESTION_RUN);
  await page.getByRole('button', { name: 'Préparer la délibération' }).click();
  await page.getByTestId('board-confirmation').waitFor({ timeout: 10000 });
  await page.getByRole('button', { name: 'Confirmer et lancer' }).click();
  await page.getByTestId('board-run-view').waitFor({ timeout: 15000 });
  await page.waitForTimeout(600);
}

async function main() {
  mkdirSync(SORTIE, { recursive: true });
  const navigateur = await chromium.launch({ headless: true });
  const rapport = [];
  try {
    // 1. Le détail enregistré, aux quatre largeurs et aux trois apparences.
    for (const apparence of [{ theme: 'light' }, { theme: 'dark' }, { hc: true }]) {
      rapport.push(await cas(navigateur, 'normal', ouvrirLeDetail, { largeur: 1280, ...apparence }));
    }
    for (const largeur of [1024, 840, 800]) {
      rapport.push(await cas(navigateur, 'normal', ouvrirLeDetail, { largeur }));
    }
    for (const fontPx of [14, 18]) {
      rapport.push(await cas(navigateur, 'normal', ouvrirLeDetail, { fontPx }));
    }

    // 2. La délibération en cours : deux avis rendus, flux JAMAIS fermé.
    const encours = (page) => lancerUneDeliberation(page, { evenements: evenementsDuFlux({ rendus: 2 }), ferme: false });
    rapport.push(await cas(navigateur, 'encours', encours, { largeur: 1280 }));
    rapport.push(await cas(navigateur, 'encours', encours, { largeur: 800 }));

    // 2bis. La phase de recherche web : le flux s'arrête après
    //       `web_search_start`, c'est le seul état où l'icône de phase est un
    //       Globe pulsé et non la roue.
    rapport.push(await cas(navigateur, 'encours-recherche-web',
      (page) => lancerUneDeliberation(page, {
        evenements: [{ type: 'task', content: 'tache-1' }, { type: 'web_search_start' }],
        ferme: false,
      }),
      { largeur: 1280 }));

    // 3. Partiel : quatre avis rendus, le flux se ferme sans `done`.
    const partiel = (page) => lancerUneDeliberation(page, { evenements: evenementsDuFlux({ rendus: 4 }), ferme: true });
    rapport.push(await cas(navigateur, 'partiel', partiel, { largeur: 1280 }));
    rapport.push(await cas(navigateur, 'partiel', partiel, { largeur: 800 }));

    // 4. Partiel avec un cinquième avis interrompu AVEC du texte.
    rapport.push(await cas(navigateur, 'partiel-avec-texte',
      (page) => lancerUneDeliberation(page, { evenements: evenementsDuFlux({ rendus: 4, cinquiemeAvecTexte: true }), ferme: true }),
      { largeur: 1280 }));

    // 5. La confirmation d'annulation, sur une délibération en cours.
    rapport.push(await cas(navigateur, 'annulation', async (page) => {
      await encours(page);
      await page.getByRole('button', { name: 'Annuler la délibération' }).click();
      await page.getByTestId('board-cancel-confirmation').waitFor({ timeout: 10000 });
    }, { largeur: 1280 }));

    // 6. Le formulaire et sa confirmation.
    rapport.push(await cas(navigateur, 'formulaire', async (page) => {
      await intercepter(page);
      await ouvrirDecision(page);
      await page.getByRole('button', { name: 'Nouvelle question' }).first().click();
      await page.getByTestId('board-new-form').waitFor({ timeout: 15000 });
      await page.getByLabel('Question stratégique').fill(QUESTION);
      await page.getByRole('button', { name: 'Préparer la délibération' }).click();
      await page.getByTestId('board-confirmation').waitFor({ timeout: 10000 });
    }, { largeur: 1280 }));

    // 7. Un détail ouvert PENDANT un run : l'étiquette doit rester
    //    « Décision enregistrée », jamais « Délibération en cours ».
    rapport.push(await cas(navigateur, 'detail-pendant-run', async (page) => {
      await encours(page);
      await page.getByTestId('board-current-run').waitFor({ timeout: 10000 }).catch(() => {});
      // La rangée du run porte QUESTION_RUN : ce clic vise bien la décision.
      await page.getByRole('button', { name: QUESTION }).click();
      await page.getByTestId('board-decision-detail').waitFor({ timeout: 15000 });
    }, { largeur: 1280 }));

    // 8. Historique vide, en panne, lent.
    rapport.push(await cas(navigateur, 'historique-vide', async (page) => {
      await intercepter(page, { liste: [] });
      await ouvrirDecision(page);
      await page.getByTestId('board-history-empty').waitFor({ timeout: 15000 });
    }, { largeur: 1280 }));
    rapport.push(await cas(navigateur, 'historique-panne', async (page) => {
      await intercepter(page, { status: 500 });
      await ouvrirDecision(page);
      await page.getByTestId('board-history-error').waitFor({ timeout: 15000 });
    }, { largeur: 1280 }));
    rapport.push(await cas(navigateur, 'chargement', async (page) => {
      await intercepter(page, { delaiMs: 8000 });
      await ouvrirDecision(page);
      await page.waitForTimeout(1200);
    }, { largeur: 1280 }));

    // 9. Le clic hors du texte du titre (sur la puce) ouvre bien la décision :
    //    la coupe pose `overflow:hidden` sur le libellé, seule la recette
    //    prouve que le bouton étiré n'en est pas rogné.
    const clicHorsTexte = await (async () => {
      const contexte = await navigateur.newContext({ viewport: { width: 1280, height: 900 }, locale: 'fr-FR' });
      const page = await contexte.newPage();
      try {
        await intercepter(page);
        await ouvrirDecision(page);
        await page.getByTestId('board-history-card').waitFor({ timeout: 15000 });
        const rangee = page.locator('[data-testid="board-history-card"] [class*="grid-cols-[2rem_1fr_auto]"]').first();
        const boite = await rangee.boundingBox();
        // La puce, à gauche du titre : hors du texte, dans la rangée.
        await page.mouse.click(boite.x + 16, boite.y + boite.height / 2);
        const ouvert = await page.getByTestId('board-decision-detail').isVisible({ timeout: 8000 }).catch(() => false);
        await capturer(page, 'clic-sur-la-puce-1280-light-16px');
        return { nom: 'clic-sur-la-puce', ouvreLaDecision: ouvert };
      } finally {
        await contexte.close();
      }
    })();
    rapport.push(clicHorsTexte);

    // 10. L'anneau de focus sur une rangée.
    rapport.push(await cas(navigateur, 'focus-rangee', async (page) => {
      await intercepter(page);
      await ouvrirDecision(page);
      await page.getByTestId('board-history-card').waitFor({ timeout: 15000 });
      await page.getByRole('button', { name: QUESTION }).focus();
    }, { largeur: 1280 }));

    writeFileSync(join(SORTIE, 'mesures.json'), JSON.stringify(rapport, null, 2));
    console.log(JSON.stringify({ sortie: SORTIE, cas: rapport.length }, null, 2));
  } finally {
    await navigateur.close();
  }
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
