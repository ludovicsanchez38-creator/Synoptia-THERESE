/**
 * Parcours 03 - Email
 *
 * Scenario : ouvrir panel email -> wizard setup visible
 *            -> options OAuth et SMTP disponibles
 *
 * User Stories : US-111, US-112, US-113
 */

import { test, expect } from '@playwright/test';

import { passerLaMiseEnRoute } from './helpers/surfaces';

test.describe('Parcours 03 - Email', () => {
  test.beforeEach(async ({ request }) => {
    // App.tsx interroge le backend, pas le stockage local : sur la base
    // jetable des E2E l'assistant de mise en route recouvrait chaque surface.
    await passerLaMiseEnRoute(request);
  });

  test('US-111.HP : le panel email s\'ouvre en mode standalone via ?panel=email', async ({ page }) => {
    await page.goto('/?panel=email');
    await page.waitForLoadState('networkidle', { timeout: 15000 });
    await page.waitForSelector('[data-testid="app-main"]', { timeout: 15000 });

    const emailPanel = page.getByTestId('email-panel');
    await expect(emailPanel).toBeVisible({ timeout: 15000 });
  });

  test('US-112.HP : le wizard de configuration email apparait quand aucun compte n\'est configure', async ({ page }) => {
    await page.goto('/?panel=email');
    await page.waitForLoadState('networkidle', { timeout: 15000 });

    // Le wizard doit s'afficher automatiquement si aucun compte email n'est configure
    // Il est rendu via createPortal donc dans document.body
    const wizardDialog = page.getByRole('dialog', { name: /configuration email/i });
    await expect(wizardDialog).toBeVisible({ timeout: 15000 });
  });

  test('US-112.HP : le wizard affiche le titre "Configuration Email"', async ({ page }) => {
    await page.goto('/?panel=email');
    await page.waitForLoadState('networkidle', { timeout: 15000 });

    const title = page.getByText('Configuration Email');
    await expect(title.first()).toBeVisible({ timeout: 15000 });
  });

  test('US-113.HP : le wizard propose l\'option Gmail OAuth', async ({ page }) => {
    await page.goto('/?panel=email');
    await page.waitForLoadState('networkidle', { timeout: 15000 });

    // Le wizard step 1 = ChoiceStep avec les options Gmail et SMTP
    const gmailOption = page.getByText(/gmail/i).first();
    await expect(gmailOption).toBeVisible({ timeout: 15000 });
  });

  test('US-113.HP : le wizard propose l\'option SMTP classique', async ({ page }) => {
    await page.goto('/?panel=email');
    await page.waitForLoadState('networkidle', { timeout: 15000 });

    const smtpOption = page.getByText(/smtp/i).first();
    await expect(smtpOption).toBeVisible({ timeout: 15000 });
  });

  test('US-112.HP : le wizard a un bouton de fermeture fonctionnel', async ({ page }) => {
    await page.goto('/?panel=email');
    await page.waitForLoadState('networkidle', { timeout: 15000 });

    // Attendre que le wizard soit visible
    const wizardDialog = page.getByRole('dialog', { name: /configuration email/i });
    await expect(wizardDialog).toBeVisible({ timeout: 15000 });

    // Cliquer sur le bouton Fermer (X)
    const closeBtn = page.getByRole('button', { name: /fermer/i });
    await closeBtn.click();

    // Le wizard doit disparaitre
    await expect(wizardDialog).not.toBeVisible({ timeout: 5000 });
  });

  test('US-113.HP : selectionner Gmail navigate vers l\'etape suivante du wizard', async ({ page }) => {
    await page.goto('/?panel=email');
    await page.waitForLoadState('networkidle', { timeout: 15000 });

    // Cliquer sur l'option Gmail
    const gmailCard = page.getByText(/gmail oauth/i);
    await expect(gmailCard).toBeVisible({ timeout: 15000 });
    await gmailCard.click();

    // Verifier qu'on passe a l'etape 2 (le texte "Etape 2" ou le contenu change)
    const step2Indicator = page.getByText(/tape 2/i).or(page.getByText(/tape 4/i));
    await expect(step2Indicator.first()).toBeVisible({ timeout: 5000 });
  });

  test('US-113.HP : selectionner SMTP navigate vers l\'etape SMTP', async ({ page }) => {
    await page.goto('/?panel=email');
    await page.waitForLoadState('networkidle', { timeout: 15000 });

    // Cliquer sur l'option SMTP
    const smtpCard = page.getByText(/smtp/i).first();
    await expect(smtpCard).toBeVisible({ timeout: 15000 });
    await smtpCard.click();

    // Le wizard avance (etape 2 pour SMTP = formulaire config SMTP)
    const step2Indicator = page.getByText(/tape 2/i);
    await expect(step2Indicator.first()).toBeVisible({ timeout: 5000 });
  });
});
