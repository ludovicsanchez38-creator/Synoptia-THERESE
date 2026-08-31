/**
 * Revue 30/08 : une recherche échouée ne doit pas réétiqueter
 * les anciens résultats avec la nouvelle requête.
 */
import { fireEvent, render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { PromptLibrary } from './PromptLibrary';

const getPromptLibrary = vi.fn();
const searchPromptLibrary = vi.fn();

vi.mock('../../services/api', async () => {
  const actual = await vi.importActual<typeof import('../../services/api')>('../../services/api');
  return {
    ...actual,
    getPromptLibrary: (...args: unknown[]) => getPromptLibrary(...args),
    searchPromptLibrary: (...args: unknown[]) => searchPromptLibrary(...args),
  };
});

const categorieRelance = {
  category: 'email',
  label: 'Email',
  prompts: [{
    id: 'p1',
    title: 'Relance facture',
    category: 'email',
    description: 'Relancer un paiement',
    prompt: 'Rédige une relance',
    tags: ['relance'],
  }],
};

describe('PromptLibrary — recherche honnête', () => {
  beforeEach(() => {
    getPromptLibrary.mockResolvedValue({ total: 1, categories: [categorieRelance] });
    searchPromptLibrary.mockReset();
  });

  it('une seconde recherche en échec n’affiche plus les résultats de la première sous le nouveau libellé', async () => {
    searchPromptLibrary
      .mockResolvedValueOnce({ query: 'relance', total: 1, categories: [categorieRelance] })
      .mockRejectedValueOnce(new Error('down'));

    render(<PromptLibrary onSelectPrompt={() => {}} onClose={() => {}} />);
    await screen.findByText('Relance facture');

    fireEvent.change(screen.getByLabelText('Rechercher un prompt'), {
      target: { value: 'relance' },
    });
    expect(await screen.findByText(/1 résultat pour "relance"/)).toBeInTheDocument();

    fireEvent.change(screen.getByLabelText('Rechercher un prompt'), {
      target: { value: 'contrat' },
    });
    expect(await screen.findByRole('alert')).toHaveTextContent(/Recherche impossible/i);
    expect(screen.queryByText(/pour "contrat"/)).toBeNull();
    expect(screen.queryByText('Relance facture')).toBeNull();
  });
});
