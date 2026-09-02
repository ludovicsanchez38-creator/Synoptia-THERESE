/**
 * Parcours 04 - CRM
 *
 * Scenario : ouvrir le panneau CRM -> pipeline a 7 colonnes
 *            -> bouton ajouter contact -> import vcf visible
 *
 * User Stories : US-300, US-301
 *
 * Révisé le 02/09/2026 (B-148). Le test des sept colonnes cherchait ses
 * libellés par `page.getByText(stage, { exact: false })`, c'est-à-dire une
 * SOUS-CHAÎNE dans TOUTE la page, puis prenait `.first()` : « Contact » était
 * satisfait par le bouton « Ajouter un contact » du même panneau, et le test
 * ne prouvait rien sur les colonnes. Les libellés étaient de surcroît écrits
 * sans accent (« Decouverte » pour « Découverte »), si bien que le test
 * échouait sur ce seul mot tout en donnant l'illusion de mesurer sept
 * colonnes. Il est désormais ancré au panneau, compte les en-têtes et compare
 * les libellés EXACTS, dans l'ordre.
 */

import { test, expect } from '@playwright/test';

import { ouvrirLApplication, ouvrirLaSurface } from './helpers/surfaces';

/**
 * Les sept colonnes du pipeline, dans l'ordre de `PIPELINE_STAGES`
 * (src/frontend/src/components/crm/PipelineView.tsx). Accents compris : ce
 * sont les libellés que l'utilisateur lit.
 */
const COLONNES_DU_PIPELINE = [
  'Contact',
  'Découverte',
  'Proposition',
  'Signature',
  'Livraison',
  'Actif',
  'Archive',
] as const;

test.describe('Parcours 04 - CRM', () => {
  test.beforeEach(async ({ page, request }) => {
    await ouvrirLApplication(page, request);
    // `?panel=crm` et `?panel=email` ne sont plus reconnus : le lien profond
    // n'accepte que `board` et `atelier`. La surface s'ouvre par son action
    // de registre, qui ne depend d'aucun parametre d'URL.
    await ouvrirLaSurface(page, 'crm.open');
    await expect(page.getByTestId('crm-panel')).toBeVisible({ timeout: 15000 });
  });

  test("US-300.HP : le panel CRM s'ouvre en mode standalone", async ({ page }) => {
    const crmPanel = page.getByTestId('crm-panel');
    await expect(crmPanel).toBeVisible({ timeout: 15000 });
  });

  test('US-300.HP : le pipeline contient 7 colonnes (stages)', async ({ page }) => {
    const crmPanel = page.getByTestId('crm-panel');
    await expect(crmPanel).toBeVisible({ timeout: 15000 });

    // L'onglet « Pipeline » est celui d'ouverture, et `DroppableStage` est le
    // SEUL à poser un titre de niveau 3 dans cet onglet : compter ces titres,
    // c'est compter les colonnes. Un locator ancré au panneau, plus de
    // `.first()`, plus de sous-chaîne : le bouton « Ajouter un contact » ne
    // peut plus tenir lieu de colonne « Contact ».
    const entetesDeColonne = crmPanel.getByRole('heading', { level: 3 });
    await expect(entetesDeColonne).toHaveCount(COLONNES_DU_PIPELINE.length, { timeout: 10000 });
    await expect(entetesDeColonne).toHaveText([...COLONNES_DU_PIPELINE]);
  });

  test('US-301.HP : le bouton "Ajouter un contact" est visible et cliquable', async ({ page }) => {
    const crmPanel = page.getByTestId('crm-panel');
    await expect(crmPanel).toBeVisible({ timeout: 15000 });

    const addBtn = crmPanel.getByRole('button', { name: /ajouter un contact/i });
    await expect(addBtn).toBeVisible();
    await addBtn.click();

    // Verifier qu'un formulaire ou modale de creation apparait
    const formulaire = page.getByRole('dialog', { name: 'Nouveau contact CRM' });
    await expect(formulaire).toBeVisible({ timeout: 5000 });
  });

  test('US-301.HP : le bouton "Import .vcf" est visible', async ({ page }) => {
    const crmPanel = page.getByTestId('crm-panel');
    await expect(crmPanel).toBeVisible({ timeout: 15000 });

    const importVcfBtn = crmPanel.getByText(/import.*\.vcf/i);
    await expect(importVcfBtn.first()).toBeVisible();
  });

  test('US-300.HP : le formulaire nouveau contact CRM contient les champs essentiels', async ({
    page,
  }) => {
    const crmPanel = page.getByTestId('crm-panel');
    await expect(crmPanel).toBeVisible({ timeout: 15000 });

    // Ouvrir le formulaire
    await crmPanel.getByRole('button', { name: /ajouter un contact/i }).click();

    const formulaire = page.getByRole('dialog', { name: 'Nouveau contact CRM' });
    await expect(formulaire).toBeVisible({ timeout: 5000 });

    // Les champs essentiels sont interrogés par leur ÉTIQUETTE réelle, accents
    // compris (« Prénom », pas « Prenom ») : l'ancien test comptait des textes
    // sans accent, ne trouvait rien, et disait « 0 attendu >= 1 ». Interroger
    // le champ plutôt que le texte prouve en plus que l'étiquette est reliée à
    // sa saisie.
    for (const champ of ['Prénom *', 'Nom', 'Entreprise', 'Email']) {
      await expect(formulaire.getByLabel(champ, { exact: true })).toBeVisible();
    }
  });

  test('US-300.HP : parcours complet CRM (ouvrir -> voir pipeline -> ajouter contact -> fermer)', async ({
    page,
  }) => {
    // 1. Panel visible
    const crmPanel = page.getByTestId('crm-panel');
    await expect(crmPanel).toBeVisible({ timeout: 15000 });

    // 2. Pipeline present avec sa premiere colonne
    await expect(crmPanel.getByRole('heading', { level: 3, name: 'Contact' })).toBeVisible();

    // 3. Ouvrir formulaire ajout
    await crmPanel.getByRole('button', { name: /ajouter un contact/i }).click();
    const formulaire = page.getByRole('dialog', { name: 'Nouveau contact CRM' });
    await expect(formulaire).toBeVisible({ timeout: 5000 });

    // 4. Fermer le formulaire par son bouton Annuler
    await formulaire.getByRole('button', { name: 'Annuler', exact: true }).click();
    await expect(formulaire).not.toBeVisible({ timeout: 5000 });

    // 5. Verifier que le panel CRM est toujours visible apres fermeture
    await expect(crmPanel).toBeVisible();
  });

  // B-262 (ex-constat RE34-C1), corrigé le 03/09/2026 : `CreateContactModal`
  // (CRMPanel.tsx) se déclarait `role="dialog" aria-modal="true"` sans jamais
  // appeler `pushEscapeHandler` (lib/escapeStack.ts) ; la cascade de la coque
  // ne le voyait donc pas et retombait sur le retour de vue, éjectant le
  // panneau CRM entier. C'était très exactement le « KO 1.1/1.2 » que la pile
  // d'Échap a été écrite pour empêcher : « Échap tombait sur le retour de vue
  // (goBack) et ÉJECTAIT la vue entière sous le modal ». Le `fixme` est levé :
  // l'application ferme désormais son formulaire d'abord.
  test(
    'US-300.HP : Echap ferme le formulaire de contact sans ejecter le panneau CRM (B-262)',
    async ({ page }) => {
      const crmPanel = page.getByTestId('crm-panel');
      await crmPanel.getByRole('button', { name: /ajouter un contact/i }).click();

      const formulaire = page.getByRole('dialog', { name: 'Nouveau contact CRM' });
      await expect(formulaire).toBeVisible({ timeout: 5000 });

      await page.keyboard.press('Escape');

      await expect(formulaire).not.toBeVisible({ timeout: 5000 });
      await expect(crmPanel).toBeVisible();
    },
  );
});
