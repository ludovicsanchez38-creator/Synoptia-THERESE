/**
 * B-1423 (tri de la couverture écran P-145, 25/09) : en mode Souverain, le
 * sélecteur de modèle de chaque conseiller s'annonçait par le code interne
 * du rôle (« Modèle du conseiller analyst »), et le nom du modèle choisi était
 * coupé dans la colonne étroite sans moyen de le lire en entier.
 */
import { render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

import { AdvisorArcLayout, type OllamaModelInfo } from './AdvisorArcLayout';

const MODELES: OllamaModelInfo[] = [{ name: 'gemma4-tia:latest', size: 9_600_000_000 }];

describe('B-1423 : les sélecteurs de modèle se lisent', () => {
  it('chaque sélecteur est nommé par le conseiller, jamais par son code', () => {
    render(<AdvisorArcLayout mode="sovereign" ollamaModels={MODELES} selectedModels={{}} onModelChange={vi.fn()} />);
    const noms = screen.getAllByRole('combobox').map((select) => select.getAttribute('aria-label'));
    expect(noms).toContain('Modèle du conseiller : L’Analyste'.replace('’', "'"));
    for (const nom of noms) {
      expect(nom).not.toMatch(/analyst|strategist|devil|pragmatic|visionary/);
    }
  });

  it('le nom complet du modèle choisi se lit au survol', () => {
    render(<AdvisorArcLayout mode="sovereign" ollamaModels={MODELES} selectedModels={{}} onModelChange={vi.fn()} />);
    for (const select of screen.getAllByRole('combobox')) {
      expect(select).toHaveAttribute('title', 'gemma4-tia:latest');
    }
  });
});
