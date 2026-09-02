/**
 * B-230 - un interrupteur sans nom ne s'annonce pas.
 *
 * Paramètres > Avancé > Comportement au lancement : le bouton
 * `role="switch"` déclarait bien son état (`aria-checked`) mais aucune source
 * de nom - ni `aria-label`, ni `aria-labelledby`, ni `id` repris par un
 * `<label>`, et pour tout contenu un `<span>` décoratif. Le libellé visible
 * « Ouvrir sur le chat directement » vivait dans un `<p>` voisin, et un `<p>`
 * n'étiquette pas, même adjacent : un lecteur d'écran annonçait « case à
 * cocher, non coché », sans dire de quoi.
 *
 * L'asymétrie était interne aux Paramètres : `ServicesTab` porte un
 * `aria-label`, `AccessibilityTab` un `id` que reprend son `<label>`.
 *
 * Deux mesures ici, parce qu'aucune ne suffit seule : le rendu réel de
 * l'onglet (le défaut signalé), et un balayage des sources de tous les
 * interrupteurs des Paramètres - une liste d'écrans se périme au premier
 * réglage ajouté, et c'est exactement ainsi que la dérive revient.
 */
import { fireEvent, render, screen } from '@testing-library/react';
import { readFileSync, readdirSync } from 'node:fs';
import path from 'node:path';
import { describe, expect, it } from 'vitest';

import { AdvancedTab } from './AdvancedTab';

function ouvrirComportementAuLancement() {
  render(
    <AdvancedTab stats={null} workingDir={null} onSelectWorkingDir={() => {}} />,
  );
  // La rubrique n'est pas dépliée par défaut : sans ce clic, le test
  // échouerait faute d'interrupteur, pas faute de nom.
  fireEvent.click(screen.getByRole('button', { name: 'Comportement au lancement' }));
}

describe('B-230 - tout interrupteur de l’onglet Avancé porte un nom', () => {
  it('« Ouvrir sur le chat directement » est joignable par son nom', () => {
    ouvrirComportementAuLancement();

    expect(
      screen.getByRole('switch', { name: /Ouvrir sur le chat directement/i }),
    ).toBeInTheDocument();
  });

  it('aucun interrupteur affiché n’a un nom accessible vide', () => {
    ouvrirComportementAuLancement();

    // `name: /\S/` délègue le calcul du nom accessible à testing-library.
    const nommes = screen.queryAllByRole('switch', { name: /\S/ });
    const anonymes = screen
      .getAllByRole('switch')
      .filter((element) => !nommes.includes(element));
    expect(anonymes).toHaveLength(0);
  });
});

/** Le bloc `<button …>` qui porte la ligne `role="switch"` donnée. */
function baliseDuBouton(lignes: string[], indexDuRole: number): string {
  let debut = indexDuRole;
  while (debut > 0 && indexDuRole - debut < 20 && !/<button/.test(lignes[debut])) debut -= 1;
  let fin = indexDuRole;
  while (fin < lignes.length - 1 && fin - indexDuRole < 20 && !/^\s*>\s*$/.test(lignes[fin])) {
    fin += 1;
  }
  return lignes.slice(debut, fin + 1).join('\n');
}

function fichiersDesParametres(): string[] {
  const dossier = __dirname;
  return readdirSync(dossier)
    .filter((entree) => entree.endsWith('.tsx') && !entree.includes('.test.'))
    .map((entree) => path.join(dossier, entree));
}

describe('B-230 - la règle vaut pour tous les interrupteurs des Paramètres', () => {
  it('aucun role="switch" sans source de nom', () => {
    const anonymes: string[] = [];
    for (const fichier of fichiersDesParametres()) {
      const lignes = readFileSync(fichier, 'utf8').split('\n');
      lignes.forEach((ligne, i) => {
        if (!ligne.includes('role="switch"')) return;
        const balise = baliseDuBouton(lignes, i);
        if (!/aria-label=|aria-labelledby=|\sid=/.test(balise)) {
          anonymes.push(`${path.basename(fichier)}:${i + 1}`);
        }
      });
    }
    expect(anonymes).toEqual([]);
  });

  it('témoin : la règle voit bien des interrupteurs (sinon elle ne prouve rien)', () => {
    const total = fichiersDesParametres().reduce(
      (compte, fichier) =>
        compte + (readFileSync(fichier, 'utf8').match(/role="switch"/g) ?? []).length,
      0,
    );
    expect(total).toBeGreaterThan(5);
  });
});
