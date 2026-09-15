/**
 * B-823 (cycle 9) : une carte de prompt se dépliait au clic seul sur une div,
 * inatteignable au clavier ; et l'accordéon se remontait à chaque frappe.
 */
import { fireEvent, render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { PromptLibrary } from './PromptLibrary';

const getPromptLibrary = vi.fn();
vi.mock('../../services/api', async () => {
  const actual = await vi.importActual<typeof import('../../services/api')>('../../services/api');
  return { ...actual, getPromptLibrary: (...a: unknown[]) => getPromptLibrary(...a), searchPromptLibrary: vi.fn() };
});

describe('PromptLibrary - B-823, carte dépliable au clavier', () => {
  beforeEach(() => {
    getPromptLibrary.mockResolvedValue({ total: 1, categories: [{ category: 'email', label: 'Email', prompts: [
      { id: 'p1', title: 'Relance facture', category: 'email', description: 'Relancer un paiement', prompt: 'Rédige une relance courtoise', tags: ['relance'] },
    ] }] });
  });

  it('le titre est un bouton avec aria-expanded, qui déplie le prompt', async () => {
    render(<PromptLibrary onSelectPrompt={() => {}} onClose={() => {}} />);
    const bascule = await screen.findByRole('button', { name: /Relance facture/ });
    expect(bascule).toHaveAttribute('aria-expanded', 'false');
    fireEvent.click(bascule);
    expect(bascule).toHaveAttribute('aria-expanded', 'true');
    expect(screen.getByText('Rédige une relance courtoise')).toBeInTheDocument();
  });
});
