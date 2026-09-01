/**
 * Parcours 02 - Mémoire (contacts et dossiers)
 *
 * Scénario : ouvrir la mémoire, vérifier ses commandes, chercher, créer.
 *
 * User Stories : US-503, US-504, US-506
 *
 * Réécrit le 01/09/2026. Les tests pressaient `Control+m` — un raccourci que
 * la coque conversationnelle ne reçoit pas quand le focus est dans le
 * composeur, et qui n'est pas le bon modificateur sur macOS. Ils passent
 * désormais par le registre d'actions de l'application, le même que sert la
 * palette de commandes. Le raccourci lui-même a son test dédié dans
 * parcours-06-navigation.
 */

import { expect, test } from '@playwright/test';

import { ouvrirLApplication, ouvrirLaSurface } from './helpers/surfaces';

test.describe('Parcours 02 - Mémoire', () => {
  test.beforeEach(async ({ page, request }) => {
    await ouvrirLApplication(page, request);
    await ouvrirLaSurface(page, 'memory.open');
    await expect(page.getByTestId('memory-panel')).toBeVisible({ timeout: 10000 });
  });

  test('US-503.HP : la mémoire s’ouvre et affiche son panneau', async ({ page }) => {
    await expect(page.getByTestId('memory-panel')).toBeVisible();
  });

  test('US-504.HP : le bouton d’ajout de contact est offert', async ({ page }) => {
    await expect(page.getByTestId('memory-add-contact-btn')).toBeVisible();
  });

  test('US-503.HP : la mémoire filtre par périmètre', async ({ page }) => {
    // L'ancien test cherchait un bouton « Nouveau projet » qui n'a jamais
    // existé dans cette surface : les dossiers se créent depuis leur propre
    // vue, ou par l'action `project.new`. Ce que la mémoire offre ici, ce
    // sont ses filtres de périmètre.
    const panneau = page.getByTestId('memory-panel');
    for (const filtre of ['Tout', 'Global', 'Projet']) {
      await expect(panneau.getByRole('button', { name: filtre, exact: true })).toBeVisible();
    }
  });

  test('US-506.HP : le champ de recherche accepte une saisie', async ({ page }) => {
    const recherche = page.getByTestId('memory-search-input');
    await expect(recherche).toBeVisible();

    await recherche.fill('test recherche');
    await expect(recherche).toHaveValue('test recherche');
  });

  test('US-506.HP : une recherche sans résultat le dit', async ({ page }) => {
    // L'ancien test assertait `expect(hasNoResultsMsg || true).toBe(true)` :
    // vrai quoi qu'il arrive. Il ne pouvait pas échouer, donc il ne prouvait
    // rien. La garantie réelle est qu'un terme introuvable ne laisse pas la
    // liste des contacts telle quelle.
    const recherche = page.getByTestId('memory-search-input');
    await recherche.fill('zzz_terme_inexistant_xyz');

    const panneau = page.getByTestId('memory-panel');
    await expect(panneau.getByText(/aucun|rien|vide/i).first()).toBeVisible({
      timeout: 8000,
    });
  });

  test('US-504.HP : ajouter un contact ouvre son formulaire', async ({ page }) => {
    const bouton = page.getByTestId('memory-add-contact-btn');
    await expect(bouton).toBeVisible({ timeout: 10000 });
    await bouton.click();

    const formulaire = page.getByRole('dialog').or(page.getByText(/nouveau contact/i));
    await expect(formulaire.first()).toBeVisible({ timeout: 5000 });
  });
});
