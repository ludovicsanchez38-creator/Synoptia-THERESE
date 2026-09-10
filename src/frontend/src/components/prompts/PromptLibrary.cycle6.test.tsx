/**
 * Cycle 6, persona Sophie (sophie-02, sophie-03) : la bibliothèque annonce des
 * résultats qu'elle n'affiche pas quand une catégorie a été repliée avant la
 * recherche, et la coche « copié » s'affiche même quand la copie a échoué.
 */
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
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

const categorieEmail = {
  category: 'email',
  label: 'Email',
  prompts: [{ id: 'p1', title: 'Relance facture', category: 'email', description: 'Relancer un paiement', prompt: 'Rédige une relance', tags: ['relance'] }],
};
const categorieVente = {
  category: 'vente',
  label: 'Vente',
  prompts: [{ id: 'p2', title: 'Pitch', category: 'vente', description: 'Un pitch', prompt: 'Rédige un pitch', tags: [] }],
};

describe('PromptLibrary — cycle 6', () => {
  beforeEach(() => {
    getPromptLibrary.mockResolvedValue({ total: 2, categories: [categorieEmail, categorieVente] });
    searchPromptLibrary.mockReset();
  });

  it('sophie-02 : une catégorie repliée avant la recherche s’ouvre avec ses résultats', async () => {
    searchPromptLibrary.mockResolvedValue({ query: 'relance', total: 1, categories: [categorieEmail] });
    render(<PromptLibrary onSelectPrompt={() => {}} onClose={() => {}} />);
    await screen.findByText('Relance facture');
    fireEvent.click(screen.getByRole('button', { name: /Email/ }));
    await waitFor(() => expect(screen.queryByText('Relance facture')).toBeNull());
    fireEvent.change(screen.getByLabelText('Rechercher un prompt'), { target: { value: 'relance' } });
    await screen.findByText(/1 résultat pour "relance"/);
    expect(await screen.findByText('Relance facture')).toBeInTheDocument();
  });

  it('sophie-03 : une copie refusée par le navigateur ne montre pas la coche « copié »', async () => {
    const writeText = vi.fn().mockRejectedValue(new DOMException('Write permission denied.', 'NotAllowedError'));
    Object.defineProperty(navigator, 'clipboard', { value: { writeText }, configurable: true });
    render(<PromptLibrary onSelectPrompt={() => {}} onClose={() => {}} />);
    await screen.findByText('Relance facture');
    const bouton = screen.getAllByTitle('Copier le prompt')[0];
    fireEvent.click(bouton);
    await waitFor(() => expect(writeText).toHaveBeenCalled());
    await waitFor(() => expect(bouton.getAttribute('data-copie')).toBe('echec'));
    expect(screen.getByRole('status')).toHaveTextContent(/copie impossible/i);
  });

  it('sophie-03 : une copie réussie garde sa coche', async () => {
    const writeText = vi.fn().mockResolvedValue(undefined);
    Object.defineProperty(navigator, 'clipboard', { value: { writeText }, configurable: true });
    render(<PromptLibrary onSelectPrompt={() => {}} onClose={() => {}} />);
    await screen.findByText('Relance facture');
    const bouton = screen.getAllByTitle('Copier le prompt')[0];
    fireEvent.click(bouton);
    await waitFor(() => expect(bouton.getAttribute('data-copie')).toBe('ok'));
  });
});
