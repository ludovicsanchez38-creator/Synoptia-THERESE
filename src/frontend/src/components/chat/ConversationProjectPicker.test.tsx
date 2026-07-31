/**
 * 0.43 - Rendre le cloisonnement documentaire visible et réglable.
 *
 * Le backend sait désormais cloisonner : une conversation rattachée à un projet
 * ne consulte plus que les documents de ce projet et les documents globaux.
 *
 * Mais une cloison invisible serait pire que pas de cloison du tout :
 * l'utilisateur verrait le contexte changer sans comprendre pourquoi, et
 * `project_id` resterait nul faute de moyen de le renseigner — une colonne
 * morte, exactement le défaut que ce chantier corrige.
 */
import { render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import { ConversationProjectPicker } from './ConversationProjectPicker';

const apiMocks = vi.hoisted(() => ({
  listProjects: vi.fn(),
  setConversationProject: vi.fn(),
}));

vi.mock('../../services/api', () => apiMocks);

describe('ConversationProjectPicker', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    apiMocks.listProjects.mockResolvedValue([
      { id: 'projet-a', name: 'Client Alpha' },
      { id: 'projet-b', name: 'Client Beta' },
    ]);
    apiMocks.setConversationProject.mockImplementation(
      async (_id: string, projectId: string | null) => ({ project_id: projectId })
    );
  });

  it('annonce que la conversation consulte toute la mémoire quand elle est libre', async () => {
    render(<ConversationProjectPicker conversationId="conv-1" projectId={null} />);

    await waitFor(() => {
      expect(screen.getByRole('combobox')).toBeTruthy();
    });
    expect(screen.getByRole('combobox')).toHaveAccessibleName(/documents consultés/i);
    expect((screen.getByRole('combobox') as HTMLSelectElement).value).toBe('');
  });

  it('affiche le projet auquel la conversation est rattachée', async () => {
    render(<ConversationProjectPicker conversationId="conv-1" projectId="projet-b" />);

    await waitFor(() => {
      expect((screen.getByRole('combobox') as HTMLSelectElement).value).toBe('projet-b');
    });
  });

  it('rattache la conversation au projet choisi', async () => {
    const surChangement = vi.fn();
    render(
      <ConversationProjectPicker
        conversationId="conv-1"
        projectId={null}
        onProjectChange={surChangement}
      />
    );

    await waitFor(() => expect(screen.getByRole('combobox')).toBeTruthy());
    const select = screen.getByRole('combobox') as HTMLSelectElement;

    const { fireEvent } = await import('@testing-library/react');
    fireEvent.change(select, { target: { value: 'projet-a' } });

    await waitFor(() => {
      expect(apiMocks.setConversationProject).toHaveBeenCalledWith('conv-1', 'projet-a');
    });
    await waitFor(() => expect(surChangement).toHaveBeenCalledWith('projet-a'));
  });

  it('détache la conversation quand on revient à toute la mémoire', async () => {
    render(<ConversationProjectPicker conversationId="conv-1" projectId="projet-a" />);

    await waitFor(() => expect(screen.getByRole('combobox')).toBeTruthy());
    const { fireEvent } = await import('@testing-library/react');
    fireEvent.change(screen.getByRole('combobox'), { target: { value: '' } });

    await waitFor(() => {
      expect(apiMocks.setConversationProject).toHaveBeenCalledWith('conv-1', null);
    });
  });

  it('ne casse rien si la liste des projets est indisponible', async () => {
    // Le backend peut être injoignable : le sélecteur ne doit pas faire tomber
    // l'en-tête du chat avec lui.
    apiMocks.listProjects.mockRejectedValue(new Error('backend injoignable'));

    render(<ConversationProjectPicker conversationId="conv-1" projectId={null} />);

    await waitFor(() => {
      expect(screen.getByRole('combobox')).toBeTruthy();
    });
  });
});
