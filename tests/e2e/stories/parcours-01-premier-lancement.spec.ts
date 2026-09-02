/**
 * Parcours 01 - Premier lancement
 *
 * Scénario : ouvrir l'application, atteindre le composeur, ouvrir puis fermer
 *            les réglages, et vérifier les commandes du composeur.
 *
 * User Stories : US-005, US-002, US-017, US-037
 *
 * Réécrit le 02/09/2026 (B-149). Ce fichier visait l'ANCIENNE coque dans son
 * entier, et c'était démontrable sans navigateur : `ConversationSidebar` (qui
 * porte `sidebar` et `sidebar-new-conversation-btn`) et `ChatHeader` (qui porte
 * `settings-btn`) n'ont AUCUN importeur hors de leurs propres tests, et la
 * chaîne « Passer au chat » n'existe nulle part dans `src/frontend/src`. Les
 * parcours 02, 05 et 06 avaient été réécrits le 01/09 ; celui-ci était resté en
 * arrière et sept de ses huit tests attendaient trente secondes un écran
 * disparu.
 *
 * Comme les parcours voisins, il passe désormais par le registre d'actions que
 * l'application expose déjà (celui-là même que sert la palette de commandes) :
 * les conversations vivent dans un tiroir, les réglages dans une modale.
 */

import { test, expect } from '@playwright/test';

import { ouvrirLApplication, ouvrirLaSurface } from './helpers/surfaces';

/** Ouvrir le composeur de chat par l'action du registre. */
async function ouvrirLeChat(page: import('@playwright/test').Page) {
  await ouvrirLaSurface(page, 'chat.new');
  await expect(page.getByTestId('chat-message-input')).toBeVisible({ timeout: 10000 });
}

test.describe('Parcours 01 - Premier lancement', () => {
  test.beforeEach(async ({ page, request }) => {
    await ouvrirLApplication(page, request);
  });

  test('US-005.HP : le conteneur principal app-main est visible au lancement', async ({ page }) => {
    const appMain = page.getByTestId('app-main');
    await expect(appMain).toBeVisible({ timeout: 15000 });
  });

  test('US-002.HP : le tiroir des conversations offre la creation d\'une conversation', async ({
    page,
  }) => {
    await ouvrirLaSurface(page, 'conversations.toggle');

    const tiroir = page.getByTestId('prototype-conversation-drawer');
    await expect(tiroir).toBeVisible({ timeout: 10000 });

    await expect(tiroir.getByRole('button', { name: /nouvelle conversation/i })).toBeVisible();
  });

  test('US-017.HP : le champ de saisie du chat est present et focusable', async ({ page }) => {
    await ouvrirLeChat(page);

    const chatInput = page.getByTestId('chat-message-input');
    await expect(chatInput).toBeVisible({ timeout: 10000 });

    await chatInput.click();
    await expect(chatInput).toBeFocused();
  });

  test('US-017.HP : le bouton envoyer est visible', async ({ page }) => {
    await ouvrirLeChat(page);

    const sendBtn = page.getByTestId('chat-send-btn');
    await expect(sendBtn).toBeVisible({ timeout: 10000 });
  });

  test('US-037.HP : ouvrir et fermer les parametres par leur action de registre', async ({
    page,
  }) => {
    // `settings-btn` vivait dans l'en-tête de chat, que la coque
    // conversationnelle ne monte plus (cf. l'en-tête de parcours-05).
    await ouvrirLaSurface(page, 'settings.open');

    const settingsModal = page.getByTestId('settings-modal');
    await expect(settingsModal).toBeVisible({ timeout: 8000 });

    await page.getByTestId('settings-close-btn').click();

    await expect(settingsModal).not.toBeVisible({ timeout: 5000 });
  });

  test('US-005.HP : parcours complet premier lancement (coque -> chat -> reglages -> fermer)', async ({
    page,
  }) => {
    // 1. App chargee
    await expect(page.getByTestId('app-main')).toBeVisible({ timeout: 15000 });

    // 2. Le tiroir des conversations repond
    await ouvrirLaSurface(page, 'conversations.toggle');
    await expect(page.getByTestId('prototype-conversation-drawer')).toBeVisible({ timeout: 10000 });

    // 3. Ouvrir le composeur
    await ouvrirLeChat(page);

    // 4. Taper un message (sans envoyer au LLM - on verifie juste la saisie)
    const chatInput = page.getByTestId('chat-message-input');
    await chatInput.fill('Bonjour THERESE');
    await expect(chatInput).toHaveValue('Bonjour THERESE');

    // 5. Ouvrir les reglages
    await ouvrirLaSurface(page, 'settings.open');
    await expect(page.getByTestId('settings-modal')).toBeVisible({ timeout: 8000 });

    // 6. Fermer les reglages
    await page.getByTestId('settings-close-btn').click();
    await expect(page.getByTestId('settings-modal')).not.toBeVisible({ timeout: 5000 });

    // 7. Le composeur survit a l'aller-retour
    await expect(chatInput).toBeVisible();
  });

  test('US-002.HP : le bouton piece jointe est accessible', async ({ page }) => {
    await ouvrirLeChat(page);

    const attachBtn = page.getByTestId('chat-attach-btn');
    await expect(attachBtn).toBeVisible({ timeout: 10000 });
  });

  test('US-002.HP : le bouton voix est accessible', async ({ page }) => {
    await ouvrirLeChat(page);

    // `chat-voice-btn` est le testId PAR DÉFAUT de `VoiceDictationButton`, que
    // `ChatInput` monte sans en passer d'autre. Le composeur d'accueil de la
    // coque en a un distinct (`prototype-chat-voice-btn`) : ce test vise celui
    // du chat, pas celui de l'accueil.
    const voiceBtn = page.getByTestId('chat-voice-btn');
    await expect(voiceBtn).toBeVisible({ timeout: 10000 });
  });
});
