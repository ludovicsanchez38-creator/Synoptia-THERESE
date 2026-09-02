/**
 * B-068 — une minuterie armée dans un composant doit mourir avec lui.
 *
 * La recherche est différée de 300 ms. Le minuteur n'était annulé qu'à la
 * frappe suivante : fermer le panneau entre-temps laissait l'échéance courir,
 * et `searchPromptLibrary()` partait pour un écran que plus personne ne
 * regarde. Le panneau se ferme à chaque retour au chat, donc le cas n'a rien
 * de théorique — c'est le seul des trois minuteurs du lot dont la conséquence
 * soit observable, les deux autres n'écrivant qu'un état sur un composant mort
 * (silencieux en React 19, mais fuite tout de même).
 */
import { fireEvent, render, screen } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

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

describe('PromptLibrary — la recherche différée meurt avec le panneau', () => {
  beforeEach(() => {
    getPromptLibrary.mockResolvedValue({ total: 1, categories: [categorieRelance] });
    searchPromptLibrary.mockReset();
    searchPromptLibrary.mockResolvedValue({ query: 'relance', total: 1, categories: [categorieRelance] });
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it('ne part pas après le démontage', async () => {
    const { unmount } = render(<PromptLibrary onSelectPrompt={() => {}} onClose={() => {}} />);
    await screen.findByText('Relance facture');

    vi.useFakeTimers();
    fireEvent.change(screen.getByLabelText('Rechercher un prompt'), {
      target: { value: 'relance' },
    });

    unmount();
    vi.advanceTimersByTime(300);
    await Promise.resolve();

    expect(searchPromptLibrary).not.toHaveBeenCalled();
  });

  it('part bien quand le panneau reste ouvert (sinon le test ne prouve rien)', async () => {
    render(<PromptLibrary onSelectPrompt={() => {}} onClose={() => {}} />);
    await screen.findByText('Relance facture');

    vi.useFakeTimers();
    fireEvent.change(screen.getByLabelText('Rechercher un prompt'), {
      target: { value: 'relance' },
    });

    vi.advanceTimersByTime(300);
    await Promise.resolve();

    expect(searchPromptLibrary).toHaveBeenCalledWith('relance');
  });
});
