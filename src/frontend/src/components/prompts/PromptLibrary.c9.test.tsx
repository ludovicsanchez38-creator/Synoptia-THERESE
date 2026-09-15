/**
 * B-775 (cycle 9) : deux recherches rapprochées pouvaient se croiser. Le minuteur
 * était annulé à chaque frappe, mais la requête déjà partie n'était ni annulée ni
 * numérotée : la réponse la plus lente gagnait et s'affichait sous le nouveau libellé.
 */
import { act, fireEvent, render, screen } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { PromptLibrary } from './PromptLibrary';

const getPromptLibrary = vi.fn();
const searchPromptLibrary = vi.fn();
vi.mock('../../services/api', async () => {
  const actual = await vi.importActual<typeof import('../../services/api')>('../../services/api');
  return { ...actual, getPromptLibrary: (...a: unknown[]) => getPromptLibrary(...a), searchPromptLibrary: (...a: unknown[]) => searchPromptLibrary(...a) };
});

const categorie = (id: string, title: string) => ({
  category: 'email', label: 'Email',
  prompts: [{ id, title, category: 'email', description: 'd', prompt: 'p', tags: [] }],
});

describe('PromptLibrary - B-775, seule la dernière recherche alimente les résultats', () => {
  beforeEach(() => {
    vi.useFakeTimers({ shouldAdvanceTime: true });
    getPromptLibrary.mockResolvedValue({ total: 0, categories: [] });
    searchPromptLibrary.mockReset();
  });
  afterEach(() => vi.useRealTimers());

  it('une réponse tardive de la première recherche n’écrase pas la seconde', async () => {
    let resoudreRelance!: (v: unknown) => void;
    let resoudreContrat!: (v: unknown) => void;
    searchPromptLibrary
      .mockImplementationOnce(() => new Promise((r) => { resoudreRelance = r; }))
      .mockImplementationOnce(() => new Promise((r) => { resoudreContrat = r; }));

    render(<PromptLibrary onSelectPrompt={() => {}} onClose={() => {}} />);
    const champ = screen.getByLabelText('Rechercher un prompt');

    fireEvent.change(champ, { target: { value: 'relance' } });
    await act(async () => { await vi.advanceTimersByTimeAsync(350); });
    fireEvent.change(champ, { target: { value: 'contrat' } });
    await act(async () => { await vi.advanceTimersByTimeAsync(350); });
    expect(searchPromptLibrary).toHaveBeenCalledTimes(2);

    await act(async () => { resoudreContrat({ query: 'contrat', total: 1, categories: [categorie('p2', 'Contrat cadre')] }); });
    expect(await screen.findByText('Contrat cadre')).toBeInTheDocument();

    await act(async () => { resoudreRelance({ query: 'relance', total: 1, categories: [categorie('p1', 'Relance facture')] }); });
    expect(screen.queryByText('Relance facture')).toBeNull();
    expect(screen.getByText('Contrat cadre')).toBeInTheDocument();
    expect(screen.getByText(/pour "contrat"/)).toBeInTheDocument();
  });
});
