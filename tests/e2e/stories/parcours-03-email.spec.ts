/**
 * Parcours 03 - Email
 *
 * Scénario : ouvrir la surface email -> sans compte, un état vide propose
 *            « Configurer un compte », qui ouvre l'assistant -> les options
 *            Gmail OAuth et SMTP mènent chacune à leur étape.
 *
 * B-1436 (25/09/2026, décision déléguée par Ludo) : l'assistant ne s'ouvre
 * plus d'office à l'arrivée sur la surface ; il s'ouvre au geste.
 *
 * User Stories : US-111, US-112, US-113
 *
 * Réécrit le 02/09/2026. Sept des huit tests faisaient `page.goto('/')` puis
 * attendaient quinze secondes l'assistant « Configuration Email » SANS jamais
 * ouvrir la surface email : cet assistant vit à l'intérieur du panneau
 * (`EmailPanel`), il ne s'affiche pas sur la coque d'accueil. Seul le premier
 * test ouvrait la surface, et lui seul passait. Les sélecteurs sont désormais
 * ancrés au dialogue de l'assistant plutôt qu'à la page entière : sur la coque,
 * « gmail », « smtp » ou « fermer » se trouvent à plusieurs endroits.
 */

import { test, expect } from '@playwright/test';

import { ouvrirLApplication, ouvrirLaSurface } from './helpers/surfaces';

/** L'assistant de configuration, tel que le panneau email le monte. */
function assistant(page: import('@playwright/test').Page) {
  return page.getByRole('dialog', { name: /configuration email/i });
}

/** B-1436 : l'assistant s'ouvre par « Configurer un compte ». */
async function ouvrirLAssistant(page: import('@playwright/test').Page) {
  await page.getByTestId('email-panel').getByRole('button', { name: 'Configurer un compte' }).click();
  await expect(assistant(page)).toBeVisible({ timeout: 15000 });
  return assistant(page);
}

test.describe('Parcours 03 - Email', () => {
  test.beforeEach(async ({ page, request }) => {
    // App.tsx interroge le backend, pas le stockage local : sur la base
    // jetable des E2E l'assistant de mise en route recouvrait chaque surface.
    await ouvrirLApplication(page, request);
    // `?panel=crm` et `?panel=email` ne sont plus reconnus : le lien profond
    // n'accepte que `board` et `atelier`. La surface s'ouvre par son action
    // de registre, qui ne depend d'aucun parametre d'URL.
    await ouvrirLaSurface(page, 'email.open');
    await expect(page.getByTestId('email-panel')).toBeVisible({ timeout: 15000 });
  });

  test("US-111.HP : la surface email s'ouvre par son action de registre", async ({ page }) => {
    await expect(page.getByTestId('email-panel')).toBeVisible();
  });

  test("US-112.HP : sans compte, l'état vide propose de configurer, et le geste ouvre l'assistant", async ({
    page,
  }) => {
    // La base jetable des E2E est vierge : aucun compte. B-1436 : l'assistant
    // ne s'ouvre plus seul ; l'état vide le propose.
    await expect(page.getByTestId('email-panel').getByText('Aucun compte email configuré')).toBeVisible({ timeout: 15000 });
    await expect(assistant(page)).toHaveCount(0);
    await ouvrirLAssistant(page);
  });

  test('US-112.HP : l\'assistant affiche le titre "Configuration Email"', async ({ page }) => {
    await ouvrirLAssistant(page);
    await expect(
      assistant(page).getByRole('heading', { name: 'Configuration Email' }),
    ).toBeVisible({ timeout: 15000 });
    await expect(assistant(page).getByText('Choix du mode de connexion')).toBeVisible();
    await expect(assistant(page).getByText(/Étape 1 sur 4/)).toHaveCount(0);
  });

  test("US-113.HP : l'assistant propose l'option Gmail OAuth", async ({ page }) => {
    await ouvrirLAssistant(page);
    await expect(assistant(page).getByRole('button', { name: /Gmail OAuth/ })).toBeVisible({
      timeout: 15000,
    });
  });

  test("US-113.HP : l'assistant propose l'option SMTP classique", async ({ page }) => {
    await ouvrirLAssistant(page);
    await expect(
      assistant(page).getByRole('button', { name: /SMTP \/ IMAP classique/ }),
    ).toBeVisible({ timeout: 15000 });
  });

  test("US-112.HP : l'assistant a un bouton de fermeture fonctionnel", async ({ page }) => {
    const dialogue = await ouvrirLAssistant(page);

    await dialogue.getByRole('button', { name: 'Fermer', exact: true }).click();

    await expect(dialogue).not.toBeVisible({ timeout: 5000 });
  });

  test("US-113.HP : selectionner Gmail mene a l'etape suivante de l'assistant", async ({ page }) => {
    const dialogue = await ouvrirLAssistant(page);
    await dialogue.getByRole('button', { name: /Gmail OAuth/ }).click();

    // Le parcours Gmail compte quatre étapes. Avec des identifiants repris du
    // serveur MCP Google Workspace il saute directement à la quatrième : les
    // deux sont des « étapes suivantes » valides, l'étape 1 ne l'est pas.
    await expect(dialogue.getByText(/Étape (2|4) sur 4/)).toBeVisible({ timeout: 5000 });
  });

  test("US-113.HP : selectionner SMTP mene a l'etape de configuration SMTP", async ({ page }) => {
    const dialogue = await ouvrirLAssistant(page);
    await dialogue.getByRole('button', { name: /SMTP \/ IMAP classique/ }).click();

    // Le parcours SMTP n'en compte que deux : le compteur le dit lui-même.
    await expect(dialogue.getByText('Étape 2 sur 2')).toBeVisible({ timeout: 5000 });
  });
});
