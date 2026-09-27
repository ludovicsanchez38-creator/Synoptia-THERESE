/** B-1725 : chaque action répétée annonce et conserve le prompt qu'elle vise. */
import { fireEvent, render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

const getPromptLibrary = vi.fn();
vi.mock('../../services/api', async () => {
  const actual = await vi.importActual<typeof import('../../services/api')>('../../services/api');
  return { ...actual, getPromptLibrary: (...args: unknown[]) => getPromptLibrary(...args) };
});

import { PromptLibrary } from './PromptLibrary';

const prompts = [
  { id: 'relance-facture', title: 'Relance facture', category: 'email', description: 'Relancer un paiement', prompt: 'Rédige une relance', tags: [] },
  { id: 'suivi-prospect', title: 'Suivi prospect', category: 'email', description: 'Suivre un prospect', prompt: 'Rédige un suivi', tags: [] },
];

describe('B-1725 : actions de la bibliothèque contextualisées', () => {
  beforeEach(() => {
    getPromptLibrary.mockReset();
    getPromptLibrary.mockResolvedValue({ total: 2, categories: [{ category: 'email', label: 'Email', prompts }] });
  });

  it('nomme la copie et l’utilisation avec le titre et garde un ID métier stable', async () => {
    const onSelectPrompt = vi.fn();
    render(<PromptLibrary onSelectPrompt={onSelectPrompt} onClose={() => {}} />);
    await screen.findByText('Suivi prospect');

    for (const prompt of prompts) {
      expect(screen.getByRole('button', { name: `Copier le prompt ${prompt.title}` })).toHaveAttribute('data-id', prompt.id);
      expect(screen.getByRole('button', { name: `Utiliser ${prompt.title}` })).toHaveAttribute('data-id', prompt.id);
    }

    fireEvent.click(screen.getByRole('button', { name: 'Utiliser Suivi prospect' }));
    expect(onSelectPrompt).toHaveBeenCalledExactlyOnceWith('Rédige un suivi');
  });

  it('garde aussi l’identité du prompt quand sa carte est dépliée', async () => {
    render(<PromptLibrary onSelectPrompt={() => {}} onClose={() => {}} />);
    await screen.findByText('Relance facture');

    const deplier = screen.getByRole('button', { name: 'Relance facture Relancer un paiement' });
    expect(deplier).toHaveAttribute('data-id', 'relance-facture');
    fireEvent.click(deplier);
    expect(screen.getByRole('button', { name: 'Insérer Relance facture dans le chat' })).toHaveAttribute('data-id', 'relance-facture');
  });
});
