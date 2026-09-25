/**
 * B-1296 : une catégorie repliée dans les résultats restait repliée quand on
 * retapait la même recherche (même texte une fois nettoyé) : ni la clé de
 * l'accordéon, qui suivait le texte, ni son intention ne changeaient.
 * L'écran annonçait « 1 résultat » sans le montrer. Revue ciblée, passe 7.
 */
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
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

describe('PromptLibrary — recherche retapée', () => {
  it('rouvre la catégorie repliée dans les résultats', async () => {
    getPromptLibrary.mockResolvedValue({ total: 1, categories: [categorieEmail] });
    searchPromptLibrary.mockResolvedValue({ query: 'relance', total: 1, categories: [categorieEmail] });
    render(<PromptLibrary onSelectPrompt={() => {}} onClose={() => {}} />);
    await screen.findByText('Relance facture');
    const champ = screen.getByLabelText('Rechercher un prompt');

    fireEvent.change(champ, { target: { value: 'relance' } });
    await waitFor(() => expect(searchPromptLibrary).toHaveBeenCalledTimes(1), { timeout: 3000 });
    await screen.findByText(/1 résultat pour "relance"/, {}, { timeout: 3000 });
    fireEvent.click(screen.getByRole('button', { name: /Email/ }));
    await waitFor(() => expect(screen.getByRole('button', { name: /Email/ })).toHaveAttribute('aria-expanded', 'false'));

    fireEvent.change(champ, { target: { value: 'relance ' } });
    await waitFor(() => expect(searchPromptLibrary).toHaveBeenCalledTimes(2), { timeout: 3000 });
    await waitFor(
      () => expect(screen.getByRole('button', { name: /Email/ })).toHaveAttribute('aria-expanded', 'true'),
      { timeout: 3000 },
    );
    expect(screen.getByText('Relance facture')).toBeInTheDocument();
  }, 15_000);
});
