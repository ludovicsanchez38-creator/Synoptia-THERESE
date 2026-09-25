/**
 * B-1281 : la catégorie repliée d'un clic se rouvrait seule quand le clic
 * arrivait avant les effets du montage. `useEffect(() => setIsOpen(defaultOpen),
 * [defaultOpen])` tourne AUSSI au montage : si React ne l'a pas encore joué au
 * moment du clic, il passe après lui et rouvre la catégorie. Cause du test
 * sophie-02 instable sur la CI Linux (B-1142, trois fois).
 */
import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

import { PromptLibrary } from './PromptLibrary';

const getPromptLibrary = vi.fn();
vi.mock('../../services/api', async () => {
  const actual = await vi.importActual<typeof import('../../services/api')>('../../services/api');
  return { ...actual, getPromptLibrary: (...args: unknown[]) => getPromptLibrary(...args) };
});

const categorieEmail = {
  category: 'email',
  label: 'Email',
  prompts: [{ id: 'p1', title: 'Relance facture', category: 'email', description: 'Relancer', prompt: 'Rédige', tags: [] }],
};

function apresLeCommit(texte: string): Promise<void> {
  // Rappel en microtâche, juste après les mutations du DOM : avant la tâche
  // où React joue les effets passifs du montage.
  return new Promise((ok) => {
    const observateur = new MutationObserver(() => {
      if (document.body.textContent?.includes(texte)) {
        observateur.disconnect();
        ok();
      }
    });
    observateur.observe(document.body, { childList: true, subtree: true, characterData: true });
  });
}

describe('PromptLibrary — clic avant les effets du montage', () => {
  it('une catégorie repliée d’un clic reste repliée', async () => {
    let livrer!: (valeur: unknown) => void;
    getPromptLibrary.mockReturnValue(new Promise((ok) => { livrer = ok; }));
    render(<PromptLibrary onSelectPrompt={() => {}} onClose={() => {}} />);
    const affichee = apresLeCommit('Relance facture');
    livrer({ total: 1, categories: [categorieEmail] });
    await affichee;
    const categorie = screen.getByRole('button', { name: /Email/ });
    fireEvent.click(categorie);
    await new Promise((ok) => setTimeout(ok, 50));
    expect(categorie).toHaveAttribute('aria-expanded', 'false');
  });
});
