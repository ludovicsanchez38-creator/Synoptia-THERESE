import { describe, it, expect, beforeEach } from 'vitest';
import { insertResultInChat } from './actionsStore';
import { useChatStore } from './chatStore';
import { useNavigationStore } from './navigationStore';
import type { TaskState } from '../services/api/actions';

/**
 * BUG-107 (Capov, 0.21.0) — volet « prep-RDV » : une action terminée annonçait
 * « Résultat inséré dans le chat » mais, lancée depuis l'Accueil, le résultat
 * partait dans une conversation invisible (la vue restait sur l'Accueil).
 */
const completedTask = (id: string): TaskState => ({
  task_id: id,
  agent_id: 'prep-rdv',
  agent_name: 'Préparation RDV',
  status: 'completed',
  params: {},
  steps: [],
  result: 'Brief de rendez-vous : préparer la réunion avec Sandrine Joly.',
  created_at: '',
  started_at: null,
  completed_at: null,
  error: null,
  progress: 1,
});

describe('actionsStore.insertResultInChat (BUG-107 / prep-RDV)', () => {
  beforeEach(() => {
    useNavigationStore.setState({ activeView: 'home', history: [] });
    useChatStore.setState({ conversations: [], currentConversationId: null });
  });

  it('insère le résultat dans le chat ET ramène la vue sur le chat', () => {
    insertResultInChat(completedTask('task-bug107-insert'));

    const conv = useChatStore.getState().currentConversation();
    expect(conv?.messages.at(-1)?.content).toContain('Brief de rendez-vous');
    expect(useNavigationStore.getState().activeView).toBe('chat');
  });
});
