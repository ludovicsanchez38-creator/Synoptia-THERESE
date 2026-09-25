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
 * Usage (pile jetable uniquement, jamais le port réel 17293) :
 *   node tests/couverture/couverture-ecran.mjs \
 *     --base http://127.0.0.1:1420 --sortie .app-loop/cycles/13/couverture-ecran
 *
 * Sortie : un JSON par combinaison (largeur × thème), des captures, et
 * `rapport.json` (anomalies dédupliquées, chacune avec un identifiant stable).
 */
import { createHash } from 'node:crypto';
import { mkdirSync, writeFileSync } from 'node:fs';
import { join } from 'node:path';
import { chromium } from '@playwright/test';

const PORT_REEL = 17293;
const ROLES_INTERACTIFS = ['button', 'link', 'menuitem', 'tab', 'checkbox', 'radio', 'switch', 'combobox', 'option'];
const GESTES_A_NE_PAS_CONFIRMER =
  /supprim|effac|purg|anonymis|envoy|réinitialis|reinitialis|déconnect|deconnect|quitter|restaur|vider|confirmer|arrêter|arreter|désinstall|desinstall|révoqu|revoqu|payer|importer|exporter|télécharg|telecharg|générer|generer|lancer|démarrer|demarrer|publier|brancher|connecter|ouvrir le dossier|sélectionner un dossier|selectionner un dossier|choisir un fichier/i;
const ACTIONS_A_OUVRIR = /\.(open|toggle|new)$/;
const ACTIONS_EXCLUES = /^(chat\.new|data\.|backup\.|app\.quit)/;
// P-145 : « chaque élément interactif » : aucun plafond (calibration du 25/09 :
// un plafond de 40 laissait l'élément témoin hors de l'exercice).
const PLAFOND_GESTES_PAR_ECRAN = Number.POSITIVE_INFINITY;

function lireLesArguments(argv) {
  const args = { base: 'http://127.0.0.1:1420', sortie: '.app-loop/couverture-ecran', largeurs: [1440, 800], themes: ['light', 'dark'] };
  for (let i = 2; i < argv.length; i += 2) {
    const [cle, valeur] = [argv[i], argv[i + 1]];
    if (cle === '--base') args.base = valeur;
    else if (cle === '--sortie') args.sortie = valeur;
    else if (cle === '--largeurs') args.largeurs = valeur.split(',').map(Number);
    else if (cle === '--themes') args.themes = valeur.split(',');
    else if (cle === '--ecrans') args.ecrans = valeur.split(',');
  }
  return args;
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

async function lesInteractifs(page) {
  const trouves = [];
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
      })).catch(() => ({ deja: false, natif: false }));
      const nom = await locator.evaluate((el) => {
        const aria = el.getAttribute('aria-label') || '';
        const labelledby = el.getAttribute('aria-labelledby');
        const parLien = labelledby
          ? labelledby.split(/\s+/).map((id) => document.getElementById(id)?.textContent ?? '').join(' ')
          : '';
        const title = el.getAttribute('title') || '';
        const texte = (el.textContent || '').trim();
        const label = el.id ? (document.querySelector(`label[for="${CSS.escape(el.id)}"]`)?.textContent ?? '') : '';
        const valeur = el.getAttribute('placeholder') || '';
        return (aria || parLien || texte || label || title || valeur).replace(/\s+/g, ' ').trim();
      }).catch(() => '');
      trouves.push({ role, index: i, nom, locator, actif, deja: etat.deja, natif: etat.natif });
    }
  }
  return trouves;
}

async function releverLEcran({ page, base, ecran, action, largeur, theme, exercer, dossier, journal, dejaExerces }) {
  const anomalies = [];
  const ajouter = (a) => anomalies.push({ ...a, ecran, largeur, theme, id: idDAnomalie({ ...a, ecran }) });
  journal.console.length = 0;
  journal.reseau.length = 0;

  await ouvrirLEcran(page, base, action);
  if (journal.portReel) throw new Error(`requête vers le port réel ${PORT_REEL} : arrêt (pile jetable seulement)`);
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
    // Le rail et l'en-tête reviennent sur chaque écran : un élément (rôle et
    // nom) ne s'exerce qu'une fois par passage.
    const aExercer = interactifs
      .filter((el) => el.nom && el.role !== 'option' && !dejaExerces.has(`${el.role}|${el.nom}`))
      .slice(0, PLAFOND_GESTES_PAR_ECRAN);
    for (const el of aExercer) dejaExerces.add(`${el.role}|${el.nom}`);
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
      if (GESTES_A_NE_PAS_CONFIRMER.test(el.nom)) {
        gestes.push({ element: `${el.role} « ${el.nom} »`, resultat: 'non exercé (geste à confirmer ou sortant)' });
        continue;
      }
      // Chaque geste part de l'écran tel qu'il s'ouvre : un clic précédent a
      // pu ouvrir un panneau ou changer d'écran (réouverture seulement alors).
      const courante = await empreinte(page);
      if (courante.url !== initiale.url || courante.dom !== initiale.dom || courante.etats !== initiale.etats || courante.dialogues !== initiale.dialogues) {
        await ouvrirLEcran(page, base, action);
      }
      const frais = page.getByRole(el.role, { name: el.nom, exact: true }).first();
      if (!(await frais.isVisible().catch(() => false))) {
        gestes.push({ element: `${el.role} « ${el.nom} »`, resultat: 'introuvable après réouverture' });
        continue;
      }
      // Un clic donne le focus à l'élément : sans ce focus préalable, le
      // « clic mort » ne pouvait jamais sortir (calibration du 25/09).
      await frais.focus().catch(() => undefined);
      const avant = await empreinte(page);
      try {
        await frais.click({ timeout: 3000 });
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

async function principal() {
  const args = lireLesArguments(process.argv);
  mkdirSync(args.sortie, { recursive: true });
  const navigateur = await chromium.launch();
  const combinaisons = [];
  try {
    for (const largeur of args.largeurs) {
      for (const theme of args.themes) {
        const contexte = await navigateur.newContext({ viewport: { width: largeur, height: 900 }, colorScheme: theme });
        // P-142 : l'écran quitté se rouvrirait ; chaque écran part de l'Accueil.
        await contexte.addInitScript(() => { try { sessionStorage.clear(); } catch { /* sans stockage */ } });
        const page = await contexte.newPage();
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
          releves.push(await releverLEcran({ page, base: args.base, ecran, action, largeur, theme, exercer, dossier, journal, dejaExerces }));
          console.log(`${largeur}-${theme} ${ecran} : ${releves.at(-1).anomalies.length} anomalie(s)`);
        }
        writeFileSync(join(args.sortie, `${largeur}-${theme}.json`), `${JSON.stringify({ largeur, theme, ecrans: releves }, null, 2)}\n`);
        combinaisons.push({ largeur, theme, releves });
        await contexte.close();
      }
    }
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
    base: args.base,
    genere_le: new Date().toISOString(),
    combinaisons: combinaisons.map((c) => ({
      largeur: c.largeur, theme: c.theme, ecrans: c.releves.length,
      gestes: c.releves.reduce((n, r) => n + r.gestes.length, 0),
    })),
    ecrans: [...new Set(combinaisons.flatMap((c) => c.releves.map((r) => r.ecran)))],
    anomalies: [...parId.values()],
  };
  writeFileSync(join(args.sortie, 'rapport.json'), `${JSON.stringify(rapport, null, 2)}\n`);
  console.log(`${rapport.ecrans.length} écrans, ${rapport.anomalies.length} anomalies → ${join(args.sortie, 'rapport.json')}`);
}

principal().catch((err) => {
  console.error(err);
  process.exit(1);
});
