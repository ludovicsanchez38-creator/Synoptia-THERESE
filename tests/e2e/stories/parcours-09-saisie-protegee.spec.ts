/**
 * Parcours 09 - Une saisie en cours ne se perd pas en quittant la vue
 *
 * B-973 (Échap) et B-978 (sorties de la vue), cycle 11, 23/09/2026 : avec un
 * formulaire Tâche ou Rendez-vous modifié, Échap, le « Retour » d'en-tête de
 * la vue et le rail « Accueil » refermaient la vue et jetaient la saisie sans
 * rien demander. Chaque sortie pose désormais la question « Abandonner les
 * modifications ? » ; la saisie reste en place tant qu'on n'a pas répondu.
 *
 * Aucune écriture : les formulaires ne sont jamais enregistrés.
 */

import { expect, test, type Page } from '@playwright/test';

import { ouvrirLApplication, ouvrirLaSurface } from './helpers/surfaces';

const FORMULAIRES = [
  { nom: 'tâche', modifie: 'tâche modifiée', vierge: 'tâche vierge', vue: 'tasks.open', bouton: /Nouvelle tâche/ },
  { nom: 'rendez-vous', modifie: 'rendez-vous modifié', vierge: 'rendez-vous vierge', vue: 'calendar.open', bouton: /Nouveau rendez-vous/ },
] as const;

async function commencerUneSaisie(page: Page, vue: string, bouton: RegExp, texte: string) {
  await ouvrirLaSurface(page, vue);
  await page.getByRole('button', { name: bouton }).first().click();
  const titre = page.getByLabel(/Titre/).first();
  await expect(titre).toBeVisible({ timeout: 10000 });
  await titre.fill(texte);
  return titre;
}

const SORTIES: Array<[string, (page: Page) => Promise<void>]> = [
  ['Échap', (page) => page.keyboard.press('Escape')],
  ['le Retour d’en-tête de la vue', (page) => page.getByRole('button', { name: 'Revenir à la conversation unifiée' }).click()],
  ['le rail « Accueil »', (page) => page.getByRole('button', { name: 'Accueil', exact: true }).first().click()],
];

test.describe('Parcours 09 - Saisie protégée', () => {
  test.beforeEach(async ({ page, request }) => {
    await ouvrirLApplication(page, request);
  });

  for (const formulaire of FORMULAIRES) {
    for (const [nomSortie, sortir] of SORTIES) {
      test(`${formulaire.modifie} : ${nomSortie} pose la question et garde la saisie`, async ({ page }) => {
        const texte = `Saisie ${formulaire.nom} ${nomSortie}`;
        const titre = await commencerUneSaisie(page, formulaire.vue, formulaire.bouton, texte);
        await sortir(page);
        await expect(page.getByText(/Abandonner les modifications/)).toBeVisible({ timeout: 5000 });
        await expect(titre).toHaveValue(texte);
      });
    }

    test(`${formulaire.modifie} : Échap sous les Réglages ferme les Réglages, pas le formulaire`, async ({ page }) => {
      const texte = `Saisie ${formulaire.nom} sous les Réglages`;
      const titre = await commencerUneSaisie(page, formulaire.vue, formulaire.bouton, texte);
      await page.getByRole('button', { name: 'Paramètres', exact: true }).first().click();
      const reglages = page.getByRole('dialog').first();
      await expect(reglages).toBeVisible({ timeout: 10000 });
      await page.keyboard.press('Escape');
      await expect(page.getByRole('dialog')).toHaveCount(0, { timeout: 5000 });
      await expect(page.getByText(/Abandonner les modifications/)).toHaveCount(0);
      await expect(titre).toHaveValue(texte);
    });

    test(`${formulaire.vierge} : le Retour d’en-tête quitte sans question`, async ({ page }) => {
      await ouvrirLaSurface(page, formulaire.vue);
      await page.getByRole('button', { name: formulaire.bouton }).first().click();
      await expect(page.getByLabel(/Titre/).first()).toBeVisible({ timeout: 10000 });
      await page.getByRole('button', { name: 'Revenir à la conversation unifiée' }).click();
      await expect(page.getByText(/Abandonner les modifications/)).toHaveCount(0);
      await expect(page.getByLabel(/Titre/)).toHaveCount(0);
    });
  }
});
