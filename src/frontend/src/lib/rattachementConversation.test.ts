/**
 * D6 : le rattachement doit marcher AVANT le premier message.
 *
 * C'est le moment où l'on en a besoin : on vient d'indexer un dossier, on
 * ouvre une conversation, on veut y travailler. Jusqu'ici le geste répondait
 * 404 et se défaisait en silence.
 */
import { readFileSync } from 'node:fs';
import path from 'node:path';

import { beforeEach, describe, expect, it, vi } from 'vitest';

const api = vi.hoisted(() => ({
  createConversation: vi.fn(),
  setConversationProject: vi.fn(),
}));
vi.mock('../services/api', () => api);

import {
  ConversationEphemereError,
  assurerConversationPersistee,
  attendrePersistance,
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

describe('Le store retrouve la conversation après le changement d’identifiant', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    api.createConversation.mockResolvedValue({ id: 'conv-serveur', title: 'Nouvelle conversation' });
    api.setConversationProject.mockResolvedValue({ project_id: 'projet-a', memory_scope: 'project' });
  });

  // Relevé par la relecture : vérifier l'argument transmis ne prouve pas que
  // l'état final est juste. Ce test suit le parcours jusqu'au bout — c'est
  // l'écart entre le store et le serveur qui produisait l'affichage menteur.
  it('le projet se pose bien sur la conversation persistée', async () => {
    poserConversation({});

    const identifiant = await rattacherAUnProjet('conv-locale', 'projet-a', 'project');
    useChatStore.getState().setConversationProjectId(identifiant, 'projet-a', 'project');

    const conversations = useChatStore.getState().conversations;
    expect(conversations).toHaveLength(1);
    expect(conversations[0].id).toBe('conv-serveur');
    expect(conversations[0].projectId).toBe('projet-a');
    expect(conversations[0].memoryScope).toBe('project');
  });

  it('l’ancien identifiant ne retrouve plus rien — d’où l’affichage menteur', async () => {
    poserConversation({});

    await rattacherAUnProjet('conv-locale', 'projet-a', 'project');
    useChatStore.getState().setConversationProjectId('conv-locale', 'projet-a', 'project');

    // Personne ne correspond : le store resterait sans projet, en contradiction
    // avec le serveur. C'est exactement ce que le correctif évite.
    expect(useChatStore.getState().conversations[0].projectId).toBeUndefined();
  });
});

describe('Un envoi attend le rattachement en vol', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    api.setConversationProject.mockResolvedValue({ project_id: 'projet-a', memory_scope: 'project' });
  });

  // Relevé par la relecture : pendant le rattachement, le sélecteur est
  // désactivé mais PAS le composeur. Un envoi parti au même instant part sans
  // identifiant, le backend crée une SECONDE conversation, et l'utilisateur se
  // retrouve avec un doublon dont l'une porte son projet et l'autre son
  // message. L'envoi doit donc attendre que la persistance soit finie.
  it('attendrePersistance ne rend la main qu’une fois la conversation posée', async () => {
    poserConversation({});
    let liberer: (v: { id: string; title: string }) => void = () => undefined;
    api.createConversation.mockReturnValue(
      new Promise((resolve) => {
        liberer = resolve;
      })
    );

    const rattachement = rattacherAUnProjet('conv-locale', 'projet-a', 'project');
    let attenteFinie = false;
    const attente = attendrePersistance().then(() => {
      attenteFinie = true;
    });

    // Tant que la création n'a pas répondu, l'envoi patiente.
    await Promise.resolve();
    expect(attenteFinie).toBe(false);

    liberer({ id: 'conv-serveur', title: 'Nouvelle conversation' });
    await rattachement;
    await attente;

    expect(attenteFinie).toBe(true);
    expect(useChatStore.getState().conversations[0].id).toBe('conv-serveur');
  });

  it('rend la main aussitôt quand rien n’est en vol', async () => {
    poserConversation({ synced: true });
    await attendrePersistance();
  });

  it('ne reste pas bloqué si la persistance échoue', async () => {
    poserConversation({});
    api.createConversation.mockRejectedValue(new Error('réseau'));

    await expect(rattacherAUnProjet('conv-locale', 'projet-a', 'project')).rejects.toThrow();
    await attendrePersistance();
  });

  it('est réellement attendue avant un envoi', () => {
    const source = readFileSync(
      path.join(__dirname, '..', 'components', 'chat', 'ChatInput.tsx'),
      'utf8',
    );
    expect(source).toContain('attendrePersistance');
  });
});
