/**
 * Parcours 04 - CRM
 *
 * Scenario : ouvrir panel CRM -> pipeline 7 colonnes
 *            -> bouton ajouter contact -> import vcf visible
 *
 * User Stories : US-300, US-301
 */

import { test, expect } from '@playwright/test';

import { passerLaMiseEnRoute } from './helpers/surfaces';

test.describe('Parcours 04 - CRM', () => {
  test.beforeEach(async ({ page, request }) => {
    await passerLaMiseEnRoute(request);
    await page.goto('/?panel=crm');
    await page.waitForLoadState('networkidle', { timeout: 15000 });
    await page.waitForSelector('[data-testid="app-main"]', { timeout: 15000 });
  });

  test('US-300.HP : le panel CRM s\'ouvre en mode standalone', async ({ page }) => {
    const crmPanel = page.getByTestId('crm-panel');
    await expect(crmPanel).toBeVisible({ timeout: 15000 });
  });

  test('US-300.HP : le pipeline contient 7 colonnes (stages)', async ({ page }) => {
    const crmPanel = page.getByTestId('crm-panel');
    await expect(crmPanel).toBeVisible({ timeout: 15000 });

    // Les 7 stages du pipeline
    const stages = ['Contact', 'Decouverte', 'Proposition', 'Signature', 'Livraison', 'Actif', 'Archive'];

    for (const stage of stages) {
      const stageLabel = page.getByText(stage, { exact: false });
      await expect(stageLabel.first()).toBeVisible({ timeout: 5000 });
    }
  });

  test('US-301.HP : le bouton "Ajouter un contact" est visible et cliquable', async ({ page }) => {
    const crmPanel = page.getByTestId('crm-panel');
    await expect(crmPanel).toBeVisible({ timeout: 15000 });

    const addBtn = page.getByRole('button', { name: /ajouter un contact/i });
    await expect(addBtn).toBeVisible();
    await addBtn.click();

    // Verifier qu'un formulaire ou modale de creation apparait
    const newContactTitle = page.getByText(/nouveau contact/i);
    await expect(newContactTitle.first()).toBeVisible({ timeout: 5000 });
  });

  test('US-301.HP : le bouton "Import .vcf" est visible', async ({ page }) => {
    const crmPanel = page.getByTestId('crm-panel');
    await expect(crmPanel).toBeVisible({ timeout: 15000 });

    const importVcfBtn = page.getByText(/import.*\.vcf/i);
    await expect(importVcfBtn.first()).toBeVisible();
  });

  test('US-300.HP : le formulaire nouveau contact CRM contient les champs essentiels', async ({ page }) => {
    const crmPanel = page.getByTestId('crm-panel');
    await expect(crmPanel).toBeVisible({ timeout: 15000 });

    // Ouvrir le formulaire
    const addBtn = page.getByRole('button', { name: /ajouter un contact/i });
    await addBtn.click();

    // Verifier la presence des champs essentiels dans le dialogue
    const dialog = page.getByRole('dialog').or(page.locator('[aria-label="Nouveau contact CRM"]'));
    await expect(dialog.first()).toBeVisible({ timeout: 5000 });

    // Champs attendus : prenom, nom, email, entreprise
    const fields = ['Prenom', 'Nom', 'Email', 'Entreprise'];
    for (const field of fields) {
      const label = page.getByText(new RegExp(field, 'i'));
      // Au moins un element avec ce texte doit etre present
      const count = await label.count();
      expect(count).toBeGreaterThanOrEqual(1);
    }
  });

  test('US-300.HP : parcours complet CRM (ouvrir -> voir pipeline -> ajouter contact -> fermer)', async ({ page }) => {
    // 1. Panel visible
    const crmPanel = page.getByTestId('crm-panel');
    await expect(crmPanel).toBeVisible({ timeout: 15000 });

    // 2. Pipeline present avec au moins la colonne "Contact"
    await expect(page.getByText('Contact').first()).toBeVisible();

    // 3. Ouvrir formulaire ajout
    await page.getByRole('button', { name: /ajouter un contact/i }).click();
    const dialog = page.getByRole('dialog').or(page.locator('[aria-label="Nouveau contact CRM"]'));
    await expect(dialog.first()).toBeVisible({ timeout: 5000 });

    // 4. Fermer le formulaire (bouton Annuler, X, ou Escape)
    await page.keyboard.press('Escape');

    // 5. Verifier que le panel CRM est toujours visible apres fermeture
    await expect(crmPanel).toBeVisible();
  });
});
