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

import { authentifierAmorcageNavigateur, BACKEND_URL } from './helpers/backend';
import { json } from './helpers/garde-lecture-seule';
import { ouvrirLApplication, ouvrirLaSurface } from './helpers/surfaces';

/** Ouvrir le composeur de chat par l'action du registre. */
async function ouvrirLeChat(page: import('@playwright/test').Page) {
  await ouvrirLaSurface(page, 'chat.new');
  await expect(page.getByTestId('chat-message-input')).toBeVisible({ timeout: 10000 });
}

test('Mise en route avec Claude déjà disponible, sans import ni dossier', async ({ page }) => {
  await authentifierAmorcageNavigateur(page);
  await page.route(`${BACKEND_URL}/api/config/onboarding-complete`, (route) =>
    json(route, { completed: route.request().method() === 'POST' }),
  );
  await page.route(`${BACKEND_URL}/api/config/profile`, (route) =>
    json(route, route.request().method() === 'POST' ? route.request().postDataJSON() : null),
  );
  await page.route(`${BACKEND_URL}/api/config/`, (route) => json(route, {
    has_anthropic_key: true,
    corrupted_keys: [],
    api_keys_source: { anthropic: 'coffre' },
  }));
  await page.route(`${BACKEND_URL}/api/config/llm`, (route) => {
    if (route.request().method() !== 'POST') return route.continue();
    return json(route, { ...route.request().postDataJSON(), available: true });
  });
  await page.route(`${BACKEND_URL}/api/consents`, (route) => {
    if (route.request().method() !== 'POST') return route.continue();
    return json(route, route.request().postDataJSON());
  });
  await page.route(`${BACKEND_URL}/api/config/working-directory`, (route) =>
    json(route, { path: null, exists: false }),
  );

  await page.goto('/');
  const accueil = page.getByTestId('onboarding-step-0');
  await expect(accueil.getByText(/Préparer une relance pour un devis resté sans réponse/)).toBeVisible();
  await accueil.getByRole('button', { name: 'Commencer la configuration' }).click();

  const profil = page.getByTestId('onboarding-step-1');
  await expect(profil.getByText('Importer un profil existant', { exact: true })).toBeVisible();
  await expect(profil.getByRole('button', { name: 'Importer un profil (THÉRÈSE.md)' })).toBeHidden();
  await profil.getByRole('textbox', { name: /Nom complet/ }).fill('Camille Exemple');
  await profil.getByTestId('onboarding-next-btn').click();

  const ia = page.getByTestId('onboarding-step-2');
  await expect(ia.getByRole('status').filter({ hasText: 'Service d’IA configuré' })).toContainText(/Claude \(Anthropic\).*Claude Opus 5\.5/);
  const procédure = ia.locator('summary').filter({ hasText: 'Pour recevoir ta première réponse' });
  await expect(procédure).toBeVisible();
  await expect(procédure.locator('..')).toHaveJSProperty('open', false);
  await ia.getByTestId('onboarding-next-btn').click();

  const accord = page.getByTestId('onboarding-step-3');
  await expect(accord.getByRole('heading', { name: 'Exemple avec Claude' })).toBeVisible();
  await expect(accord.getByText(/THÉRÈSE adresse à Anthropic le mot « Bonjour »/)).toBeVisible();
  await accord.getByRole('checkbox').check();
  await accord.getByTestId('onboarding-next-btn').click();

  const dossier = page.getByTestId('onboarding-step-4');
  await expect(dossier.getByRole('button', { name: /^(Continuer|Passer)/ })).toHaveCount(1);
  await dossier.getByRole('button', { name: 'Continuer sans dossier', exact: true }).click();
  await page.getByTestId('onboarding-complete-btn').click();
  await expect(page.getByTestId('onboarding-wizard')).toBeHidden();
});

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
