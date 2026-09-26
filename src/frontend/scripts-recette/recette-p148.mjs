/**
 * P-148 : recette navigateur de la fenêtre d'un projet (vue d'ensemble et
 * confirmation de suppression). UI réelle, données synthétiques aux frontières
 * HTTP, aucune écriture autorisée.
 *
 * Revue P-148, constat 11 : trois gardes vitest ne vérifiaient qu'une classe
 * CSS. jsdom ne charge pas les feuilles de Tailwind : une classe n'y prouve
 * rien du rendu. Elles vivent ici, mesurées sur les styles calculés et les
 * boîtes réelles :
 *  1. seul un élément qui mène quelque part a une bordure (VueDEnsemble) ;
 *  2. ramener la confirmation dans la vue ne fait pas défiler la fenêtre
 *     entière (le contenu défilant est le bloc conteneur de ses éléments
 *     positionnés) : l'en-tête reste en place ;
 *  3. les boutons de la confirmation ont leur propre ligne, la phrase garde
 *     la largeur du bloc (dans la fenêtre du projet et dans la vue Projets).
 * En prime, le constat 7 dans un vrai navigateur : Échap ne ferme que la
 * confirmation.
 *
 * Lancement : un moteur jetable (jamais 17293 ni 17393) et un Vite hors de
 * 1420, sur une origine que le moteur accepte en développement :
 *   VITE_THERESE_BACKEND_PORT=<port du moteur> vite --port 5173
 *   RECETTE_URL=http://127.0.0.1:5173 RECETTE_SORTIE=<dossier> node scripts-recette/recette-p148.mjs
 */
import { chromium, expect } from '@playwright/test';
import { mkdir, writeFile } from 'node:fs/promises';
import { fileURLToPath, pathToFileURL } from 'node:url';

const base = process.env.RECETTE_URL ?? 'http://127.0.0.1:1420';
if (new URL(base).port === '1420' && !process.env.RECETTE_URL) {
  console.warn('RECETTE_URL absente : la recette vise le Vite de développement sur 1420.');
}
const sortie = process.env.RECETTE_SORTIE
  ? pathToFileURL(`${process.env.RECETTE_SORTIE.replace(/\/$/, '')}/`)
  : new URL('../../../.app-loop/recettes/p148/', import.meta.url);
await mkdir(sortie, { recursive: true });

const date = '2026-09-22T10:00:00Z';
const contact = { id: 'contact-p148', first_name: 'Victor', last_name: 'Ruiz', company: 'Entreprise Ardent', email: 'victor@example.invalid', phone: null, address: null, notes: null, tags: [], stage: 'contact', scope: 'global', score: 0, created_at: date, updated_at: date };
const projet = { id: 'projet-p148', name: 'Chantier Ardent p148', description: 'Projet pour Victor Ruiz', contact_id: contact.id, status: 'active', budget: 1200, notes: null, tags: [], created_at: date, updated_at: date };
// Une vue d'ensemble assez longue pour que le formulaire (et l'étiquette
// sr-only de « Nouveau livrable ») commence sous le bas de la fenêtre : c'est
// là que le défaut du contenu défilant se voyait.
const suite = (n, fabrique) => Array.from({ length: n }, (_, i) => fabrique(i));
const ensemble = {
  conversations: { total: 5, elements: [
    { id: 'conv-p148', titre: 'Devis Ardent', mise_a_jour: date },
    ...suite(4, (i) => ({ id: `conv-p148-${i}`, titre: `Échange ${i + 1}`, mise_a_jour: date })),
  ] },
  documents: { total: 3, elements: suite(3, (i) => ({ id: `doc-p148-${i}`, titre: `Document ${i + 1}`, statut: 'en_cours', mise_a_jour: date })) },
  taches: { total: 5, ouvertes: 5, en_retard: 0, elements: [
    { id: 'tache-p148', titre: 'Métrer la pièce', statut: 'todo', echeance: null, en_retard: false },
    ...suite(4, (i) => ({ id: `tache-p148-${i}`, titre: `Tâche ${i + 1}`, statut: 'todo', echeance: null, en_retard: false })),
  ] },
  contacts: { total: 1, ranges: 0, elements: [{ id: contact.id, first_name: contact.first_name, last_name: contact.last_name, company: contact.company, associe: true }] },
  livrables: { total: 0 }, fichiers: { total: 0, deposes: 0, indexes_sur_place: 0 }, rendez_vous: { total: 0 },
  dossier_synchronise: { rattache: false }, sous_dossiers: { total: 0 }, planning: { total: 0, ressources: 0, calculs: 0 },
  indisponibles: [],
};

const resultats = [];
const navigateur = await chromium.launch({ headless: true });
try {
  for (const largeur of [1280, 900]) {
    const contexte = await navigateur.newContext({ viewport: { width: largeur, height: 800 }, locale: 'fr-FR', reducedMotion: 'reduce' });
    const page = await contexte.newPage();
    const erreurs = [], mutations = [];
    page.on('pageerror', (error) => erreurs.push(error.message));
    await page.route((url) => url.pathname.startsWith('/api/'), async (route) => {
      const requete = route.request(), url = new URL(requete.url()), chemin = url.pathname;
      if (['17293', '17393'].includes(url.port)) throw new Error('Un moteur réel est hors périmètre');
      if (!['GET', 'OPTIONS'].includes(requete.method())) {
        mutations.push({ chemin, methode: requete.method() });
        return route.fulfill({ status: 403, json: { detail: 'Recette en lecture seule' } });
      }
      if (chemin === '/api/config/onboarding-complete') return route.fulfill({ json: { completed: true } });
      if (chemin === '/api/memory/projects') return route.fulfill({ json: [projet] });
      if (chemin === '/api/memory/contacts') return route.fulfill({ json: [contact] });
      if (chemin === `/api/memory/projects/${projet.id}/ensemble`) return route.fulfill({ json: ensemble });
      if (chemin === `/api/memory/projects/${projet.id}/files`) return route.fulfill({ json: { files: [], total: 0, truncated: false } });
      return route.continue();
    });
    await page.goto(base, { waitUntil: 'networkidle' });
    const action = (id) => page.evaluate((identifiant) => window.__therese.runAction(identifiant), id);
    const boite = (locator) => locator.evaluate((element) => {
      const r = element.getBoundingClientRect();
      return { haut: r.top, bas: r.bottom, gauche: r.left, largeur: r.width };
    });
    const controles = [];

    await action('projects.open');
    await page.getByText(projet.name, { exact: true }).click();
    const fenetre = page.getByRole('dialog', { name: `Projet ${projet.name}`, exact: true });
    await expect(fenetre.getByRole('button', { name: 'Ouvrir la conversation Devis Ardent' })).toBeVisible();

    // 1. La bordure ne va qu'à ce qui mène quelque part.
    const bordure = (locator) => locator.evaluate((element) => {
      const s = getComputedStyle(element);
      return ['Top', 'Right', 'Bottom', 'Left'].some((cote) => s[`border${cote}Style`] !== 'none' && parseFloat(s[`border${cote}Width`]) > 0);
    });
    expect(await bordure(fenetre.getByRole('button', { name: 'Ouvrir la conversation Devis Ardent' }))).toBe(true);
    const ligneTache = fenetre.getByText('Métrer la pièce', { exact: true }).locator('..');
    expect(await bordure(ligneTache)).toBe(false);
    controles.push('bordure-reservee-aux-destinations');

    // 2, cause : le contenu défilant est le bloc conteneur de ses éléments
    // positionnés (étiquettes sr-only), qui ne débordent donc pas sur la fenêtre.
    const horsDuContenu = await fenetre.evaluate((element) => {
      const contenu = element.querySelector('.overflow-y-auto');
      return [...element.querySelectorAll('.sr-only')]
        .filter((e) => getComputedStyle(e).position === 'absolute')
        .filter((e) => !contenu || !contenu.contains(e.offsetParent)).length;
    });
    expect(horsDuContenu).toBe(0);
    expect(await fenetre.evaluate((element) => element.scrollHeight - element.clientHeight)).toBeLessThanOrEqual(1);
    controles.push('contenu-defilant-bloc-conteneur');

    // 2, symptôme, et 3 : l'en-tête ne bouge pas, les boutons ont leur ligne.
    const enTete = fenetre.getByRole('heading', { level: 2, name: projet.name });
    const avant = await boite(enTete);
    const supprimer = fenetre.getByRole('button', { name: 'Supprimer', exact: true });
    await supprimer.click();
    const statut = fenetre.getByRole('status').filter({ hasText: 'La suppression emporte' });
    await expect(statut).toBeVisible();
    await page.waitForTimeout(300);
    const apres = await boite(enTete);
    expect(Math.abs(apres.haut - avant.haut)).toBeLessThanOrEqual(1);
    expect(await fenetre.evaluate((element) => element.scrollTop)).toBe(0);
    controles.push('en-tete-immobile');
    const texte = await boite(statut.locator('..'));
    const blocDeLaQuestion = statut.locator('../..');
    // Le formulaire a son propre « Annuler » : on vise celui de la question.
    const boutons = await boite(blocDeLaQuestion.getByRole('button', { name: 'Annuler', exact: true }).locator('..'));
    const bloc = await boite(blocDeLaQuestion);
    expect(boutons.haut).toBeGreaterThanOrEqual(texte.bas - 1);
    expect(texte.largeur).toBeGreaterThanOrEqual(0.8 * bloc.largeur);
    controles.push('fenetre-boutons-sur-leur-ligne');
    await page.screenshot({ path: fileURLToPath(new URL(`${largeur}-fenetre-confirmation.png`, sortie)) });

    // Constat 7 : Échap ne ferme que la confirmation.
    await page.keyboard.press('Escape');
    await expect(statut).toBeHidden();
    await expect(fenetre).toBeVisible();
    await expect(supprimer).toBeFocused();
    controles.push('echap-ne-ferme-que-la-confirmation');
    await fenetre.getByRole('button', { name: 'Fermer', exact: true }).click();
    await expect(fenetre).toBeHidden();

    // 3, vue Projets : même confirmation, en boîte de dialogue.
    await page.getByRole('button', { name: `Supprimer ${projet.name}`, exact: true }).click();
    const dialogue = page.getByRole('dialog', { name: 'Supprimer ce projet ?', exact: true });
    const statutDialogue = dialogue.getByRole('status').filter({ hasText: 'La suppression emporte' });
    await expect(statutDialogue).toBeVisible();
    const phrase = await boite(statutDialogue);
    const rangee = await boite(dialogue.getByRole('button', { name: 'Annuler', exact: true }).locator('..'));
    expect(rangee.haut).toBeGreaterThanOrEqual(phrase.bas - 1);
    expect(phrase.largeur).toBeGreaterThanOrEqual(0.9 * rangee.largeur);
    controles.push('vue-projets-boutons-sur-leur-ligne');
    await page.screenshot({ path: fileURLToPath(new URL(`${largeur}-vue-projets-confirmation.png`, sortie)) });
    await page.keyboard.press('Escape');
    await expect(dialogue).toBeHidden();

    expect(mutations).toEqual([]);
    expect(erreurs).toEqual([]);
    resultats.push({ viewport: `${largeur}x800`, controles, erreurs, mutations });
    await contexte.close();
  }
} finally {
  await navigateur.close();
  await writeFile(new URL('resultats.json', sortie), `${JSON.stringify(resultats, null, 2)}\n`);
}
console.log(JSON.stringify({ largeurs: resultats.length, ok: resultats.length === 2 }));
