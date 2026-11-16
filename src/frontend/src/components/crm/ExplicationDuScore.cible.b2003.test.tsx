import { render, screen } from '@testing-library/react';
import { compile } from 'tailwindcss';
import { expect, it, vi } from 'vitest';
import { ExplicationDuScore } from './ExplicationDuScore';

vi.mock('../../services/api/crm-extended', () => ({ listActivities: vi.fn() }));

function pixels(dimension: string): number {
  // jsdom simplifie calc(0.25rem * 6), sans convertir les rem en pixels.
  const valeur = dimension.replace(/^calc\((.*)\)$/, '$1');
  if (valeur.endsWith('rem')) return Number.parseFloat(valeur) * 16;
  if (valeur.endsWith('px')) return Number.parseFloat(valeur);
  throw new Error(`Dimension non mesurable : ${dimension}`);
}

it('B-2003 : la cible de l’aide respecte les 36 px des boutons Contacts', async () => {
  // Règle DA lot 4, § 0 point 4 : boutons de 36 px, hors puces de filtre.
  // Le vrai compilateur Tailwind applique les classes du DOM rendu. Le pas
  // standard est inliné, car jsdom ne résout pas les variables CSS de thème.
  const feuille = document.createElement('style');
  const compilateur = await compile('@theme inline { --spacing: 0.25rem; } @tailwind utilities;');
  render(<ExplicationDuScore />);
  const bouton = screen.getByRole('button', { name: 'Expliquer le score' });
  feuille.textContent = compilateur.build([...bouton.classList].filter((classe) => /^(?:h|w|size|min-h|min-w)-/.test(classe)));
  document.head.appendChild(feuille);
  try {
    const style = getComputedStyle(bouton);
    expect(pixels(style.height), 'hauteur de la cible en pixels').toBeGreaterThanOrEqual(36);
    expect(pixels(style.width), 'largeur de la cible en pixels').toBeGreaterThanOrEqual(36);
  } finally {
    feuille.remove();
  }
});
