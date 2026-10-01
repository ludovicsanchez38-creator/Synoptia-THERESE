#!/usr/bin/env node
/**
 * P-145 : l'instrument « couverture écran » de la boucle Plateau.
 *
 * Sans IA : il ouvre chaque écran que le registre d'actions de la coque sait
 * ouvrir (plus l'Accueil), et relève, à 1440 et 800 px, en thème clair et
 * sombre :
 *   - les erreurs de la console et les réponses réseau en échec (4xx, 5xx) ;
 *   - toute requête qui sort de la machine (hôte autre que 127.0.0.1 ou
 *     localhost) ;
 *   - les éléments interactifs sans nom accessible ;
 *   - le débordement horizontal de la page.
 * À 1440 px en thème clair, il exerce aussi chaque élément interactif
 * (clic réel, jamais `el.click()` : B-1417) et relève le « clic mort »
 * (ni adresse, ni dialogue, ni focus, ni DOM changés) et le focus retombé sur
 * `body`. Un clic mort est un CANDIDAT : le persona de tri tranche.
 *
 * Il ne confirme jamais un geste destructif ou sortant (supprimer, envoyer,
 * purger, importer…) : ces éléments sont listés, pas cliqués.
 *
 * Usage (backend de test lancé via backend_offline:create_app --factory,
 * données jetables uniquement, jamais le port réel 17293) :
 *   node tests/couverture/couverture-ecran.mjs \
 *     --base 'http://127.0.0.1:1420/?port=17393' \
 *     --expected-data-dir /private/tmp/therese-c14/data \
 *     --sortie .app-loop/cycles/14/couverture-ecran
 *
 * Sortie : un JSON par combinaison (largeur × thème), des captures, et
 * `rapport.json` (anomalies dédupliquées, chacune avec un identifiant stable).
 */
import { createHash } from 'node:crypto';
import { mkdirSync, readFileSync, realpathSync, writeFileSync } from 'node:fs';
import { isAbsolute, join, resolve, sep } from 'node:path';
import { fileURLToPath } from 'node:url';
import { chromium } from '@playwright/test';

const PORT_REEL = 17293;
const BASE_JETABLE = 'http://127.0.0.1:1420/?port=17393';
const ORIGINE_FRONT = 'http://127.0.0.1:1420';
const ORIGINE_BACKEND = 'http://127.0.0.1:17393';
const ROUTES_GET_A_NE_PAS_EXERCER = new Set([
  '/api/crm/google-sheets/list',
  '/api/crm/sync/callback',
  '/api/email/auth/callback-redirect',
  '/api/config/llm/models/openrouter',
]);
const ROLES_INTERACTIFS = ['button', 'link', 'menuitem', 'tab', 'checkbox', 'radio', 'switch', 'combobox', 'option'];
const ATTRIBUTS_IDENTITE = ['data-testid', 'data-agent-id', 'data-id', 'id', 'href', 'aria-controls'];
const GESTES_A_NE_PAS_CONFIRMER =
  /supprim|effac|purg|anonymis|envoy|réinitialis|reinitialis|déconnect|deconnect|quitter|restaur|vider|confirmer|arrêter|arreter|désinstall|desinstall|révoqu|revoqu|payer|importer|exporter|télécharg|telecharg|gén[èé]r|gener|lancer|démarrer|demarrer|publier|brancher|connecter|ouvrir le dossier|sélectionner un dossier|selectionner un dossier|choisir un fichier|install|tester|test de|vérifier|verifier|synchronis|rafraîch|rafraich|actualis|rechercher sur le web|ouvrir (?:un )?(?:site|lien externe)|autoriser|authentifier|se connecter|s'inscrire|inscription|préparation rdv|onboarding client|audit trésorerie|veille concurrentielle/i;
// B-1715 : ces cartes ouvrent leur fiche ; le bouton « Lancer » y est distinct.
// Une exception exige l'écran, le rôle, l'identifiant DOM et le nom attendus.
const FICHES_ACTIONS_SANS_LANCEMENT = new Map([
  ['rapport-hebdo', 'Rapport hebdomadaire'],
  ['relance-clients', 'Relance clients'],
  ['prep-rdv', 'Préparation RDV'],
  ['onboarding-client', 'Onboarding client'],
  ['audit-tresorerie', 'Audit trésorerie'],
  ['veille-concurrent', 'Veille concurrentielle'],
]);
const ACTIONS_A_OUVRIR = /\.(open|toggle|new)$/;
const ACTIONS_EXCLUES = /^(chat\.new|data\.|backup\.|app\.quit)/;
// P-145 : « chaque élément interactif » : aucun plafond (calibration du 25/09 :
// un plafond de 40 laissait l'élément témoin hors de l'exercice).
const PLAFOND_GESTES_PAR_ECRAN = Number.POSITIVE_INFINITY;

function lireLesArguments(argv) {
  const args = { base: BASE_JETABLE, sortie: '.app-loop/couverture-ecran', largeurs: [1440, 800], themes: ['light', 'dark'] };
  for (let i = 2; i < argv.length; i += 2) {
    const [cle, valeur] = [argv[i], argv[i + 1]];
    if (cle === '--base') args.base = valeur;
    else if (cle === '--expected-data-dir') args.expectedDataDir = valeur;
    else if (cle === '--sortie') args.sortie = valeur;
    else if (cle === '--largeurs') args.largeurs = valeur.split(',').map(Number);
    else if (cle === '--themes') args.themes = valeur.split(',');
    else if (cle === '--ecrans') args.ecrans = valeur.split(',');
  }
  return args;
}

// B-1714 : l'URL est validée avant toute navigation ou ouverture de navigateur. Le
// paramètre port=17393 empêche le fallback frontend vers l'instance 17293.
export function verifierBaseJetable(base) {
  let url;
  try { url = new URL(base); } catch { throw new Error('Base invalide : pile jetable attendue'); }
  if (url.href !== BASE_JETABLE) {
    throw new Error(`Base refusée : utiliser exactement ${BASE_JETABLE}`);
  }
  return url;
}

// Une paire de ports locale ne suffit pas : une pile lancée sur des données
// utilisateur serait locale aussi. Ce GET contrôlé précède tout navigateur.
export async function verifierPileJetable(base, expectedDataDir, fetcher = fetch) {
  verifierBaseJetable(base);
  if (!expectedDataDir || !isAbsolute(expectedDataDir)) {
    throw new Error('--expected-data-dir absolu requis pour une pile jetable');
  }
  const racineJetable = realpathSync('/private/tmp');
  const attendu = realpathSync(expectedDataDir);
  if (!attendu.startsWith(`${racineJetable}${sep}`)) {
    throw new Error(`Dossier attendu hors de ${racineJetable} : ${attendu}`);
  }
  // La garde du navigateur ne voit pas les requêtes HTTP lancées par le
  // backend. Le wrapper ASGI de test bloque les sockets non locales avant
  // d'importer l'application et atteste ici sa présence, avant tout jeton.
  const attestation = await fetcher(`${ORIGINE_BACKEND}/__couverture/offline`, {
    method: 'GET', redirect: 'error', signal: AbortSignal.timeout(5000),
  });
  if (!attestation.ok) throw new Error(`Attestation du backend hors ligne absente : HTTP ${attestation.status}`);
  const preuveReseau = await attestation.json();
  if (preuveReseau.version !== 1 || preuveReseau.network_policy !== 'loopback-only' || preuveReseau.offline !== true) {
    throw new Error('Attestation du backend hors ligne invalide');
  }
  // Cette route d'amorçage est exempte du middleware d'authentification et
  // accepte un client local sans Origin. Le jeton ne sort pas de cette portée.
  const amorcage = await fetcher(`${ORIGINE_BACKEND}/api/auth/token`, {
    method: 'GET', redirect: 'error', signal: AbortSignal.timeout(5000),
  });
  if (!amorcage.ok) throw new Error(`Amorçage de la pile jetable indisponible : HTTP ${amorcage.status}`);
  const { token } = await amorcage.json();
  if (typeof token !== 'string' || !token) throw new Error('Jeton de la pile jetable absent');
  const reponse = await fetcher(`${ORIGINE_BACKEND}/api/config/stats`, {
    method: 'GET', redirect: 'error', signal: AbortSignal.timeout(5000),
    headers: { 'X-Therese-Token': token },
  });
  if (!reponse.ok) throw new Error(`Preuve de pile jetable indisponible : HTTP ${reponse.status}`);
  const stats = await reponse.json();
  if (typeof stats.data_dir !== 'string' || typeof stats.db_path !== 'string'
      || !isAbsolute(stats.data_dir) || !isAbsolute(stats.db_path)) {
    throw new Error('Preuve de pile jetable incomplète : data_dir ou db_path');
  }
  const dataDir = realpathSync(stats.data_dir);
  const dbPath = realpathSync(stats.db_path);
  if (dataDir !== attendu || !dbPath.startsWith(`${attendu}${sep}`)) {
    throw new Error(`Pile non jetable ou incohérente : data_dir=${dataDir}, db_path=${dbPath}`);
  }
  return { data_dir: dataDir, db_path: dbPath };
}

// Le POST /api/variables/preview est le seul verbe d'écriture admis : le
// service (routers/variables.py -> variables_service.py) ne fait que SELECT,
// substitution en mémoire et calcul d'empreinte, sans commit ni effet externe.
export function requeteAutorisee(methode, adresse) {
  let url;
  try { url = new URL(adresse); } catch { return false; }
  if (url.protocol !== 'http:' || url.hostname !== '127.0.0.1'
      || ![ORIGINE_FRONT, ORIGINE_BACKEND].includes(url.origin)
      || url.username || url.password || url.hash) return false;
  if (ROUTES_GET_A_NE_PAS_EXERCER.has(url.pathname)) return false;
  if (['GET', 'HEAD', 'OPTIONS'].includes(methode)) return true;
  return url.origin === ORIGINE_BACKEND && methode === 'POST'
    && url.pathname === '/api/variables/preview' && !url.search;
}

function adresseSansSecrets(adresse) {
  try {
    const url = new URL(adresse);
    return `${url.origin}${url.pathname}`;
  } catch {
    return '[adresse invalide]';
  }
}

export function gesteExclu(nom, { ecran, role, agentId } = {}) {
  if (role === 'button') {
    if (ecran === 'invoices.open' && nom === 'Envoyée') return false;
    if (ecran === 'tasks.open' && nom === 'Rafraîchir les tâches') return false;
    const nomFiche = ecran === 'actions.open' && FICHES_ACTIONS_SANS_LANCEMENT.get(agentId);
    if (nomFiche && nom === `Ouvrir la fiche ${nomFiche}`) return false;
    if (ecran === 'actions.open' && nom.startsWith('Ouvrir la fiche ')) return true;
  }
  return GESTES_A_NE_PAS_CONFIRMER.test(nom);
}

export function installerGardeReseau(contexte, garde) {
  return Promise.all([
    contexte.route('**/*', (route) => {
      const requete = route.request();
      if (requeteAutorisee(requete.method(), requete.url())) return route.continue();
      garde.bloquees.push({ methode: requete.method(), url: adresseSansSecrets(requete.url()) });
      try {
        if (new URL(requete.url()).port === String(PORT_REEL)) garde.portReel = true;
      } catch { /* URL invalide : déjà bloquée */ }
      return route.abort('blockedbyclient');
    }),
    contexte.routeWebSocket(/.*/, (route) => {
      let autorisee = false;
      try {
        const url = new URL(route.url());
        autorisee = url.protocol === 'ws:' && url.origin === 'ws://127.0.0.1:1420';
      } catch { /* URL invalide : bloquée */ }
      if (autorisee) return route.connectToServer();
      garde.websockets_bloques.push(adresseSansSecrets(route.url()));
      return route.close();
    }),
  ]);
}

function idDAnomalie(anomalie) {
  const cle = [anomalie.type, anomalie.ecran, anomalie.element ?? '', anomalie.detail ?? ''].join('|');
  return createHash('sha256').update(cle).digest('hex').slice(0, 12);
}

async function empreinte(page) {
  return page.evaluate(() => ({
    url: location.href,
    dialogues: document.querySelectorAll('[role="dialog"],[role="alertdialog"]').length,
    focus: (() => {
      const el = document.activeElement;
      if (!el || el === document.body) return 'body';
      return `${el.tagName}#${el.id}|${el.getAttribute('aria-label') ?? ''}|${(el.textContent ?? '').trim().slice(0, 40)}`;
    })(),
    dom: `${document.body.getElementsByTagName('*').length}:${document.body.innerText.length}`,
    // Un filtre ou un onglet change d'état sans changer de texte : les états
    // ARIA entrent dans l'empreinte (calibration du 25/09).
    etats: [...document.querySelectorAll('[aria-pressed],[aria-selected],[aria-checked],[aria-expanded],[aria-current]')]
      .map((el) => ['aria-pressed', 'aria-selected', 'aria-checked', 'aria-expanded', 'aria-current'].map((a) => el.getAttribute(a) ?? '').join(','))
      .join('|'),
  }));
}

async function ouvrirLEcran(page, base, action) {
  await page.goto(base, { waitUntil: 'domcontentloaded' });
  await page.waitForFunction(() => Boolean(window.__therese?.runAction), undefined, { timeout: 15000 });
  if (action) {
    await page.evaluate((id) => window.__therese.runAction(id), action);
  }
  await page.waitForTimeout(1200);
}

// Seuls l'en-tête direct et le rail de la coque sont communs aux écrans.
// Une vue métier peut contenir ses propres header/nav et des noms homonymes.
function zoneGlobalePourNoeud(el) {
  const coque = el.closest('[data-testid="conversation-canvas-prototype"]');
  if (!coque) return null;
  const entete = coque.querySelector(':scope > div > header');
  if (entete?.contains(el)) return 'entete';
  const corps = entete?.nextElementSibling;
  const navigation = corps?.querySelector(':scope > nav[aria-label="Navigation principale"]');
  if (navigation?.contains(el)) return 'navigation';
  return null;
}

export async function lesInteractifs(page) {
  const trouves = [];
  const occurrences = new Map();
  // Une fenêtre modale ouverte : seuls ses éléments sont atteignables ; ceux
  // de la page dessous seraient relevés « non cliquables » à tort.
  const modales = page.locator('[role="dialog"][aria-modal="true"], [role="alertdialog"][aria-modal="true"]');
  const racine = (await modales.count()) > 0 ? modales.last() : page;
  for (const role of ROLES_INTERACTIFS) {
    const liste = racine.getByRole(role);
    const n = await liste.count();
    for (let i = 0; i < n; i += 1) {
      const locator = liste.nth(i);
      if (!(await locator.isVisible().catch(() => false))) continue;
      const boite = await locator.boundingBox().catch(() => null);
      // Lien d'évitement et autres éléments réservés au clavier : 1 px.
      if (!boite || boite.width < 2 || boite.height < 2) continue;
      const actif = await locator.isEnabled().catch(() => true);
      const etat = await locator.evaluate((el) => ({
        deja: ['aria-pressed', 'aria-selected', 'aria-checked'].some((a) => el.getAttribute(a) === 'true')
          || ['page', 'true', 'step'].includes(el.getAttribute('aria-current') ?? ''),
        natif: el.tagName === 'SELECT' || (el.tagName === 'INPUT' && el.getAttribute('type') === 'file'),
        identites: Object.fromEntries(
          ['data-testid', 'data-agent-id', 'data-id', 'id', 'href', 'aria-controls']
            .map((attribut) => [attribut, el.getAttribute(attribut)])
            .filter(([, valeur]) => valeur),
        ),
      })).catch(() => ({ deja: false, natif: false, identites: {} }));
      const nom = await locator.evaluate((el) => {
        const aria = el.getAttribute('aria-label') || '';
        const labelledby = el.getAttribute('aria-labelledby');
        const parLien = labelledby
          ? labelledby.split(/\s+/).map((id) => document.getElementById(id)?.textContent ?? '').join(' ')
          : '';
        const title = el.getAttribute('title') || '';
        const texte = (el.textContent || '').trim();
        const label = el.id ? (document.querySelector(`label[for="${CSS.escape(el.id)}"]`)?.textContent ?? '') : '';
        const labelEnglobant = el.closest('label')?.textContent ?? '';
        const valeur = el.getAttribute('placeholder') || '';
        return (aria || parLien || texte || label || labelEnglobant || title || valeur).replace(/\s+/g, ' ').trim();
      }).catch(() => '');
      // Le texte ci-dessus sert au rapport, mais n'est pas forcément le nom
      // accessible calculé par le navigateur (23 gestes ratés au cycle 14).
      const signature = await locator.ariaSnapshot().then((s) => s.split('\n')[0]).catch(() => '');
      const zoneGlobale = await locator.evaluate(zoneGlobalePourNoeud).catch(() => null);
      const cleSignature = JSON.stringify([role, signature, zoneGlobale]);
      const signatureOccurrence = occurrences.get(cleSignature) ?? 0;
      occurrences.set(cleSignature, signatureOccurrence + 1);
      const agentId = await locator.getAttribute('data-agent-id').catch(() => null);
      trouves.push({ role, index: i, nom, signature, signatureOccurrence, zoneGlobale,
        identites: etat.identites, identiteStable: null, agentId, locator, actif, deja: etat.deja, natif: etat.natif });
    }
  }
  const groupes = new Map();
  for (const el of trouves) {
    const cle = JSON.stringify([el.role, el.signature, el.zoneGlobale]);
    if (!groupes.has(cle)) groupes.set(cle, []);
    groupes.get(cle).push(el);
  }
  for (const groupe of groupes.values()) {
    for (const el of groupe) {
      el.signatureTotal = groupe.length;
      // Même un singleton peut être remplacé par une autre action portant le
      // même nom ; son identité explicite doit survivre à la réouverture.
      for (const attribut of ATTRIBUTS_IDENTITE) {
        const valeur = el.identites[attribut];
        if (valeur && groupe.filter((autre) => autre.identites[attribut] === valeur).length === 1) {
          el.identiteStable = { attribut, valeur };
          break;
        }
      }
    }
  }
  return trouves;
}

export async function relocaliserInteractif(page, element) {
  const modales = page.locator('[role="dialog"][aria-modal="true"], [role="alertdialog"][aria-modal="true"]');
  const racine = (await modales.count()) > 0 ? modales.last() : page;
  if (!element.signature) return null;
  // B-1718 : SetupChecklist peut retirer une étape après son GET asynchrone.
  // Le rang de tous les boutons suivants change alors, même si le geste et
  // son nom accessible sont encore présents. On retrouve la signature dans
  // la même zone, puis une identité unique pour ses éventuels homonymes.
  const liste = racine.getByRole(element.role);
  const n = await liste.count();
  const correspondants = [];
  for (let i = 0; i < n; i += 1) {
    const frais = liste.nth(i);
    if (!(await frais.isVisible().catch(() => false))) continue;
    const boite = await frais.boundingBox().catch(() => null);
    if (!boite || boite.width < 2 || boite.height < 2) continue;
    const signature = await frais.ariaSnapshot().then((s) => s.split('\n')[0]).catch(() => '');
    if (signature !== element.signature) continue;
    const zoneGlobale = await frais.evaluate(zoneGlobalePourNoeud).catch(() => null);
    if (zoneGlobale !== (element.zoneGlobale ?? null)) continue;
    correspondants.push(frais);
  }
  // Un rang ne prouve pas l'identité d'un homonyme : même à effectif constant,
  // deux actions peuvent échanger de place pendant un GET ou une réouverture.
  if (element.signatureTotal !== undefined && correspondants.length !== element.signatureTotal) return null;
  if (correspondants.length === 0) return null;
  if (!element.identiteStable) return correspondants.length === 1 ? correspondants[0] : null;
  const { attribut, valeur } = element.identiteStable;
  if (!ATTRIBUTS_IDENTITE.includes(attribut)) return null;
  const memes = [];
  for (const frais of correspondants) {
    if (await frais.getAttribute(attribut).catch(() => null) !== valeur) continue;
    // Un testid peut décrire la place du bouton tandis que data-id ou href
    // décrit sa cible métier. Toute identité présente au relevé doit tenir.
    let concordant = true;
    for (const [cle, attendu] of Object.entries(element.identites ?? {})) {
      if (!ATTRIBUTS_IDENTITE.includes(cle) || await frais.getAttribute(cle).catch(() => null) !== attendu) {
        concordant = false;
        break;
      }
    }
    if (concordant) memes.push(frais);
  }
  return memes.length === 1 ? memes[0] : null;
}

function cleGesteGlobal(element) {
  if (!element.zoneGlobale) return null;
  return JSON.stringify([element.zoneGlobale, element.role, element.signature || element.nom,
    element.identiteStable ?? element.signatureOccurrence]);
}

export function choisirGestes(interactifs, dejaExerces) {
  // Les gestes métier se répètent par écran, même avec un nom identique à un
  // bouton de coque. Seuls les contrôles fixes de la coque sont dédupliqués.
  return interactifs
    .filter((el) => el.nom && el.role !== 'option'
      && (el.zoneGlobale === null || !dejaExerces.has(cleGesteGlobal(el))))
    .slice(0, PLAFOND_GESTES_PAR_ECRAN);
}

export function memoriserGesteExerce(dejaExerces, element) {
  const cle = cleGesteGlobal(element);
  if (cle) dejaExerces.add(cle);
}

export function detailRejetRelocalisation(element) {
  if (element.signatureTotal > 1 && !element.identiteStable) {
    return 'homonymes sans identité stable : clic refusé';
  }
  return 'absent, effectif ou identité changés après réouverture';
}

// B-1717 : les filtres de Factures sont persistés par invoiceStore. Une
// réouverture après un clic sur « Annulée » ne retrouve plus le CTA de l'état
// vide initial. Ne restaurer que cette clé, sur la même origine jetable ; le
// thème, l'onboarding et les autres espaces locaux restent intacts.
export async function capturerEtatLocalEcran(page, ecran) {
  if (ecran !== 'invoices.open') return null;
  if (new URL(page.url()).origin !== ORIGINE_FRONT) throw new Error('Capture locale hors du frontend jetable');
  return {
    cle: 'therese-invoice-storage',
    valeur: await page.evaluate(() => localStorage.getItem('therese-invoice-storage')),
  };
}

export async function restaurerEtatLocalEcran(page, etat) {
  if (etat === null) return;
  if (etat?.cle !== 'therese-invoice-storage' || new URL(page.url()).origin !== ORIGINE_FRONT) {
    throw new Error('Restauration locale refusée hors des filtres Factures jetables');
  }
  await page.evaluate(({ valeur }) => {
    if (valeur === null) localStorage.removeItem('therese-invoice-storage');
    else localStorage.setItem('therese-invoice-storage', valeur);
  }, etat);
}

async function releverLEcran({ page, base, ecran, action, largeur, theme, exercer, dossier, journal, dejaExerces }) {
  const anomalies = [];
  const ajouter = (a) => anomalies.push({ ...a, ecran, largeur, theme, id: idDAnomalie({ ...a, ecran }) });
  journal.console.length = 0;
  journal.reseau.length = 0;

  await ouvrirLEcran(page, base, action);
  if (journal.portReel) throw new Error(`requête vers le port réel ${PORT_REEL} : arrêt (pile jetable seulement)`);
  const etatLocalInitial = await capturerEtatLocalEcran(page, ecran);
  const capture = join(dossier, `${ecran.replace(/[^a-z0-9.-]/gi, '_')}-${largeur}-${theme}.png`);
  await page.screenshot({ path: capture, fullPage: false }).catch(() => undefined);

  const debordement = await page.evaluate(() => {
    const page = document.documentElement.scrollWidth - document.documentElement.clientWidth;
    // La coque rogne au lieu de faire défiler la page : un contenu trop large
    // disparaît dans un conteneur `overflow: hidden`. Une troncature voulue
    // (points de suspension) n'en est pas une.
    const rognes = [];
    for (const el of document.querySelectorAll('body *')) {
      const style = getComputedStyle(el);
      if (style.overflowX === 'visible') continue;
      if (style.textOverflow === 'ellipsis') continue;
      const exces = el.scrollWidth - el.clientWidth;
      // clientWidth ≤ 1 : lien d'évitement et textes réservés aux lecteurs d'écran.
      if (exces <= 2 || el.clientWidth <= 1) continue;
      const boite = el.getBoundingClientRect();
      if (boite.width === 0 || boite.height === 0) continue;
      const mode = ['auto', 'scroll'].includes(style.overflowX) ? 'défile en largeur' : 'rogné';
      rognes.push(`${el.tagName.toLowerCase()}${el.id ? `#${el.id}` : ''}.${[...el.classList].slice(0, 3).join('.')} (${mode}, ${exces} px)`);
      if (rognes.length >= 10) break;
    }
    return { page, rognes };
  });
  if (debordement.page > 1) {
    ajouter({ type: 'debordement-horizontal', detail: `${debordement.page} px au-delà de la largeur`, capture });
  }
  for (const rogne of debordement.rognes) {
    ajouter({ type: 'contenu-rogne', element: rogne.split(' (')[0], detail: rogne, capture });
  }

  const interactifs = await lesInteractifs(page);
  for (const el of interactifs) {
    if (!el.nom) ajouter({ type: 'nom-accessible-vide', element: `${el.role}#${el.index}`, capture });
  }

  const gestes = [];
  if (exercer) {
    const aExercer = choisirGestes(interactifs, dejaExerces);
    const initiale = await empreinte(page);
    for (const el of aExercer) {
      if (!el.actif) {
        gestes.push({ element: `${el.role} « ${el.nom} »`, resultat: 'inactif (non exercé)' });
        continue;
      }
      if (el.deja) {
        gestes.push({ element: `${el.role} « ${el.nom} »`, resultat: 'déjà sélectionné (non exercé)' });
        continue;
      }
      if (el.natif) {
        gestes.push({ element: `${el.role} « ${el.nom} »`, resultat: 'contrôle natif du système (non exercé)' });
        continue;
      }
      if (gesteExclu(el.nom, { ecran, role: el.role, agentId: el.agentId })) {
        gestes.push({ element: `${el.role} « ${el.nom} »`, resultat: 'non exercé (geste à confirmer ou sortant)' });
        continue;
      }
      // Chaque geste part de l'écran tel qu'il s'ouvre : un clic précédent a
      // pu ouvrir un panneau ou changer d'écran (réouverture seulement alors).
      const courante = await empreinte(page);
      if (courante.url !== initiale.url || courante.dom !== initiale.dom || courante.etats !== initiale.etats || courante.dialogues !== initiale.dialogues) {
        await restaurerEtatLocalEcran(page, etatLocalInitial);
        await ouvrirLEcran(page, base, action);
      }
      const frais = await relocaliserInteractif(page, el);
      if (!frais) {
        ajouter({ type: 'geste-introuvable', element: `${el.role} « ${el.nom} »`, detail: detailRejetRelocalisation(el) });
        gestes.push({ element: `${el.role} « ${el.nom} »`, resultat: 'introuvable après réouverture' });
        continue;
      }
      // Un clic donne le focus à l'élément : sans ce focus préalable, le
      // « clic mort » ne pouvait jamais sortir (calibration du 25/09).
      await frais.focus().catch(() => undefined);
      const avant = await empreinte(page);
      try {
        await frais.click({ timeout: 3000 });
        memoriserGesteExerce(dejaExerces, el);
      } catch (err) {
        ajouter({ type: 'clic-impossible', element: `${el.role} « ${el.nom} »`, detail: String(err.message ?? err).split('\n')[0] });
        gestes.push({ element: `${el.role} « ${el.nom} »`, resultat: 'clic impossible' });
        continue;
      }
      await page.waitForTimeout(500);
      const apres = await empreinte(page);
      const change = ['url', 'dialogues', 'focus', 'dom', 'etats'].filter((k) => avant[k] !== apres[k]);
      if (change.length === 0) {
        ajouter({ type: 'clic-mort-candidat', element: `${el.role} « ${el.nom} »`, detail: 'ni adresse, ni dialogue, ni focus, ni contenu changés' });
      }
      // Le focus doit revenir à qui a ouvert : on ne le vérifie que pour une
      // fenêtre ouverte PAR ce clic (une fenêtre ouverte par le registre
      // n'a pas de déclencheur à qui le rendre).
      if (apres.dialogues > avant.dialogues) {
        await page.keyboard.press('Escape');
        await page.waitForTimeout(300);
        const fin = await empreinte(page);
        if (fin.focus === 'body' && fin.dialogues === 0) {
          ajouter({ type: 'focus-perdu', element: `${el.role} « ${el.nom} »`, detail: 'après Échap, le focus retombe sur la page' });
        }
      }
      gestes.push({ element: `${el.role} « ${el.nom} »`, resultat: change.length ? `change : ${change.join(', ')}` : 'rien ne change' });
    }
  }

  for (const message of journal.console) ajouter({ type: 'console-erreur', detail: message.slice(0, 300) });
  for (const requete of journal.reseau) ajouter({ type: requete.type, detail: requete.detail });

  return { ecran, action, largeur, theme, capture, interactifs: interactifs.length, gestes, anomalies };
}

export function enregistrerInterruption(dossier, erreur, garde, ecran, preuvePile = null, combinaisons = []) {
  mkdirSync(dossier, { recursive: true });
  const rapport = {
    version: 1,
    source_sha256: createHash('sha256').update(readFileSync(fileURLToPath(import.meta.url))).digest('hex'),
    genere_le: new Date().toISOString(),
    ecran,
    cause: String(erreur?.message ?? erreur),
    preuve_pile: preuvePile,
    combinaisons_terminees: combinaisons.map((c) => `${c.largeur}-${c.theme}`),
    garde,
  };
  writeFileSync(join(dossier, 'interruption.json'), `${JSON.stringify(rapport, null, 2)}\n`);
}

async function principal() {
  const args = lireLesArguments(process.argv);
  const preuvePile = await verifierPileJetable(args.base, args.expectedDataDir);
  mkdirSync(args.sortie, { recursive: true });
  const navigateur = await chromium.launch();
  const combinaisons = [];
  const garde = { bloquees: [], websockets_bloques: [], telechargements: [], popups: [], portReel: false };
  let ecranEnCours = null;
  try {
    for (const largeur of args.largeurs) {
      for (const theme of args.themes) {
        const contexte = await navigateur.newContext({ viewport: { width: largeur, height: 900 }, colorScheme: theme, serviceWorkers: 'block', acceptDownloads: false });
        await installerGardeReseau(contexte, garde);
        // P-142 : l'écran quitté se rouvrirait ; chaque écran part de l'Accueil.
        await contexte.addInitScript(() => { try { sessionStorage.clear(); } catch { /* sans stockage */ } });
        // B-1648 : l'application ne lit pas prefers-color-scheme, elle lit son
        // thème dans le store d'accessibilité persisté ; colorScheme seul
        // laissait les combinaisons « dark » en clair.
        await contexte.addInitScript((themeVoulu) => {
          try {
            const cle = 'therese-accessibility';
            const actuel = JSON.parse(localStorage.getItem(cle) ?? 'null') ?? { state: {}, version: 0 };
            localStorage.setItem(cle, JSON.stringify({ ...actuel, state: { ...actuel.state, theme: themeVoulu } }));
          } catch { /* sans stockage : l'auto-contrôle du thème le dira */ }
        }, theme);
        const page = await contexte.newPage();
        page.on('download', (download) => { garde.telechargements.push(adresseSansSecrets(download.url())); void download.cancel(); });
        page.on('popup', (popup) => { garde.popups.push(adresseSansSecrets(popup.url())); void popup.close(); });
        const journal = { console: [], reseau: [] };
        page.on('console', (m) => { if (m.type() === 'error') journal.console.push(m.text()); });
        page.on('request', (r) => {
          const url = new URL(r.url());
          if (url.port === String(PORT_REEL)) journal.portReel = true;
          if (!['127.0.0.1', 'localhost'].includes(url.hostname) && !url.protocol.startsWith('data') && !url.protocol.startsWith('blob')) {
            journal.reseau.push({ type: 'requete-sortante', detail: `${r.method()} ${url.origin}${url.pathname}` });
          }
        });
        page.on('response', (r) => {
          if (r.status() >= 400) journal.reseau.push({ type: 'reseau-echec', detail: `${r.status()} ${r.request().method()} ${new URL(r.url()).pathname}` });
        });

        await ouvrirLEcran(page, args.base, null);
        // B-1648 : l'instrument se vérifie lui-même. Une combinaison « dark »
        // relevée en clair attribuerait sa mesure à un thème jamais affiché.
        const themeAffiche = await page.evaluate(() => document.documentElement.getAttribute('data-theme'));
        if (themeAffiche !== theme) {
          throw new Error(`Instrument non calibré : thème « ${theme} » demandé, « ${themeAffiche} » affiché`);
        }
        const actions = await page.evaluate(() => window.__therese.getActions().map((a) => a.id));
        const ecrans = [{ ecran: 'accueil', action: null }, ...actions
          .filter((id) => ACTIONS_A_OUVRIR.test(id) && !ACTIONS_EXCLUES.test(id))
          .map((id) => ({ ecran: id, action: id }))]
          // Calibration et reprise ciblée : --ecrans accueil,memory.open
          .filter((e) => !args.ecrans || args.ecrans.includes(e.ecran));

        const dossier = join(args.sortie, `${largeur}-${theme}`);
        mkdirSync(dossier, { recursive: true });
        const exercer = largeur === Math.max(...args.largeurs) && theme === args.themes[0];
        const releves = [];
        const dejaExerces = new Set();
        for (const { ecran, action } of ecrans) {
          ecranEnCours = ecran;
          releves.push(await releverLEcran({ page, base: args.base, ecran, action, largeur, theme, exercer, dossier, journal, dejaExerces }));
          if (garde.bloquees.length || garde.websockets_bloques.length || garde.telechargements.length || garde.popups.length) {
            throw new Error(`Couverture interrompue sur ${ecran} : requête, WebSocket, téléchargement ou fenêtre sortante bloqués`);
          }
          console.log(`${largeur}-${theme} ${ecran} : ${releves.at(-1).anomalies.length} anomalie(s)`);
        }
        writeFileSync(join(args.sortie, `${largeur}-${theme}.json`), `${JSON.stringify({ largeur, theme, ecrans: releves }, null, 2)}\n`);
        combinaisons.push({ largeur, theme, releves });
        await contexte.close();
      }
    }
  } catch (erreur) {
    enregistrerInterruption(args.sortie, erreur, garde, ecranEnCours, preuvePile, combinaisons);
    throw erreur;
  } finally {
    await navigateur.close();
  }

  const parId = new Map();
  for (const c of combinaisons) for (const r of c.releves) for (const a of r.anomalies) {
    const deja = parId.get(a.id);
    if (deja) deja.combinaisons.push(`${a.largeur}-${a.theme}`);
    else parId.set(a.id, { ...a, combinaisons: [`${a.largeur}-${a.theme}`] });
  }
  const rapport = {
    version: 1,
    source_sha256: createHash('sha256').update(readFileSync(fileURLToPath(import.meta.url))).digest('hex'),
    base: args.base,
    preuve_pile: preuvePile,
    genere_le: new Date().toISOString(),
    combinaisons: combinaisons.map((c) => ({
      largeur: c.largeur, theme: c.theme, ecrans: c.releves.length,
      gestes: c.releves.reduce((n, r) => n + r.gestes.length, 0),
    })),
    ecrans: [...new Set(combinaisons.flatMap((c) => c.releves.map((r) => r.ecran)))],
    anomalies: [...parId.values()],
    garde,
  };
  writeFileSync(join(args.sortie, 'rapport.json'), `${JSON.stringify(rapport, null, 2)}\n`);
  console.log(`${rapport.ecrans.length} écrans, ${rapport.anomalies.length} anomalies → ${join(args.sortie, 'rapport.json')}`);
}

if (process.argv[1] && fileURLToPath(import.meta.url) === resolve(process.argv[1])) {
  principal().catch((err) => {
    console.error(err);
    process.exit(1);
  });
}
