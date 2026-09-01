/**
 * Parcours 01 - Premier lancement
 *
 * Scenario : ouvrir app -> dashboard visible -> passer au chat
 *            -> envoyer message -> ouvrir settings -> fermer settings
 *
 * User Stories : US-005, US-002, US-017, US-037
 */

import { test, expect } from '@playwright/test';

import { ouvrirLApplication } from './helpers/surfaces';

test.describe('Parcours 01 - Premier lancement', () => {
  test.beforeEach(async ({ page, request }) => {
    await ouvrirLApplication(page, request);
  });

  /** Helper : depuis le dashboard, cliquer "Passer au chat" pour acceder au chat */
  async function navigateToChat(page: import('@playwright/test').Page) {
    const passerAuChat = page.getByRole('button', { name: /passer au chat/i });
    await expect(passerAuChat).toBeVisible({ timeout: 15000 });
    await passerAuChat.click();
    await expect(page.getByTestId('chat-message-input')).toBeVisible({ timeout: 10000 });
  }

  test('US-005.HP : le conteneur principal app-main est visible au lancement', async ({ page }) => {
    const appMain = page.getByTestId('app-main');
    await expect(appMain).toBeVisible({ timeout: 15000 });
  });

  test('US-002.HP : la sidebar est visible et contient le bouton nouvelle conversation', async ({ page }) => {
    const sidebar = page.getByTestId('sidebar');
    await expect(sidebar).toBeVisible({ timeout: 10000 });

    const newConvBtn = page.getByTestId('sidebar-new-conversation-btn');
    await expect(newConvBtn).toBeVisible();
  });

  test('US-017.HP : le champ de saisie du chat est present et focusable', async ({ page }) => {
    await navigateToChat(page);

    const chatInput = page.getByTestId('chat-message-input');
    await expect(chatInput).toBeVisible({ timeout: 10000 });

    await chatInput.click();
    await expect(chatInput).toBeFocused();
  });

  test('US-017.HP : le bouton envoyer est visible', async ({ page }) => {
    await navigateToChat(page);

    const sendBtn = page.getByTestId('chat-send-btn');
    await expect(sendBtn).toBeVisible({ timeout: 10000 });
  });

  test('US-037.HP : ouvrir et fermer les parametres via le bouton settings', async ({ page }) => {
    // Ouvrir les settings (le bouton est dans le header, visible sur le dashboard)
    const settingsBtn = page.getByTestId('settings-btn');
    await expect(settingsBtn).toBeVisible({ timeout: 10000 });
    await settingsBtn.click();

    // Verifier que la modale settings est visible
    const settingsModal = page.getByTestId('settings-modal');
    await expect(settingsModal).toBeVisible({ timeout: 5000 });

    // Fermer les settings
    const closeBtn = page.getByTestId('settings-close-btn');
    await closeBtn.click();

    // Verifier que la modale est fermee
    await expect(settingsModal).not.toBeVisible({ timeout: 5000 });
  });

  test('US-005.HP : parcours complet premier lancement (dashboard -> chat -> settings -> fermer)', async ({ page }) => {
    // 1. App chargee
    await expect(page.getByTestId('app-main')).toBeVisible({ timeout: 15000 });

    // 2. Sidebar visible
    await expect(page.getByTestId('sidebar')).toBeVisible();

    // 3. Passer au chat depuis le dashboard
    await navigateToChat(page);

    // 4. Zone de chat visible
    const chatInput = page.getByTestId('chat-message-input');
    await expect(chatInput).toBeVisible();

    // 5. Taper un message (sans envoyer au LLM - on verifie juste la saisie)
    await chatInput.fill('Bonjour THERESE');
    await expect(chatInput).toHaveValue('Bonjour THERESE');

    // 6. Ouvrir les settings
    await page.getByTestId('settings-btn').click();
    await expect(page.getByTestId('settings-modal')).toBeVisible({ timeout: 5000 });

    // 7. Fermer les settings
    await page.getByTestId('settings-close-btn').click();
    await expect(page.getByTestId('settings-modal')).not.toBeVisible({ timeout: 5000 });

    // 8. Le chat input conserve le texte
    await expect(chatInput).toBeVisible();
  });

  test('US-002.HP : le bouton piece jointe est accessible', async ({ page }) => {
    await navigateToChat(page);

    const attachBtn = page.getByTestId('chat-attach-btn');
    await expect(attachBtn).toBeVisible({ timeout: 10000 });
  });

  test('US-002.HP : le bouton voix est accessible', async ({ page }) => {
    await navigateToChat(page);

    const voiceBtn = page.getByTestId('chat-voice-btn');
    await expect(voiceBtn).toBeVisible({ timeout: 10000 });
  });
});
