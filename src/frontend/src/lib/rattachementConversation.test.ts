/**
 * D6 : le rattachement doit marcher AVANT le premier message.
 *
 * C'est le moment où l'on en a besoin : on vient d'indexer un dossier, on
 * ouvre une conversation, on veut y travailler. Jusqu'ici le geste répondait
 * 404 et se défaisait en silence.
 */
import { beforeEach, describe, expect, it, vi } from 'vitest';

const api = vi.hoisted(() => ({
  createConversation: vi.fn(),
  setConversationProject: vi.fn(),
}));
vi.mock('../services/api', () => api);

import {
  ConversationEphemereError,
  assurerConversationPersistee,
  rattacherAUnProjet,
} from './rattachementConversation';
import { useChatStore } from '../stores/chatStore';

function poserConversation(partiel: Record<string, unknown>) {
  useChatStore.setState({
    conversations: [
      {
        id: 'conv-locale',
        title: 'Nouvelle conversation',
        messages: [],
        createdAt: Date.now(),
        updatedAt: Date.now(),
        synced: false,
        ...partiel,
      },
    ] as never,
    currentConversationId: 'conv-locale',
  });
}

describe('Rattacher un projet avant le premier message', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    api.createConversation.mockResolvedValue({ id: 'conv-serveur', title: 'Nouvelle conversation' });
    api.setConversationProject.mockResolvedValue({ project_id: 'projet-a', memory_scope: 'project' });
  });

  it('persiste la conversation puis la rattache', async () => {
    poserConversation({});

    const identifiant = await rattacherAUnProjet('conv-locale', 'projet-a', 'project');

    expect(api.createConversation).toHaveBeenCalledWith('Nouvelle conversation');
    expect(identifiant).toBe('conv-serveur');
    // Le rattachement porte sur l'identifiant que le serveur connaît.
    expect(api.setConversationProject).toHaveBeenCalledWith('conv-serveur', 'projet-a', 'project');
    // Et le store suit, sinon le message suivant repartirait sur l'ancien id.
    expect(useChatStore.getState().conversations[0].id).toBe('conv-serveur');
    expect(useChatStore.getState().conversations[0].synced).toBe(true);
  });

  it('ne crée rien quand la conversation est déjà enregistrée', async () => {
    poserConversation({ synced: true });

    const identifiant = await rattacherAUnProjet('conv-locale', 'projet-a', 'project');

    expect(api.createConversation).not.toHaveBeenCalled();
    expect(identifiant).toBe('conv-locale');
  });

  it('ne crée rien pour un simple retour aux documents généraux', async () => {
    poserConversation({});

    await rattacherAUnProjet('conv-locale', null, 'global');

    expect(api.createConversation).not.toHaveBeenCalled();
    expect(api.setConversationProject).toHaveBeenCalledWith('conv-locale', null, 'global');
  });

  it('refuse de persister une conversation éphémère, et le dit', async () => {
    poserConversation({ ephemeral: true });

    await expect(rattacherAUnProjet('conv-locale', 'projet-a', 'project')).rejects.toBeInstanceOf(
      ConversationEphemereError
    );
    expect(api.createConversation).not.toHaveBeenCalled();
    expect(api.setConversationProject).not.toHaveBeenCalled();
  });

  it('laisse passer une conversation que le store ne connaît pas', async () => {
    useChatStore.setState({ conversations: [], currentConversationId: null });

    const identifiant = await assurerConversationPersistee('conv-inconnue');

    expect(identifiant).toBe('conv-inconnue');
    expect(api.createConversation).not.toHaveBeenCalled();
  });
});
