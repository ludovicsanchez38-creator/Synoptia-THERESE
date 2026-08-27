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
import { useChatStore } from '../../stores/chatStore';

const apiMocks = vi.hoisted(() => ({
  listProjects: vi.fn(),
  setConversationProject: vi.fn(),
  createConversation: vi.fn(),
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
      async (_id: string, projectId: string | null, memoryScope: string) => ({
        project_id: projectId,
        memory_scope: memoryScope,
      })
    );
  });

  it('annonce des documents généraux quand rien n’est rattaché', async () => {
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
      expect(apiMocks.setConversationProject).toHaveBeenCalledWith(
        'conv-1', 'projet-a', 'project'
      );
    });
    await waitFor(() =>
      // Troisième argument (D6) : l'identifiant que le serveur connaît.
      expect(surChangement).toHaveBeenCalledWith('projet-a', 'project', 'conv-1')
    );
  });

  it('revient aux documents généraux — le défaut de moindre privilège', async () => {
    render(<ConversationProjectPicker conversationId="conv-1" projectId="projet-a" />);

    await waitFor(() => expect(screen.getByRole('combobox')).toBeTruthy());
    const { fireEvent } = await import('@testing-library/react');
    fireEvent.change(screen.getByRole('combobox'), { target: { value: '' } });

    await waitFor(() => {
      expect(apiMocks.setConversationProject).toHaveBeenCalledWith(
        'conv-1', null, 'global'
      );
    });
  });

  it('permet le mode transversal explicite « tous les projets »', async () => {
    // Le moindre privilège ne doit pas supprimer l'usage transversal : il le
    // rend explicite. Sans cette option, un utilisateur qui compare deux
    // dossiers n'aurait plus aucun moyen de le faire.
    render(<ConversationProjectPicker conversationId="conv-1" projectId={null} />);

    await waitFor(() => expect(screen.getByRole('combobox')).toBeTruthy());
    const select = screen.getByRole('combobox') as HTMLSelectElement;
    const transversal = [...select.options].find(
      (o) => o.textContent === 'Tous les projets'
    );
    expect(transversal).toBeTruthy();

    const { fireEvent } = await import('@testing-library/react');
    fireEvent.change(select, { target: { value: transversal!.value } });

    await waitFor(() => {
      expect(apiMocks.setConversationProject).toHaveBeenCalledWith(
        'conv-1', null, 'all'
      );
    });
  });

  it('affiche le mode transversal quand il est déjà actif', async () => {
    render(
      <ConversationProjectPicker
        conversationId="conv-1"
        projectId={null}
        memoryScope="all"
      />
    );

    await waitFor(() => {
      const select = screen.getByRole('combobox') as HTMLSelectElement;
      expect(select.selectedOptions[0]?.textContent).toBe('Tous les projets');
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

// ---------------------------------------------------------------------------
// D6 (Dr_logic, 27/08) — le rattachement qui se défait tout seul.
//
// Une conversation neuve n'existe pas en base tant que le premier message n'a
// pas été envoyé : son identifiant est local. Choisir un projet avant cela
// répond 404, et le composant remettait la sélection précédente SANS RIEN
// DIRE. L'utilisateur voit son choix revenir à « Documents généraux » et
// n'apprend jamais que ses documents de projet restent hors de portée.
//
// Le rétablissement est juste — laisser une sélection que le serveur n'a pas
// enregistrée ferait croire à un cloisonnement inexistant. C'est le silence
// qui ne l'est pas.
// ---------------------------------------------------------------------------

const statusMocks = vi.hoisted(() => ({ addNotification: vi.fn() }));
vi.mock('../../stores/statusStore', () => ({
  useStatusStore: { getState: () => ({ addNotification: statusMocks.addNotification }) },
}));

describe('D6 : un rattachement qui échoue le dit', () => {
  beforeEach(() => {
    statusMocks.addNotification.mockClear();
    // Le rejet posé par le test précédent survivrait sinon à ce describe.
    apiMocks.setConversationProject.mockReset();
    apiMocks.setConversationProject.mockResolvedValue({
      project_id: 'projet-a',
      memory_scope: 'project',
    });
    apiMocks.listProjects.mockResolvedValue([
      { id: 'projet-a', name: 'Client Alpha' },
      { id: 'projet-b', name: 'Client Beta' },
    ]);
  });

  it('prévient quand le serveur refuse le rattachement', async () => {
    apiMocks.setConversationProject.mockRejectedValue(new Error('404'));
    const { container } = render(
      <ConversationProjectPicker conversationId="conv-locale" projectId={null} />
    );
    await waitFor(() => expect(apiMocks.listProjects).toHaveBeenCalled());

    const select = container.querySelector('select') as HTMLSelectElement;
    select.value = 'projet-a';
    select.dispatchEvent(new Event('change', { bubbles: true }));

    await waitFor(() => {
      expect(statusMocks.addNotification).toHaveBeenCalled();
    });
    const arg = statusMocks.addNotification.mock.calls[0][0];
    expect(arg.type).toBe('warning');
    // Le message doit dire ce qui est en jeu : les documents du projet.
    expect(`${arg.title} ${arg.message}`.toLowerCase()).toMatch(/document|projet/);
  });

  it('ne prévient de rien quand le rattachement réussit', async () => {
    const { container } = render(
      <ConversationProjectPicker conversationId="conv-1" projectId={null} />
    );
    await waitFor(() => expect(apiMocks.listProjects).toHaveBeenCalled());

    const select = container.querySelector('select') as HTMLSelectElement;
    select.value = 'projet-a';
    select.dispatchEvent(new Event('change', { bubbles: true }));

    await waitFor(() => expect(apiMocks.setConversationProject).toHaveBeenCalled());
    expect(statusMocks.addNotification).not.toHaveBeenCalled();
  });
});


// ---------------------------------------------------------------------------
// D6 : rattacher avant le premier message.
//
// C'est le moment où l'on en a besoin : on vient d'indexer un dossier, on
// ouvre une conversation, on veut y travailler. La conversation n'existe alors
// qu'en local, et le rattachement répondait 404.
// ---------------------------------------------------------------------------

describe('D6 : le rattachement marche avant le premier message', () => {
  beforeEach(() => {
    statusMocks.addNotification.mockClear();
    apiMocks.createConversation.mockReset();
    apiMocks.createConversation.mockResolvedValue({
      id: 'conv-serveur',
      title: 'Nouvelle conversation',
    });
    apiMocks.setConversationProject.mockReset();
    apiMocks.setConversationProject.mockResolvedValue({
      project_id: 'projet-a',
      memory_scope: 'project',
    });
    apiMocks.listProjects.mockResolvedValue([
      { id: 'projet-a', name: 'Client Alpha' },
      { id: 'projet-b', name: 'Client Beta' },
    ]);
    useChatStore.setState({
      conversations: [
        {
          id: 'conv-locale',
          title: 'Nouvelle conversation',
          messages: [],
          createdAt: Date.now(),
          updatedAt: Date.now(),
          synced: false,
        },
      ] as never,
      currentConversationId: 'conv-locale',
    });
  });

  it('persiste la conversation au lieu d’échouer, et la sélection tient', async () => {
    const { container } = render(
      <ConversationProjectPicker conversationId="conv-locale" projectId={null} />
    );
    await waitFor(() => expect(apiMocks.listProjects).toHaveBeenCalled());

    const select = container.querySelector('select') as HTMLSelectElement;
    select.value = 'projet-a';
    select.dispatchEvent(new Event('change', { bubbles: true }));

    await waitFor(() => {
      expect(apiMocks.setConversationProject).toHaveBeenCalledWith(
        'conv-serveur',
        'projet-a',
        'project'
      );
    });
    // Le choix reste affiché : c'est tout l'enjeu, il se défaisait avant.
    await waitFor(() => expect(select.value).toBe('projet-a'));
    expect(statusMocks.addNotification).not.toHaveBeenCalled();
  });

  it('refuse une conversation éphémère en expliquant pourquoi', async () => {
    useChatStore.setState({
      conversations: [
        {
          id: 'conv-ephemere',
          title: 'Conversation éphémère',
          messages: [],
          createdAt: Date.now(),
          updatedAt: Date.now(),
          synced: false,
          ephemeral: true,
        },
      ] as never,
      currentConversationId: 'conv-ephemere',
    });

    const { container } = render(
      <ConversationProjectPicker conversationId="conv-ephemere" projectId={null} />
    );
    await waitFor(() => expect(apiMocks.listProjects).toHaveBeenCalled());

    const select = container.querySelector('select') as HTMLSelectElement;
    select.value = 'projet-a';
    select.dispatchEvent(new Event('change', { bubbles: true }));

    await waitFor(() => expect(statusMocks.addNotification).toHaveBeenCalled());
    const arg = statusMocks.addNotification.mock.calls[0][0];
    expect(`${arg.title} ${arg.message}`.toLowerCase()).toContain('éphémère');
    expect(apiMocks.createConversation).not.toHaveBeenCalled();
  });
});


// Relevé par la relecture adversariale : après la persistance, l'identifiant
// de la conversation change. Prévenir le parent avec l'ANCIEN identifiant
// laissait le store sur `projectId: null` alors que le serveur, lui, était
// rattaché. L'affichage local masquait le mensonge jusqu'à ce qu'on revienne
// sur la conversation — et un affichage qui ment sur la cloison est
// exactement ce que ce composant existe pour empêcher.
describe('D6 : le parent est prévenu avec l’identifiant que le serveur connaît', () => {
  beforeEach(() => {
    statusMocks.addNotification.mockClear();
    apiMocks.createConversation.mockReset();
    apiMocks.createConversation.mockResolvedValue({
      id: 'conv-serveur',
      title: 'Nouvelle conversation',
    });
    apiMocks.setConversationProject.mockReset();
    apiMocks.setConversationProject.mockResolvedValue({
      project_id: 'projet-a',
      memory_scope: 'project',
    });
    apiMocks.listProjects.mockResolvedValue([{ id: 'projet-a', name: 'Client Alpha' }]);
    useChatStore.setState({
      conversations: [
        {
          id: 'conv-locale',
          title: 'Nouvelle conversation',
          messages: [],
          createdAt: Date.now(),
          updatedAt: Date.now(),
          synced: false,
        },
      ] as never,
      currentConversationId: 'conv-locale',
    });
  });

  it('annonce le nouvel identifiant après persistance', async () => {
    const onProjectChange = vi.fn();
    const { container } = render(
      <ConversationProjectPicker
        conversationId="conv-locale"
        projectId={null}
        onProjectChange={onProjectChange}
      />
    );
    await waitFor(() => expect(apiMocks.listProjects).toHaveBeenCalled());

    const select = container.querySelector('select') as HTMLSelectElement;
    select.value = 'projet-a';
    select.dispatchEvent(new Event('change', { bubbles: true }));

    await waitFor(() => expect(onProjectChange).toHaveBeenCalled());
    expect(onProjectChange).toHaveBeenCalledWith('projet-a', 'project', 'conv-serveur');
  });

  it('annonce l’identifiant inchangé quand rien n’a été persisté', async () => {
    useChatStore.setState({
      conversations: [
        {
          id: 'conv-1',
          title: 'Déjà enregistrée',
          messages: [],
          createdAt: Date.now(),
          updatedAt: Date.now(),
          synced: true,
        },
      ] as never,
      currentConversationId: 'conv-1',
    });
    const onProjectChange = vi.fn();
    const { container } = render(
      <ConversationProjectPicker
        conversationId="conv-1"
        projectId={null}
        onProjectChange={onProjectChange}
      />
    );
    await waitFor(() => expect(apiMocks.listProjects).toHaveBeenCalled());

    const select = container.querySelector('select') as HTMLSelectElement;
    select.value = 'projet-a';
    select.dispatchEvent(new Event('change', { bubbles: true }));

    await waitFor(() => expect(onProjectChange).toHaveBeenCalled());
    expect(onProjectChange).toHaveBeenCalledWith('projet-a', 'project', 'conv-1');
  });
});
