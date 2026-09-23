/**
 * Parcours 10 - Les couches passent au-dessus de l'Agenda (B-1021, BUG-181).
 *
 * BUG-181 (Discord, Dr_logic-3D, v0.74.0) : le sélecteur « Mon calendrier »
 * restait visible au-dessus des Paramètres ouverts depuis l'Agenda. La ronde
 * B2 du cycle 11 en a trouvé la cause : son enveloppe portait la couche
 * réservée à l'onboarding (`z-[100]`), au-dessus des modales (`z-50`), de la
 * palette (`z-[80]`) et des toasts. Le point du sélecteur doit appartenir à
 * la surface ouverte par-dessus, pas au sélecteur.
 */
import { expect, test, type Page } from '@playwright/test';

import { ouvrirLApplication, ouvrirLaSurface } from './helpers/surfaces';

/**
 * Pixels de la zone du sélecteur. Le test de toucher ne suffit pas : sous une
 * modale, la colonne principale est `inert`, et `elementFromPoint` la traverse
 * même quand le sélecteur reste PEINT au-dessus. On compare donc ce qui est
 * dessiné, avant et pendant la surface ouverte.
 */
async function zoneDuSelecteur(page: Page) {
  const selecteur = page.getByRole('combobox', { name: 'Agenda affiché' });
  await expect(selecteur).toBeVisible({ timeout: 15000 });
  const boite = await selecteur.boundingBox();
  if (!boite) throw new Error('sélecteur sans boîte');
  // L'intérieur seul : le liseré extérieur peut rester visible en bord de modale.
  return { x: boite.x + 6, y: boite.y + 6, width: Math.max(4, boite.width - 12), height: Math.max(4, boite.height - 12) };
}

async function pixels(page: Page, zone: { x: number; y: number; width: number; height: number }) {
  await page.waitForTimeout(400);
  return page.screenshot({ clip: zone, animations: 'disabled' });
}

test.describe('Parcours 10 - Couches au-dessus de l’Agenda', () => {
  test.beforeEach(async ({ page, request }) => {
    await ouvrirLApplication(page, request);
    await ouvrirLaSurface(page, 'calendar.open');
  });

  test('les Paramètres ouverts depuis l’Agenda recouvrent le sélecteur (BUG-181)', async ({ page }) => {
    const zone = await zoneDuSelecteur(page);
    const avant = await pixels(page, zone);
    await page.getByRole('button', { name: 'Paramètres', exact: true }).first().click();
    await expect(page.getByRole('dialog').first()).toBeVisible({ timeout: 10000 });
    const pendant = await pixels(page, zone);
    expect(avant.equals(pendant), 'le sélecteur reste peint au-dessus des Paramètres').toBe(false);
  });

  test('la palette de commandes recouvre le sélecteur', async ({ page }) => {
    const zone = await zoneDuSelecteur(page);
    const avant = await pixels(page, zone);
    await page.keyboard.press('Control+k');
    await expect(page.getByRole('dialog').first()).toBeVisible({ timeout: 10000 });
    const pendant = await pixels(page, zone);
    expect(avant.equals(pendant), 'le sélecteur reste peint au-dessus de la palette').toBe(false);
  });
});
