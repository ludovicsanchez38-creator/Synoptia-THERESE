/**
 * Parcours 06 - Navigation & Sidebar
 *
 * Scenario : ouvrir la sidebar -> conversations listees -> search
 *            -> nouvelle conversation -> app-main intact
 *
 * Depuis le 11/06/2026 la sidebar est FERMEE au lancement (l'utilisateur
 * atterrit sur l'Accueil) : le beforeEach l'ouvre via le raccourci clavier.
 *
 * User Stories : US-700, US-023, US-018
 */

import { test, expect } from '@playwright/test';

test.describe('Parcours 06 - Navigation', () => {
  test.beforeEach(async ({ page }) => {
    await page.addInitScript(() => {
      localStorage.setItem('onboarding_complete', 'true');
    });
    await page.goto('/');
    await page.waitForLoadState('networkidle', { timeout: 15000 });
    await page.waitForSelector('[data-testid="app-main"]', { timeout: 15000 });
    // Sidebar fermee par defaut : l'ouvrir (⌘B sur macOS, Ctrl+B ailleurs)
    const modifier = process.platform === 'darwin' ? 'Meta' : 'Control';
    await page.keyboard.press(`${modifier}+b`);
    await page.waitForSelector('[data-testid="sidebar"]', { timeout: 10000 });
  });

  /** Helper : depuis le dashboard, cliquer "Passer au chat" pour acceder au chat */
  async function navigateToChat(page: import('@playwright/test').Page) {
    const passerAuChat = page.getByRole('button', { name: /passer au chat/i });
    await expect(passerAuChat).toBeVisible({ timeout: 15000 });
    await passerAuChat.click();
    await expect(page.getByTestId('chat-message-input')).toBeVisible({ timeout: 10000 });
  }

  test('US-700.HP : la sidebar s\'ouvre au raccourci clavier', async ({ page }) => {
    const sidebar = page.getByTestId('sidebar');
    await expect(sidebar).toBeVisible({ timeout: 15000 });
  });

  test('US-700.HP : la liste des conversations est presente dans la sidebar', async ({ page }) => {
    const conversationList = page.getByTestId('sidebar-conversation-list');
    await expect(conversationList).toBeVisible({ timeout: 10000 });
  });

  test('US-023.HP : le champ de recherche sidebar est visible et fonctionnel', async ({ page }) => {
    const searchInput = page.getByTestId('sidebar-search-input');
    await expect(searchInput).toBeVisible({ timeout: 10000 });

    await searchInput.fill('recherche test');
    await expect(searchInput).toHaveValue('recherche test');
  });

  test('US-018.HP : le bouton "Nouvelle conversation" est visible et cliquable', async ({ page }) => {
    const newConvBtn = page.getByTestId('sidebar-new-conversation-btn');
    await expect(newConvBtn).toBeVisible({ timeout: 10000 });

    await newConvBtn.click();

    // Apres clic sur nouvelle conversation, le chat doit etre visible
    const chatInput = page.getByTestId('chat-message-input');
    await expect(chatInput).toBeVisible({ timeout: 10000 });
  });

  test('US-018.HP : creer une nouvelle conversation vide le chat', async ({ page }) => {
    // D'abord passer au chat depuis le dashboard
    await navigateToChat(page);

    const chatInput = page.getByTestId('chat-message-input');
    await expect(chatInput).toBeVisible({ timeout: 10000 });

    // Cliquer sur nouvelle conversation
    await page.getByTestId('sidebar-new-conversation-btn').click();

    // Attendre que le chat input soit visible (signe que la nouvelle conversation est prete)
    await expect(chatInput).toBeVisible({ timeout: 10000 });

    // Le chat doit etre reinitialise (liste de messages vide ou prompts guides visibles)
    const messageList = page.getByTestId('chat-message-list');
    if (await messageList.isVisible()) {
      const messages = page.getByTestId('chat-message-item');
      const count = await messages.count();
      // Une nouvelle conversation ne devrait pas avoir de messages utilisateur
      expect(count).toBeLessThanOrEqual(1); // 0 ou 1 (message systeme eventuel)
    }
  });

  test('US-700.HP : app-main reste intact apres les navigations', async ({ page }) => {
    const appMain = page.getByTestId('app-main');
    await expect(appMain).toBeVisible({ timeout: 15000 });

    // Ouvrir settings puis fermer
    await page.getByTestId('settings-btn').click();
    await expect(page.getByTestId('settings-modal')).toBeVisible({ timeout: 5000 });
    await page.getByTestId('settings-close-btn').click();
    await expect(page.getByTestId('settings-modal')).not.toBeVisible({ timeout: 5000 });

    // app-main toujours la
    await expect(appMain).toBeVisible();

    // Nouvelle conversation
    await page.getByTestId('sidebar-new-conversation-btn').click();

    // app-main toujours la
    await expect(appMain).toBeVisible();
  });

  test('US-023.HP : la recherche filtre les conversations dans la sidebar', async ({ page }) => {
    const searchInput = page.getByTestId('sidebar-search-input');
    await expect(searchInput).toBeVisible({ timeout: 10000 });

    // Rechercher un terme qui ne devrait pas matcher
    await searchInput.fill('zzz_terme_impossible_xyz');

    // Attendre que le filtrage soit applique
    await expect(async () => {
      const conversationItems = page.getByTestId('sidebar-conversation-item');
      const count = await conversationItems.count();
      expect(count).toBe(0);
    }).toPass({ timeout: 5000 });
  });

  test('US-023.HP : vider la recherche restaure les conversations', async ({ page }) => {
    const searchInput = page.getByTestId('sidebar-search-input');
    await expect(searchInput).toBeVisible({ timeout: 10000 });

    // Rechercher puis effacer
    await searchInput.fill('test');
    await searchInput.fill('');

    // La liste doit etre restauree (le composant doit etre visible)
    const conversationList = page.getByTestId('sidebar-conversation-list');
    await expect(conversationList).toBeVisible({ timeout: 5000 });
  });

  test('US-700.HP : parcours complet navigation (sidebar -> search -> new conv -> settings -> retour)', async ({ page }) => {
    // 1. Sidebar visible
    await expect(page.getByTestId('sidebar')).toBeVisible({ timeout: 15000 });

    // 2. Recherche
    const searchInput = page.getByTestId('sidebar-search-input');
    await searchInput.fill('test');
    await searchInput.fill('');

    // 3. Nouvelle conversation (depuis le dashboard, doit basculer vers le chat)
    await page.getByTestId('sidebar-new-conversation-btn').click();
    await expect(page.getByTestId('chat-message-input')).toBeVisible({ timeout: 10000 });

    // 4. Ouvrir settings
    await page.getByTestId('settings-btn').click();
    await expect(page.getByTestId('settings-modal')).toBeVisible({ timeout: 5000 });

    // 5. Fermer settings
    await page.getByTestId('settings-close-btn').click();
    await expect(page.getByTestId('settings-modal')).not.toBeVisible({ timeout: 5000 });

    // 6. Tout est intact
    await expect(page.getByTestId('app-main')).toBeVisible();
    await expect(page.getByTestId('sidebar')).toBeVisible();
    await expect(page.getByTestId('chat-message-input')).toBeVisible();
  });
});
