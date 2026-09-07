/**
 * B-627 (persona Sophie, c4) : pendant la génération de la trame (3 min 20 s
 * avec un modèle local), la colonne affichait « Aucune section pour
 * l'instant. » et un bouton grisé. L'état vide mentait sur ce qui se passait.
 */
import { render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import { OutlineTree } from './OutlineTree';

function renderTrame(isLoading: boolean) {
  render(
    <OutlineTree
      sections={[]}
      activeSectionId={null}
      isLoading={isLoading}
      error={null}
      onSelect={vi.fn()}
      onReorder={vi.fn()}
      onCreateSection={vi.fn()}
      onGenerateOutline={vi.fn()}
    />
  );
}

describe('B-627 : la génération de la trame se voit', () => {
  it('pendant la génération, un état de travail nommé remplace l’état vide', () => {
    renderTrame(true);
    const statut = screen.getByRole('status');
    expect(statut).toHaveTextContent(/génération de la trame en cours/i);
    expect(statut).toHaveTextContent(/plusieurs minutes/i);
    expect(screen.queryByText(/Aucune section pour l’instant|Aucune section pour l'instant/)).toBeNull();
  });

  it('sans génération en cours, l’état vide propose de générer la trame', () => {
    renderTrame(false);
    expect(screen.getByText(/Aucune section pour l’instant|Aucune section pour l'instant/)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Générer la trame/ })).toBeEnabled();
    expect(screen.queryByRole('status')).toBeNull();
  });
});
