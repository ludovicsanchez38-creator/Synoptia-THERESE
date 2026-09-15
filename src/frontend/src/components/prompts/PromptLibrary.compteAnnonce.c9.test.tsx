/**
 * B-858 (cycle 9) : le nombre de résultats d'une recherche vivait dans un
 * paragraphe ordinaire, sans région dynamique : un lecteur d'écran n'entendait
 * jamais « 1 résultat pour "relance" » alors que l'attente, elle, est annoncée.
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
  prompts: [{ id: 'p1', title: 'Relance facture', category: 'email', description: 'Relancer un paiement', prompt: 'Rédige une relance', tags: ['relance'] }],
};

describe('PromptLibrary - B-858, le compte de résultats est annoncé', () => {
  beforeEach(() => {
    getPromptLibrary.mockResolvedValue({ total: 1, categories: [categorieRelance] });
    searchPromptLibrary.mockReset();
    searchPromptLibrary.mockResolvedValue({ query: 'relance', total: 1, categories: [categorieRelance] });
  });

  it('le compte vit dans une région polie', async () => {
    render(<PromptLibrary onSelectPrompt={() => {}} onClose={() => {}} />);
    await screen.findByText('Relance facture');

    fireEvent.change(screen.getByLabelText('Rechercher un prompt'), { target: { value: 'relance' } });
    const compte = await screen.findByText(/1 résultat pour "relance"/);
    expect(compte.closest('[aria-live="polite"]')).not.toBeNull();
  });
});
