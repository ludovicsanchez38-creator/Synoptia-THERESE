/** B-1102 : les snapshots viennent de Chromium, sans serveur ni réseau. */
import test from 'node:test';
import assert from 'node:assert/strict';
import { chromium } from '@playwright/test';
import { lesInteractifs, choisirGestes } from './couverture-ecran.mjs';

export const NOMS = [
  'Ouvrir',
  'Supprimer : Facture',
  "Supprimer : Facture d'acompte",
  'Générer et ouvrir le PDF : Facture, FAC-2026-001, 01/10/2026, 1 055,00 €, Marie Dupont',
  'Supprimer : Facture, FAC-2026-001, 01/10/2026, 1 055,00 €, Marie Dupont',
  'Lire "le devis" : version 2',
  'Ouvrir le dossier \\ archives',
  'Fermer l’image',
];

export async function verifierNoms(noms = NOMS) {
  const navigateur = await chromium.launch({ executablePath: process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH });
  try {
    const page = await navigateur.newPage();
    await page.route('**/*', (route) => route.abort());
    await page.setContent('<main></main>');
    await page.evaluate((valeurs) => {
      for (const nom of valeurs) {
        const bouton = document.createElement('button');
        bouton.textContent = nom;
        document.querySelector('main').append(bouton);
      }
      const boutonImage = document.createElement('button');
      const image = document.createElement('img');
      image.alt = 'Fermer l’aperçu';
      boutonImage.append(image);
      document.querySelector('main').append(boutonImage);
    }, noms);
    const releve = await lesInteractifs(page);
    const attendus = [...noms, 'Fermer l’aperçu'];
    assert.deepEqual(releve.map((el) => el.nom), attendus);
    assert.deepEqual(choisirGestes(releve, new Set()).map((el) => el.nom), attendus);
    return releve.map(({ nom, signature }) => ({ nom, signature }));
  } finally {
    await navigateur.close();
  }
}

test('B-1102 : le relevé lit les vrais ariaSnapshot de Chromium', async () => {
  const releve = await verifierNoms();
  assert.ok(releve.some((el) => el.signature.startsWith("- '")), 'Chromium doit exercer le scalaire YAML cité');
  assert.ok(releve.some((el) => el.signature.includes("d''acompte")), 'apostrophe doublée par YAML');
});
