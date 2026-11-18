import { render, screen } from '@testing-library/react';
import { compile } from 'tailwindcss';
import { expect, it, vi } from 'vitest';
import { useAccessibilityRoot } from '../../hooks/useAccessibilityRoot';
import { useAccessibilityStore, useFontSize } from '../../stores/accessibilityStore';
import { ExplicationDuScore } from './ExplicationDuScore';

vi.mock('../../services/api/crm-extended', () => ({ listActivities: vi.fn() }));

function pixels(dimension: string): number {
  // jsdom simplifie calc(0.25rem * 6), sans convertir les rem en pixels.
  const valeur = dimension.replace(/^calc\((.*)\)$/, '$1');
  if (valeur.endsWith('rem')) return Number.parseFloat(valeur) * Number.parseFloat(getComputedStyle(document.documentElement).fontSize);
  if (valeur.endsWith('px')) return Number.parseFloat(valeur);
  throw new Error(`Dimension non mesurable : ${dimension}`);
}

function AideAvecLaPreferenceDePolice() {
  useAccessibilityRoot(useFontSize(), false);
  return <ExplicationDuScore />;
}

it.each(['small', 'medium', 'large'] as const)('B-2003 : la cible de l’aide respecte les 36 px des boutons Contacts (%s)', async (taille) => {
  // Règle DA lot 4, § 0 point 4 : boutons de 36 px, hors puces de filtre.
  // Le vrai compilateur Tailwind applique les classes du DOM rendu. Le pas
  // standard est inliné, car jsdom ne résout pas les variables CSS de thème.
  const feuille = document.createElement('style');
  const compilateur = await compile('@theme inline { --spacing: 0.25rem; } @tailwind utilities;');
  const preference = useAccessibilityStore.getState().fontSize;
  useAccessibilityStore.setState({ fontSize: taille });
  const vue = render(<AideAvecLaPreferenceDePolice />);
  const bouton = screen.getByRole('button', { name: 'Expliquer le score' });
  feuille.textContent = compilateur.build([...bouton.classList].filter((classe) => /^(?:h|w|size|min-h|min-w)-/.test(classe)));
  document.head.appendChild(feuille);
  try {
    const style = getComputedStyle(bouton);
    expect(Math.max(pixels(style.height), pixels(style.minHeight || '0px')), 'hauteur de la cible en pixels').toBeGreaterThanOrEqual(36);
    expect(Math.max(pixels(style.width), pixels(style.minWidth || '0px')), 'largeur de la cible en pixels').toBeGreaterThanOrEqual(36);
  } finally {
    vue.unmount();
    useAccessibilityStore.setState({ fontSize: preference });
    feuille.remove();
  }
});
