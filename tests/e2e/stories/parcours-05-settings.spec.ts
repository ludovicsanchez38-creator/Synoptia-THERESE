/**
 * Parcours 05 - Settings
 *
 * Scenario : ouvrir les reglages -> verifier les rubriques offertes
 *            -> naviguer entre elles -> sauvegarder -> fermer
 *
 * User Stories : US-600 a US-625
 *
 * Révisé le 02/09/2026. Les tests attendaient huit onglets dont « Outils »,
 * « Agents » et « Avancé » : ces trois-là sont `contributeurOnly`
 * (SettingsModal.tsx, `ALL_TABS`) et le mode par défaut est `standard`
 * (`DEFAULT_UX_MODE`, personalisationStore.ts). En mode standard la modale
 * n'offre que six rubriques, et une septième — « Accessibilité » — que les
 * tests ignoraient entièrement. Les six tests concernés cliquaient donc sur
 * des boutons absents et expiraient au bout de trente secondes.
 *
 * Les rubriques réservées ne sont pas retirées de ce parcours pour autant :
 * elles sont atteintes par le chemin réel, l'interrupteur « Mode
 * Contributeur » de la barre latérale des réglages.
 */

import { test, expect } from '@playwright/test';

import { ouvrirLApplication, ouvrirLaSurface } from './helpers/surfaces';

/** Les rubriques offertes d'emblée, en mode standard. */
const ONGLETS_STANDARD = [
  { id: 'profile', label: 'Profil' },
  { id: 'ai', label: 'IA' },
  { id: 'services', label: 'Services' },
  { id: 'accessibility', label: 'Accessibilité' },
  { id: 'privacy', label: 'Confidentialité' },
  { id: 'about', label: 'À propos' },
] as const;

/** Les rubriques que le mode contributeur ajoute. */
const ONGLETS_CONTRIBUTEUR = [
  { id: 'tools', label: 'Outils' },
  { id: 'agents', label: 'Agents' },
  { id: 'advanced', label: 'Avancé' },
] as const;

/**
 * Passer en mode contributeur par l'interrupteur de la modale.
 *
 * La case elle-même est `sr-only` sous un décor : on clique son étiquette,
 * comme le fait un utilisateur. On attend ensuite un ÉTAT (la case cochée et
 * une rubriques réservée montée), jamais un délai.
 */
async function passerEnModeContributeur(page: import('@playwright/test').Page) {
  const modale = page.getByTestId('settings-modal');
  await modale.getByText('Mode Contributeur').click();
  await expect(page.getByTestId('ux-mode-toggle')).toBeChecked();
  await expect(page.getByTestId('settings-tab-advanced')).toBeVisible({ timeout: 5000 });
}

/** Cliquer une rubrique et prouver que le contenu affiché est bien le sien. */
async function ouvrirLOnglet(page: import('@playwright/test').Page, id: string) {
  const onglet = page.getByTestId(`settings-tab-${id}`);
  await onglet.click();
  // Le contenu était vérifié par des expressions du genre `getByText(/outil/i)`
  // sur la page entière : elles passaient sur n'importe quelle rubrique. Le
  // contrat réel de la modale, c'est que l'onglet devienne sélectionné et que
  // le panneau porte SON étiquette.
  await expect(onglet).toHaveAttribute('aria-selected', 'true');
  await expect(page.getByRole('tabpanel')).toHaveAttribute('aria-labelledby', `settings-tab-${id}`);
}

test.describe('Parcours 05 - Settings', () => {
  test.beforeEach(async ({ page, request }) => {
    await ouvrirLApplication(page, request);

    // `settings-btn` vivait dans l'en-tête de chat, que la coque
    // conversationnelle ne monte plus. Les réglages s'ouvrent par leur action
    // de registre, celle-là même que sert la palette de commandes.
    await ouvrirLaSurface(page, 'settings.open');

    await expect(page.getByTestId('settings-modal')).toBeVisible({ timeout: 8000 });
  });

  test('US-600.HP : en mode standard la modale offre ses six rubriques, et seulement elles', async ({
    page,
  }) => {
    const modale = page.getByTestId('settings-modal');

    for (const onglet of ONGLETS_STANDARD) {
      await expect(page.getByTestId(`settings-tab-${onglet.id}`)).toBeVisible();
    }
    for (const onglet of ONGLETS_CONTRIBUTEUR) {
      await expect(page.getByTestId(`settings-tab-${onglet.id}`)).toHaveCount(0);
    }

    // Le compte ferme la porte : une rubrique ajoutée sans être déclarée ici
    // ferait rougir ce test plutôt que de passer inaperçue.
    await expect(modale.getByRole('tab')).toHaveCount(ONGLETS_STANDARD.length);
  });

  test('US-600.HP : le mode contributeur ajoute les trois rubriques reservees', async ({ page }) => {
    const modale = page.getByTestId('settings-modal');

    await passerEnModeContributeur(page);

    for (const onglet of [...ONGLETS_STANDARD, ...ONGLETS_CONTRIBUTEUR]) {
      await expect(page.getByTestId(`settings-tab-${onglet.id}`)).toBeVisible();
    }
    await expect(modale.getByRole('tab')).toHaveCount(
      ONGLETS_STANDARD.length + ONGLETS_CONTRIBUTEUR.length,
    );
  });

  test("US-601.HP : l'onglet Profil est le premier onglet visible", async ({ page }) => {
    const profileTab = page.getByTestId('settings-tab-profile');
    await expect(profileTab).toBeVisible();
    await expect(profileTab).toHaveAttribute('aria-selected', 'true');
  });

  test("US-602.HP : cliquer sur l'onglet IA affiche le contenu IA", async ({ page }) => {
    await ouvrirLOnglet(page, 'ai');
  });

  test("US-603.HP : cliquer sur l'onglet Services affiche le contenu Services", async ({ page }) => {
    await ouvrirLOnglet(page, 'services');
  });

  test("US-604.HP : cliquer sur l'onglet Outils affiche le contenu Outils", async ({ page }) => {
    await passerEnModeContributeur(page);
    await ouvrirLOnglet(page, 'tools');
  });

  test("US-605.HP : cliquer sur l'onglet Agents affiche le contenu Agents", async ({ page }) => {
    await passerEnModeContributeur(page);
    await ouvrirLOnglet(page, 'agents');
  });

  test("US-606.HP : cliquer sur l'onglet Confidentialite affiche les options RGPD", async ({
    page,
  }) => {
    await ouvrirLOnglet(page, 'privacy');
  });

  test("US-607.HP : cliquer sur l'onglet Avance affiche les parametres avances", async ({ page }) => {
    await passerEnModeContributeur(page);
    await ouvrirLOnglet(page, 'advanced');
  });

  test("US-608.HP : cliquer sur l'onglet A propos affiche les infos de version", async ({ page }) => {
    await ouvrirLOnglet(page, 'about');
  });

  test('US-609.HP : cliquer sur l\'onglet Accessibilite affiche ses reglages', async ({ page }) => {
    // Rubrique absente de l'ancienne liste, donc jamais éprouvée jusqu'ici.
    await ouvrirLOnglet(page, 'accessibility');
  });

  test('US-610.HP : navigation entre toutes les rubriques successivement', async ({ page }) => {
    await passerEnModeContributeur(page);

    for (const onglet of [...ONGLETS_STANDARD, ...ONGLETS_CONTRIBUTEUR]) {
      await ouvrirLOnglet(page, onglet.id);
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

  test('US-600.HP : parcours complet settings (ouvrir -> naviguer -> sauvegarder -> fermer)', async ({
    page,
  }) => {
    await passerEnModeContributeur(page);

    // Naviguer dans chaque rubrique
    for (const onglet of [...ONGLETS_STANDARD, ...ONGLETS_CONTRIBUTEUR]) {
      await ouvrirLOnglet(page, onglet.id);
    }

    // Revenir au profil
    await ouvrirLOnglet(page, 'profile');

    // Sauvegarder. Le bouton reste DÉSACTIVÉ tant que le nom complet est vide
    // (`disabled={profileSaving || !profileForm.name.trim()}`) : sur la base
    // jetable des E2E, vierge, l'ancien test cliquait donc trente secondes sur
    // un bouton inerte. On renseigne le champ obligatoire, puis on vérifie que
    // l'enregistrement a bien eu lieu plutôt que le seul fait d'avoir cliqué.
    const modale = page.getByTestId('settings-modal');
    await modale.getByLabel('Nom complet *').fill('Recette E2E');

    const sauvegarder = page.getByTestId('settings-save-btn');
    await expect(sauvegarder).toBeEnabled();
    await sauvegarder.click();
    await expect(modale.getByText('Profil enregistré')).toBeVisible({ timeout: 10000 });

    // Fermer
    await page.getByTestId('settings-close-btn').click();
    await expect(page.getByTestId('settings-modal')).not.toBeVisible({ timeout: 5000 });
  });
});
