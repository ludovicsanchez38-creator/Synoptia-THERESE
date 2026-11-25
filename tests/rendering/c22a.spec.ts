import { test, expect } from '@playwright/test';

test('le guide 0.85 embarqué se lit sans appel à un lecteur externe', async ({ page }) => {
  await page.route(/^https?:\/\/(?!localhost:|127\.0\.0\.1:)/, route => route.abort());
  await page.goto('/tests/recette-c22a.html');
  await page.getByRole('button', { name: 'Aide', exact: true }).click();
  const aide = page.getByRole('dialog', { name: 'Aide' });
  await expect(aide).toBeVisible();
  await aide.getByRole('button', { name: 'Ouvrir le guide' }).click();
  const guide = aide.getByRole('article', { name: 'Guide des testeurs' });
  await expect(guide.getByRole('heading', { name: 'Guide des testeurs de THÉRÈSE 0.85' })).toBeVisible();
  const demarrage = guide.getByRole('img', { name: 'Écran de démarrage avec v0.85.0-beta' });
  await expect.poll(() => demarrage.evaluate((image: HTMLImageElement) => image.naturalWidth)).toBeGreaterThan(0);
});

for (const hauteur of [640, 800]) {
  test(`B-1344 : le dernier risque reste entièrement visible après animation (${hauteur}px)`, async ({ page }) => {
    await page.setViewportSize({ width: 1100, height: hauteur });
    await page.goto('/tests/recette-c22a.html?ecran=securite');
    const dernier = page.getByRole('button', { expanded: false }).last();
    await expect(dernier).toBeVisible();
    // Attendre l'animation d'entrée, puis aligner le risque replié au bord.
    await page.waitForTimeout(500);
    await dernier.evaluate((element) => element.scrollIntoView({ block: 'end' }));
    await dernier.click({ position: { x: 50, y: 25 } });
    await page.waitForTimeout(600);
    const debordement = await page.locator('[aria-expanded="true"]').evaluate((element) => {
      const cadre = document.querySelector('[data-testid="defilement"]')!.getBoundingClientRect();
      return element.getBoundingClientRect().bottom - cadre.bottom;
    });
    expect(debordement).toBeLessThanOrEqual(1);
  });
}
