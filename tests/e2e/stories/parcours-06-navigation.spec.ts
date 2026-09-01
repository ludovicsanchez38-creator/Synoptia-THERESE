/**
 * Parcours 06 - Navigation
 *
 * Scénario : ouvrir le tiroir des conversations, chercher, en créer une,
 *            ouvrir puis fermer les réglages, et vérifier que la coque tient.
 *
 * User Stories : US-018, US-023, US-700
 *
 * Réécrit le 01/09/2026. Ces tests visaient la barre latérale de l'ancienne
 * coque (`sidebar`, `sidebar-search-input`, `sidebar-new-conversation-btn`) et
 * le bouton de réglages de l'en-tête de chat (`settings-btn`). La coque
 * conversationnelle ne monte plus aucun des deux : les conversations vivent
 * dans un tiroir (`prototype-conversation-drawer`), les réglages sont une
 * modale ouverte par le registre d'actions.
 *
 * Le raccourci clavier garde son propre test : c'est la seule chose que le
 * registre ne prouve pas.
 */

import { expect, test } from '@playwright/test';

import { fermerLaSurface, ouvrirLApplication, ouvrirLaSurface } from './helpers/surfaces';

/** Le tiroir des conversations, ouvert. */
async function ouvrirLeTiroir(page: import('@playwright/test').Page) {
  await ouvrirLaSurface(page, 'conversations.toggle');
  const tiroir = page.getByTestId('prototype-conversation-drawer');
  await expect(tiroir).toBeVisible({ timeout: 10000 });
  return tiroir;
}

test.describe('Parcours 06 - Navigation', () => {
  test.beforeEach(async ({ page, request }) => {
    await ouvrirLApplication(page, request);
  });

  test('US-700.HP : le raccourci clavier ouvre le tiroir des conversations', async ({ page }) => {
    // Le seul test qui éprouve le CHEMIN plutôt que la destination. Le
    // modificateur suit la plateforme, comme le hook de l'application, et le
    // focus doit quitter le composeur : `useKeyboardShortcuts` ignore les
    // raccourcis pendant une saisie.
    await page.locator('body').click({ position: { x: 5, y: 5 } });
    const modificateur = process.platform === 'darwin' ? 'Meta' : 'Control';
    await page.keyboard.press(`${modificateur}+b`);

    await expect(page.getByTestId('prototype-conversation-drawer')).toBeVisible({
      timeout: 10000,
    });
  });

  test('US-700.HP : le tiroir liste les conversations', async ({ page }) => {
    await ouvrirLeTiroir(page);
    await expect(page.getByTestId('prototype-conversation-list')).toBeVisible({
      timeout: 10000,
    });
  });

  test('US-023.HP : le champ de recherche du tiroir accepte une saisie', async ({ page }) => {
    const tiroir = await ouvrirLeTiroir(page);
    const recherche = tiroir.getByPlaceholder(/rechercher/i);
    await expect(recherche).toBeVisible({ timeout: 10000 });

    await recherche.fill('recherche test');
    await expect(recherche).toHaveValue('recherche test');
  });

  test('US-018.HP : « Nouvelle conversation » mène au composeur', async ({ page }) => {
    const tiroir = await ouvrirLeTiroir(page);
    await tiroir.getByRole('button', { name: /nouvelle conversation/i }).click();

    await expect(page.getByTestId('chat-message-input')).toBeVisible({ timeout: 10000 });
  });

  test('US-023.HP : une recherche sans correspondance vide la liste', async ({ page }) => {
    const tiroir = await ouvrirLeTiroir(page);
    const recherche = tiroir.getByPlaceholder(/rechercher/i);
    await recherche.fill('zzz_terme_impossible_xyz');

    // La garantie porte sur le RÉSULTAT du filtre, pas sur la présence d'un
    // message : une liste qui ne bouge pas serait un filtre qui ne filtre pas.
    await expect(async () => {
      const restantes = await tiroir.getByRole('button', { name: /^Actions pour /i }).count();
      expect(restantes).toBe(0);
    }).toPass({ timeout: 8000 });
  });

  test('US-023.HP : vider la recherche restaure la liste', async ({ page }) => {
    const tiroir = await ouvrirLeTiroir(page);
    const recherche = tiroir.getByPlaceholder(/rechercher/i);

    await recherche.fill('zzz_terme_impossible_xyz');
    await recherche.fill('');

    await expect(page.getByTestId('prototype-conversation-list')).toBeVisible({
      timeout: 8000,
    });
  });

  test('US-700.HP : la coque survit à l’ouverture et à la fermeture des réglages', async ({
    page,
  }) => {
    const coque = page.getByTestId('app-main');
    await expect(coque).toBeVisible({ timeout: 15000 });

    await ouvrirLaSurface(page, 'settings.open');
    await expect(page.getByTestId('settings-modal')).toBeVisible({ timeout: 8000 });

    await page.getByTestId('settings-close-btn').click();
    await expect(page.getByTestId('settings-modal')).not.toBeVisible({ timeout: 5000 });

    await expect(coque).toBeVisible();
  });

  test('US-700.HP : parcours complet — tiroir, recherche, conversation, réglages', async ({
    page,
  }) => {
    const tiroir = await ouvrirLeTiroir(page);

    const recherche = tiroir.getByPlaceholder(/rechercher/i);
    await recherche.fill('test');
    await recherche.fill('');

    await tiroir.getByRole('button', { name: /nouvelle conversation/i }).click();
    await expect(page.getByTestId('chat-message-input')).toBeVisible({ timeout: 10000 });

    await ouvrirLaSurface(page, 'settings.open');
    await expect(page.getByTestId('settings-modal')).toBeVisible({ timeout: 8000 });
    await fermerLaSurface(page);
    await expect(page.getByTestId('settings-modal')).not.toBeVisible({ timeout: 5000 });

    await expect(page.getByTestId('app-main')).toBeVisible();
    await expect(page.getByTestId('chat-message-input')).toBeVisible();
  });
});
