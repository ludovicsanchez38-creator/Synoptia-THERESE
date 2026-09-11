/**
 * Recette visuelle DA lot 9 : l'écran Paramètres.
 *
 * Ne pas lancer ici : l'orchestrateur la joue sur pile jetable (uvicorn 17393,
 * Vite 1420, jamais 17293). Captures et mesures dans
 * `.cartography-work/validation/da-lot9/`.
 *
 *   FRONTEND_URL=http://localhost:1420 node src/frontend/scripts-recette/recette-da-lot9.mjs
 *
 * Ce que la recette doit montrer, et que jsdom ne peut pas voir (§ 9 du design) :
 * la nav en trois colonnes AU-DESSUS du panneau sous 1024 px (le panneau ne
 * tombe pas à zéro), la grille des fournisseurs à deux colonnes à TOUTES les
 * largeurs, le halo de sélection à 30 % distinct de l'anneau de focus plein de
 * 3 px, une seule carte de service, la pilule de statut du profil qui revient à
 * la ligne au lieu de déborder, et un Réessayer par action.
 */
import { chromium } from 'playwright';
import { mkdirSync, writeFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const FRONTEND = process.env.FRONTEND_URL || 'http://localhost:1420';
const ICI = dirname(fileURLToPath(import.meta.url));
const SORTIE = process.env.RECETTE_SORTIE
  || join(ICI, '../../../.cartography-work/validation/da-lot9');

const MODELES_OLLAMA = [
  { name: 'gemma4-tia', size: 5_368_709_120, modified_at: null, digest: null, gere_les_outils: true },
  { name: 'qwen:8b', size: 5_368_709_120, modified_at: null, digest: null },
];

const PROFIL = {
  display_name: 'Marie Exemple',
  name: 'Marie Exemple',
  nickname: 'Marie',
  company: 'Exemple SARL',
  role: 'Entrepreneur IA',
  email: 'marie@exemple.fr',
  location: 'Manosque, France',
  address: '12 rue de l’Exemple, 04100 Manosque',
  siren: '123 456 789',
  tva_intra: 'FR 00 123 456 789',
  siret: '123 456 789 00010',
  code_ape: '6202A',
  nda: '00 00 00000 00',
  context: 'Je propose des formations IA pour TPE.',
};

/** Un nom volontairement long : la pilule doit revenir à la ligne, pas déborder. */
const PROFIL_NOM_LONG = { ...PROFIL, display_name: 'Marie-Charlotte de la Tour-Maubourg' };

/**
 * Prédicats sur le chemin, jamais de glob : `**` + `/api/config**` attraperait
 * les modules Vite `/src/services/api/config.ts` et la coque ne démarrerait pas
 * (défaut vu aux lots 5 et 6).
 */
async function intercepter(page, {
  cles = { keys: {}, corrupted: [], sources: {} },
  llm = { provider: 'anthropic', model: 'claude-sonnet-4-6', available_models: [], effort: 'auto' },
  profil = null,
  ollama = null,
  clesEnEchec = false,
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
    // `/api/config/` exactement : c'est la route de `getApiKeysWithCorrupted`
    // (config.ts:96). L'égalité stricte évite d'attraper `/api/config/llm`,
    // `/api/config/profile` et `/api/config/ollama/status`, routés à part.
    page.route((u) => u.pathname === '/api/config/', async (route) => {
      if (delaiMs) await new Promise((r) => setTimeout(r, delaiMs));
      if (clesEnEchec) {
        await route.fulfill({ status: 500, json: { detail: 'Lecture refusée' } });
        return;
      }
      await route.fulfill({ json: cles });
    }),
    page.route((u) => u.pathname === '/api/config/llm', async (route) => {
      if (route.request().method() !== 'GET') {
        await route.fulfill({ json: llm });
        return;
      }
      if (delaiMs) await new Promise((r) => setTimeout(r, delaiMs));
      await route.fulfill({ json: llm });
    }),
    page.route((u) => u.pathname === '/api/config/profile', async (route) => {
      if (route.request().method() !== 'GET') {
        await route.continue();
        return;
      }
      if (profil) await route.fulfill({ json: profil });
      else await route.fulfill({ status: 404, json: { detail: 'Aucun profil' } });
    }),
    page.route((u) => u.pathname === '/api/config/ollama/status', async (route) => {
      await route.fulfill({ json: ollama ?? { available: false, base_url: null, models: [], error: 'Ollama ne répond pas' } });
    }),
  ]);
}

async function ouvrirParametres(page, onglet = 'profile') {
  await page.goto(`${FRONTEND}/?prototype=conversation-canvas&scenario=today`, { waitUntil: 'domcontentloaded' });
  await page.waitForFunction(() => Boolean(window.__therese?.runAction), null, { timeout: 20000 });
  await page.evaluate(() => window.__therese.runAction('settings.open'));
  await page.waitForSelector('[data-testid="settings-modal"]', { timeout: 15000 });
  if (onglet !== 'profile') {
    await page.click(`[data-testid="settings-tab-${onglet}"]`);
    await page.waitForFunction(
      (o) => document.querySelector('[data-testid="settings-modal"]')?.getAttribute('data-active-tab') === o,
      onglet,
      { timeout: 10000 },
    );
    // `transition-colors` : le fond de l'onglet met ~150 ms à suivre la classe ; sans cette
    // attente la capture montre l'ancien onglet encore teinté (constaté le 11/09).
    await page.waitForTimeout(300);
  }
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
    const modale = document.querySelector('[data-testid="settings-modal"]');
    if (!modale) return { absente: true };

    const textesSous12 = [];
    const interactifsSous14 = [];
    const hauteursBoutons = [];
    const visiter = (el) => {
      if (el.nodeType !== 1) return;
      const style = getComputedStyle(el);
      const px = parseFloat(style.fontSize);
      const porteDuTexte = [...el.childNodes].some((c) => c.nodeType === 3 && c.textContent.trim());
      if (porteDuTexte && px < 12 - 0.05) {
        textesSous12.push({ texte: el.textContent.trim().slice(0, 40), px: Math.round(px * 10) / 10 });
      }
      if (el.matches('button, input, select, textarea, a[href], [role="switch"]')) {
        if (px < 14 - 0.05) {
          interactifsSous14.push({
            texte: (el.textContent || el.getAttribute('aria-label') || '').trim().slice(0, 40),
            px: Math.round(px * 10) / 10,
          });
        }
        if (el.tagName === 'BUTTON') {
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
    visiter(modale);

    const nav = modale.querySelector('nav[role="tablist"]');
    const panneau = modale.querySelector('[role="tabpanel"]');
    const grille = modale.querySelector('[role="group"][aria-label*="service"]');
    const rectNav = nav?.getBoundingClientRect() ?? null;
    const rectPanneau = panneau?.getBoundingClientRect() ?? null;

    // Les pilules de statut du profil : entières dans leur carte, ou rognées ?
    const pilules = [...modale.querySelectorAll('[data-etiquette]')].map((p) => {
      const r = p.getBoundingClientRect();
      const parent = p.parentElement?.getBoundingClientRect();
      return {
        texte: (p.textContent || '').trim().slice(0, 60),
        largeur: Math.round(r.width),
        deborde: parent ? Math.round(r.right - parent.right) > 1 : null,
        retourALaLigne: getComputedStyle(p).whiteSpace,
      };
    });

    const carteCourante = modale.querySelector('[aria-pressed="true"]');
    const styleCourante = carteCourante ? getComputedStyle(carteCourante) : null;

    return {
      textesSous12,
      interactifsSous14,
      hauteursBoutons,
      largeurModale: Math.round(modale.getBoundingClientRect().width),
      // Sous 1024 px, la nav est AU-DESSUS du panneau (son bas est au-dessus du
      // haut du panneau) et le panneau garde une largeur utile.
      navAuDessusDuPanneau: rectNav && rectPanneau ? rectNav.bottom <= rectPanneau.top + 1 : null,
      largeurNav: rectNav ? Math.round(rectNav.width) : null,
      largeurPanneau: rectPanneau ? Math.round(rectPanneau.width) : null,
      colonnesDeLaNav: nav ? getComputedStyle(nav).gridTemplateColumns.trim().split(/\s+/).length : null,
      defilementHorizontalDeLaNav: nav ? nav.scrollWidth > nav.clientWidth + 1 : null,
      colonnesDesFournisseurs: grille
        ? getComputedStyle(grille).gridTemplateColumns.trim().split(/\s+/).length
        : null,
      cartesFournisseurs: grille ? grille.querySelectorAll('button[aria-pressed]').length : 0,
      cartesSansTabindex: grille
        ? [...grille.querySelectorAll('button')].every((b) => !b.hasAttribute('tabindex'))
        : null,
      // Le halo de sélection est une ombre portée à 30 %, pas un contour.
      haloDeSelection: styleCourante ? styleCourante.boxShadow : null,
      contourDeSelection: styleCourante ? styleCourante.outlineWidth : null,
      titresDeNiveau3: [...modale.querySelectorAll('h3')].map((h) => h.textContent.trim()),
      titreH1: modale.querySelector('h1')?.textContent?.trim() ?? null,
      pilules,
      reessayer: [...modale.querySelectorAll('button')]
        .map((b) => b.textContent.trim())
        .filter((t) => /^Réessayer/.test(t)),
      alertes: modale.querySelectorAll('[role="alert"]').length,
      statuts: modale.querySelectorAll('[role="status"]').length,
      champDeCle: Boolean(modale.querySelector('#settings-api-key')),
      invalide: modale.querySelector('#settings-api-key')?.getAttribute('aria-invalid') ?? null,
      selectDuModele: modale.querySelector('#settings-llm-model')?.value ?? null,
      optionsDuModele: [...(modale.querySelector('#settings-llm-model')?.options ?? [])]
        .map((o) => ({ value: o.value, label: o.textContent.trim(), inerte: o.disabled })),
      grilleIdentiteEnDeuxColonnes: (() => {
        const g = modale.querySelector('[class*="grid-cols-1"][class*="grid-cols-2"]');
        return g ? getComputedStyle(g).gridTemplateColumns.trim().split(/\s+/).length : null;
      })(),
      contexteHorsGrille: (() => {
        const champ = modale.querySelector('#settings-profile-context');
        const g = modale.querySelector('[class*="grid-cols-1"][class*="grid-cols-2"]');
        return champ && g ? !g.contains(champ) : null;
      })(),
      defilementHorizontalDeLaPage: document.documentElement.scrollWidth > window.innerWidth + 1,
    };
  });
}

async function capturer(page, nom) {
  const chemin = join(SORTIE, `${nom}.png`);
  await page.screenshot({ path: chemin, fullPage: true });
  return chemin;
}

async function cas(page, nom, { largeur, theme = 'light', hc = false, fontPx = 16, onglet = 'ai', interception = {} }) {
  await page.setViewportSize({ width: largeur, height: 900 });
  await intercepter(page, interception);
  await ouvrirParametres(page, onglet);
  await poserApparence(page, { theme, hc, fontPx });
  const complet = `${nom}-${largeur}-${theme}${hc ? '-hc' : ''}-${fontPx}px`;
  await capturer(page, complet);
  return { nom: complet, ...(await mesurer(page)) };
}

async function main() {
  mkdirSync(SORTIE, { recursive: true });
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({ locale: 'fr-FR' });
  const page = await context.newPage();
  const rapport = [];

  const OLLAMA_ACTIF = {
    llm: { provider: 'ollama', model: 'gemma4-tia', available_models: [], effort: 'auto' },
    ollama: { available: true, base_url: 'http://127.0.0.1:11434', models: MODELES_OLLAMA, error: null },
  };
  const OPENAI_AVEC_CLE = {
    cles: { keys: { openai: true }, corrupted: [], sources: {} },
    llm: { provider: 'openai', model: 'gpt-5.6-luna', available_models: [], effort: 'auto' },
  };

  try {
    // --- IA, Ollama actif : les trois apparences puis les quatre largeurs
    for (const apparence of [
      { theme: 'light', hc: false, fontPx: 16 },
      { theme: 'dark', hc: false, fontPx: 16 },
      { theme: 'light', hc: true, fontPx: 16 },
    ]) {
      rapport.push(await cas(page, 'ia-ollama-actif', { largeur: 1280, ...apparence, interception: OLLAMA_ACTIF }));
    }
    for (const largeur of [1024, 1023, 840, 800]) {
      rapport.push(await cas(page, 'ia-ollama-actif', { largeur, interception: OLLAMA_ACTIF }));
    }
    // Trois tailles de police : les pilules et la grille doivent tenir.
    for (const fontPx of [14, 18]) {
      rapport.push(await cas(page, 'ia-ollama-actif', { largeur: 1280, fontPx, interception: OLLAMA_ACTIF }));
    }

    // --- IA, OpenAI muni d'une clé (une seule carte de service, au nom du service)
    rapport.push(await cas(page, 'ia-openai-cle', { largeur: 1280, interception: OPENAI_AVEC_CLE }));
    rapport.push(await cas(page, 'ia-openai-cle', { largeur: 800, interception: OPENAI_AVEC_CLE }));

    // --- IA sans aucune clé
    rapport.push(await cas(page, 'ia-sans-cle', { largeur: 1280 }));

    // --- Ollama courant ET indisponible : la carte est désactivée, les treize
    //     autres restent atteignables au clavier (c'est le défaut que la
    //     doctrine Segments ferme).
    rapport.push(await cas(page, 'ia-ollama-indisponible', {
      largeur: 1280,
      interception: { llm: { provider: 'ollama', model: '', available_models: [], effort: 'auto' } },
    }));

    // --- Clé corrompue : la consigne reste en rouge, sous la tête de carte
    rapport.push(await cas(page, 'ia-cle-corrompue', {
      largeur: 1280,
      interception: {
        cles: { keys: { openai: true }, corrupted: ['openai'], sources: {} },
        llm: { provider: 'openai', model: 'gpt-5.6-luna', available_models: [], effort: 'auto' },
      },
    }));

    // --- Modèle hors catalogue (BUG-084) : le Select affiche le modèle
    //     ENREGISTRÉ, pas le premier de la liste.
    rapport.push(await cas(page, 'ia-modele-hors-catalogue', {
      largeur: 1280,
      interception: {
        cles: { keys: { openai: true }, corrupted: [], sources: {} },
        llm: { provider: 'openai', model: 'gpt-maison-42', available_models: [], effort: 'auto' },
      },
    }));

    // --- Fournisseur inconnu du catalogue : la carte et sa clé restent
    rapport.push(await cas(page, 'ia-fournisseur-inconnu', {
      largeur: 1280,
      interception: { llm: { provider: 'venu-du-serveur', model: '', available_models: [], effort: 'auto' } },
    }));

    // --- Lecture des clés en échec : le bandeau d'attention et son Réessayer
    rapport.push(await cas(page, 'ia-lecture-en-echec', { largeur: 1280, interception: { clesEnEchec: true } }));

    // --- Refus de préfixe : une SEULE alerte, et l'aria-invalid qui va avec
    await page.setViewportSize({ width: 1280, height: 900 });
    await intercepter(page);
    await ouvrirParametres(page, 'ai');
    await page.fill('#settings-api-key', 'sk-mauvais-prefixe');
    await page.getByRole('button', { name: 'Enregistrer' }).click();
    await page.locator('[role="alert"]').first().waitFor();
    await capturer(page, 'ia-refus-de-prefixe-1280-light-16px');
    rapport.push({ nom: 'ia-refus-de-prefixe', ...(await mesurer(page)) });

    // --- Focus : un onglet, puis une carte de fournisseur. L'anneau plein de
    //     3 px et le halo de sélection à 30 % doivent rester distinguables.
    await intercepter(page, OLLAMA_ACTIF);
    await ouvrirParametres(page, 'ai');
    await page.locator('[data-testid="settings-tab-ai"]').focus();
    await capturer(page, 'focus-onglet-1280-light-16px');
    const anneauOnglet = await page.evaluate(() => {
      const s = getComputedStyle(document.activeElement);
      return { outline: s.outlineWidth, style: s.outlineStyle, ombre: s.boxShadow };
    });
    await page.locator('[role="group"][aria-label*="service"] button[aria-pressed="true"]').focus();
    await capturer(page, 'focus-carte-fournisseur-1280-light-16px');
    const anneauCarteCourante = await page.evaluate(() => {
      const s = getComputedStyle(document.activeElement);
      return { outline: s.outlineWidth, style: s.outlineStyle, ombre: s.boxShadow };
    });
    rapport.push({ nom: 'focus', anneauOnglet, anneauCarteCourante });

    // --- Clavier : Tab traverse les quatorze cartes, les flèches ne font rien
    await intercepter(page, OLLAMA_ACTIF);
    await ouvrirParametres(page, 'ai');
    const avantFleche = await page.evaluate(() => {
      const grille = document.querySelector('[role="group"][aria-label*="service"]');
      grille.querySelector('button').focus();
      return document.activeElement.textContent.trim().slice(0, 30);
    });
    await page.keyboard.press('ArrowDown');
    await page.keyboard.press('ArrowRight');
    const apresFleche = await page.evaluate(() => document.activeElement.textContent.trim().slice(0, 30));
    let arretsDeTabulation = 1;
    for (let i = 0; i < 20; i += 1) {
      await page.keyboard.press('Tab');
      const dansLaGrille = await page.evaluate(() => Boolean(
        document.activeElement.closest('[role="group"][aria-label*="service"]'),
      ));
      if (!dansLaGrille) break;
      arretsDeTabulation += 1;
    }
    rapport.push({ nom: 'clavier-grille', avantFleche, apresFleche, arretsDeTabulation });

    // --- Profil : Marie Exemple, puis un nom long (la pilule doit revenir à la
    //     ligne au lieu de déborder), aux trois tailles de police.
    for (const apparence of [
      { theme: 'light', hc: false, fontPx: 16 },
      { theme: 'dark', hc: false, fontPx: 16 },
      { theme: 'light', hc: true, fontPx: 16 },
    ]) {
      rapport.push(await cas(page, 'profil', { largeur: 1280, onglet: 'profile', ...apparence, interception: { profil: PROFIL } }));
    }
    for (const largeur of [1024, 1023, 840, 800]) {
      rapport.push(await cas(page, 'profil', { largeur, onglet: 'profile', interception: { profil: PROFIL } }));
    }
    for (const fontPx of [14, 18]) {
      rapport.push(await cas(page, 'profil-nom-long', {
        largeur: 1023, onglet: 'profile', fontPx, interception: { profil: PROFIL_NOM_LONG },
      }));
      rapport.push(await cas(page, 'profil-nom-long', {
        largeur: 800, onglet: 'profile', fontPx, interception: { profil: PROFIL_NOM_LONG },
      }));
    }
    rapport.push(await cas(page, 'profil-absent', { largeur: 800, onglet: 'profile' }));

    // --- Chargement lent : six squelettes, et le bandeau de lecture partielle
    //     ne se démonte pas sous le doigt (son bouton garde le focus).
    await page.setViewportSize({ width: 1280, height: 900 });
    await intercepter(page, { delaiMs: 4000 });
    await ouvrirParametres(page, 'profile');
    await capturer(page, 'chargement-1280-light-16px');
    rapport.push({
      nom: 'chargement',
      squelettes: await page.locator('[data-testid="settings-modal"] [aria-hidden="true"]').count(),
      statut: await page.locator('[role="status"]').first().textContent().catch(() => null),
      ...(await mesurer(page)),
    });

    // --- Le focus survit à la reprise du chargement (au CLAVIER, pas à la souris)
    await intercepter(page, { clesEnEchec: true });
    await ouvrirParametres(page, 'profile');
    await page.getByRole('button', { name: 'Réessayer le chargement' }).waitFor();
    await page.getByRole('button', { name: 'Réessayer le chargement' }).focus();
    await intercepter(page, {});
    await page.keyboard.press('Enter');
    await page.waitForTimeout(1500);
    await capturer(page, 'reprise-du-chargement-1280-light-16px');
    rapport.push({
      nom: 'reprise-du-chargement',
      focusApresReprise: await page.evaluate(() => document.activeElement?.id || document.activeElement?.tagName),
      bandeauEncoreLa: await page.locator('[data-testid="settings-load-warning"]').count(),
    });

    // --- L'overlay recouvre établi et composeur (BUG-156 : pas de fermeture au
    //     clic sur le fond). Les juger DERRIÈRE l'overlay, pas à côté.
    await intercepter(page, {});
    await ouvrirParametres(page, 'profile');
    const overlay = await page.evaluate(() => {
      const voile = document.querySelector('[data-dialog-backdrop]');
      if (!voile) return null;
      const r = voile.getBoundingClientRect();
      return {
        couvreToutLEcran: Math.round(r.width) >= window.innerWidth && Math.round(r.height) >= window.innerHeight,
        position: getComputedStyle(voile).position,
      };
    });
    await page.mouse.click(20, 20);
    rapport.push({
      nom: 'overlay',
      ...overlay,
      modaleEncoreOuverte: await page.locator('[data-testid="settings-modal"]').count(),
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
