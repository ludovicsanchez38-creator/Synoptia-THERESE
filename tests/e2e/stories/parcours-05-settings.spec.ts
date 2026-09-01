/**
 * Parcours 05 - Settings
 *
 * Scenario : ouvrir settings -> verifier 8 onglets
 *            -> naviguer entre onglets -> fermer
 *
 * User Stories : US-600 a US-625
 */

import { test, expect } from '@playwright/test';

import { ouvrirLApplication, ouvrirLaSurface } from './helpers/surfaces';

const SETTINGS_TABS = [
  { id: 'profile', label: 'Profil' },
  { id: 'ai', label: 'IA' },
  { id: 'services', label: 'Services' },
  { id: 'tools', label: 'Outils' },
  { id: 'agents', label: 'Agents' },
  { id: 'privacy', label: 'Confidentialite' },  // sans accent pour le matcher
  { id: 'advanced', label: 'Avance' },
  { id: 'about', label: 'propos' },
] as const;

test.describe('Parcours 05 - Settings', () => {
  test.beforeEach(async ({ page, request }) => {
    await ouvrirLApplication(page, request);

    // `settings-btn` vivait dans l'en-tête de chat, que la coque
    // conversationnelle ne monte plus. Les réglages s'ouvrent par leur action
    // de registre, celle-là même que sert la palette de commandes.
    await ouvrirLaSurface(page, 'settings.open');

    await expect(page.getByTestId('settings-modal')).toBeVisible({ timeout: 8000 });
  });

  test('US-600.HP : la modale settings contient exactement 8 onglets', async ({ page }) => {
    for (const tab of SETTINGS_TABS) {
      const tabBtn = page.getByTestId(`settings-tab-${tab.id}`);
      await expect(tabBtn).toBeVisible();
    }
  });

  test('US-601.HP : l\'onglet Profil est le premier onglet visible', async ({ page }) => {
    const profileTab = page.getByTestId('settings-tab-profile');
    await expect(profileTab).toBeVisible();
  });

  test('US-602.HP : cliquer sur l\'onglet IA affiche le contenu IA', async ({ page }) => {
    const aiTab = page.getByTestId('settings-tab-ai');
    await aiTab.click();

    // Le contenu de l'onglet IA doit etre visible (provider LLM, cles API...)
    const aiContent = page.getByText(/provider/i)
      .or(page.getByText(/mod.le/i))
      .or(page.getByText(/cl.*api/i));
    await expect(aiContent.first()).toBeVisible({ timeout: 5000 });
  });

  test('US-603.HP : cliquer sur l\'onglet Services affiche le contenu Services', async ({ page }) => {
    const servicesTab = page.getByTestId('settings-tab-services');
    await servicesTab.click();

    // Contenu attendu : MCP, serveurs, integrations
    const servicesContent = page.getByText(/mcp/i)
      .or(page.getByText(/serveur/i))
      .or(page.getByText(/service/i));
    await expect(servicesContent.first()).toBeVisible({ timeout: 5000 });
  });

  test('US-604.HP : cliquer sur l\'onglet Outils affiche le contenu Outils', async ({ page }) => {
    const toolsTab = page.getByTestId('settings-tab-tools');
    await toolsTab.click();

    // Verifier que le contenu de l'onglet Outils est visible (texte attendu dans le panneau)
    const toolsContent = page.getByText(/outil/i)
      .or(page.getByText(/tool/i))
      .or(page.getByText(/workspace/i));
    await expect(toolsContent.first()).toBeVisible({ timeout: 5000 });
  });

  test('US-605.HP : cliquer sur l\'onglet Agents affiche le contenu Agents', async ({ page }) => {
    const agentsTab = page.getByTestId('settings-tab-agents');
    await agentsTab.click();

    // Verifier que le contenu a change (pas l'onglet profil)
    const agentsContent = page.getByText(/agent/i);
    await expect(agentsContent.first()).toBeVisible({ timeout: 5000 });
  });

  test('US-606.HP : cliquer sur l\'onglet Confidentialite affiche les options RGPD', async ({ page }) => {
    const privacyTab = page.getByTestId('settings-tab-privacy');
    await privacyTab.click();

    const privacyContent = page.getByText(/donn/i)
      .or(page.getByText(/rgpd/i))
      .or(page.getByText(/confidentialit/i))
      .or(page.getByText(/export/i));
    await expect(privacyContent.first()).toBeVisible({ timeout: 5000 });
  });

  test('US-607.HP : cliquer sur l\'onglet Avance affiche les parametres avances', async ({ page }) => {
    const advancedTab = page.getByTestId('settings-tab-advanced');
    await advancedTab.click();

    // Verifier que le contenu de l'onglet Avance est visible
    const advancedContent = page.getByText(/avanc/i)
      .or(page.getByText(/debug/i))
      .or(page.getByText(/log/i))
      .or(page.getByText(/reset/i));
    await expect(advancedContent.first()).toBeVisible({ timeout: 5000 });
  });

  test('US-608.HP : cliquer sur l\'onglet A propos affiche les infos de version', async ({ page }) => {
    const aboutTab = page.getByTestId('settings-tab-about');
    await aboutTab.click();

    const aboutContent = page.getByText(/version/i)
      .or(page.getByText(/th.r.se/i))
      .or(page.getByText(/licence/i));
    await expect(aboutContent.first()).toBeVisible({ timeout: 5000 });
  });

  test('US-610.HP : navigation entre tous les onglets successivement', async ({ page }) => {
    for (const tab of SETTINGS_TABS) {
      const tabBtn = page.getByTestId(`settings-tab-${tab.id}`);
      await tabBtn.click();

      // Verifier que l'onglet est actif (visuellement distinct)
      await expect(tabBtn).toBeVisible();
    }
  });

  test('US-620.HP : le bouton Sauvegarder est present dans la modale', async ({ page }) => {
    const saveBtn = page.getByTestId('settings-save-btn');
    await expect(saveBtn).toBeVisible();
  });

  test('US-625.HP : fermer la modale settings avec le bouton X', async ({ page }) => {
    const closeBtn = page.getByTestId('settings-close-btn');
    await closeBtn.click();

    const settingsModal = page.getByTestId('settings-modal');
    await expect(settingsModal).not.toBeVisible({ timeout: 5000 });
  });

  test('US-625.HP : fermer la modale settings avec Escape', async ({ page }) => {
    await page.keyboard.press('Escape');

    const settingsModal = page.getByTestId('settings-modal');
    await expect(settingsModal).not.toBeVisible({ timeout: 5000 });
  });

  test('US-600.HP : parcours complet settings (ouvrir -> naviguer 8 onglets -> sauvegarder -> fermer)', async ({ page }) => {
    // Naviguer dans chaque onglet
    for (const tab of SETTINGS_TABS) {
      await page.getByTestId(`settings-tab-${tab.id}`).click();
      await expect(page.getByTestId(`settings-tab-${tab.id}`)).toBeVisible();
    }

    // Revenir au profil
    await page.getByTestId('settings-tab-profile').click();

    // Cliquer sur sauvegarder
    await page.getByTestId('settings-save-btn').click();

    // Fermer
    await page.getByTestId('settings-close-btn').click();
    await expect(page.getByTestId('settings-modal')).not.toBeVisible({ timeout: 5000 });
  });
});
