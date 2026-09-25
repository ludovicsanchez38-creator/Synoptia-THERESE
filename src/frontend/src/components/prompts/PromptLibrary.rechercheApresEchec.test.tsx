/**
 * B-1305 : quand la bibliothèque n'avait pas pu se charger, une recherche
 * réussie restait cachée derrière l'alerte « Bibliothèque indisponible »,
 * alors que l'en-tête annonçait ses résultats. Lecteur Y, passe 5.
 */
import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

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

const categorieEmail = {
  category: 'email',
  label: 'Email',
  prompts: [{ id: 'p1', title: 'Relance facture', category: 'email', description: 'Relancer', prompt: 'Rédige', tags: [] }],
};

describe('PromptLibrary — recherche après un chargement en échec', () => {
  it('montre les résultats de la recherche', async () => {
    getPromptLibrary.mockRejectedValue(new Error('Serveur injoignable'));
    searchPromptLibrary.mockResolvedValue({ query: 'relance', total: 1, categories: [categorieEmail] });
    render(<PromptLibrary onSelectPrompt={() => {}} onClose={() => {}} />);
    await screen.findByText('Bibliothèque indisponible');

    fireEvent.change(screen.getByLabelText('Rechercher un prompt'), { target: { value: 'relance' } });
    await screen.findByText(/1 résultat pour "relance"/, {}, { timeout: 3000 });
    expect(await screen.findByText('Relance facture')).toBeInTheDocument();
    expect(screen.queryByText('Bibliothèque indisponible')).not.toBeInTheDocument();
  }, 15_000);
});
