/**
 * B-762 (cycle 9) : un champ de type « file » n'avait aucun rendu. Le libellé
 * s'affichait seul, la valeur restait indéfinie, « Générer » ne s'activait
 * jamais : analyze-xlsx et analyze-pdf étaient injouables depuis le formulaire.
 */
import { fireEvent, render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { open } from '@tauri-apps/plugin-dialog';

vi.mock('@tauri-apps/plugin-dialog', () => ({ open: vi.fn() }));

import { DynamicSkillForm } from './DynamicSkillForm';

const schema = {
  file_path: { type: 'file' as const, label: 'Fichier à analyser', required: true, help_text: 'Un classeur .xlsx' },
};

describe('DynamicSkillForm - B-762, un champ fichier se remplit et débloque Générer', () => {
  beforeEach(() => vi.clearAllMocks());

  it('rend un champ de chemin et active Générer une fois rempli', () => {
    const onSubmit = vi.fn();
    render(<DynamicSkillForm skillName="Analyser un Excel" schema={schema} onSubmit={onSubmit} onBack={vi.fn()} />);

    const champ = screen.getByLabelText(/Fichier à analyser/);
    expect(screen.getByRole('button', { name: 'Générer' })).toBeDisabled();

    fireEvent.change(champ, { target: { value: '/Users/ludo/Documents/ventes.xlsx' } });
    expect(screen.getByRole('button', { name: 'Générer' })).toBeEnabled();

    fireEvent.click(screen.getByRole('button', { name: 'Générer' }));
    expect(onSubmit).toHaveBeenCalledWith({ file_path: '/Users/ludo/Documents/ventes.xlsx' });
  });

  it('« Parcourir » remplit le chemin depuis le sélecteur natif', async () => {
    vi.mocked(open).mockResolvedValue('/Users/ludo/Documents/bilan.pdf');
    render(<DynamicSkillForm skillName="Analyser un PDF" schema={schema} onSubmit={vi.fn()} onBack={vi.fn()} />);

    fireEvent.click(screen.getByRole('button', { name: /Parcourir/ }));
    expect(await screen.findByDisplayValue('/Users/ludo/Documents/bilan.pdf')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Générer' })).toBeEnabled();
  });
});
