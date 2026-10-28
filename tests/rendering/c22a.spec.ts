import { test, expect } from '@playwright/test';

test('le guide utilise le chemin du bundle dans un vrai navigateur', async ({ page }) => {
  await page.addInitScript(() => {
    (window as any).appelsPdf = [];
    (window as any).__TAURI_INTERNALS__ = { invoke: async (commande: string, args: unknown) => {
      (window as any).appelsPdf.push({ commande, args });
      if (commande === 'plugin:path|resolve_directory') return '/bundle/resources/guide-therese-0.82.pdf';
      return undefined;
    } };
  });
  await page.goto('/tests/recette-c22a.html');
  await page.getByRole('button', { name: 'Aide', exact: true }).click();
  await expect(page.getByRole('dialog', { name: 'Aide' })).toBeVisible();
  await page.getByRole('button', { name: 'Ouvrir le guide (PDF)' }).click();
  await expect.poll(() => page.evaluate(() => (window as any).appelsPdf.some((a: any) =>
    a.commande === 'plugin:opener|open_path' && a.args.path === '/bundle/resources/guide-therese-0.82.pdf'))).toBe(true);
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
