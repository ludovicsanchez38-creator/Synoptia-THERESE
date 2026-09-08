import { describe, it, expect, beforeEach } from 'vitest';
import { insertResultInChat } from './actionsStore';
import { useChatStore } from './chatStore';
import { useNavigationStore } from './navigationStore';
import { useStatusStore } from './statusStore';
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
    useNavigationStore.setState({ activeView: 'crm', history: [] });
    useChatStore.setState({ conversations: [], currentConversationId: null });
  });

  it('insère le résultat dans le chat SANS déplacer la vue, et propose « Voir » (B-409 / B-534)', () => {
    useStatusStore.setState({ notifications: [] });
    insertResultInChat(completedTask('task-bug107-insert'));

    const conv = useChatStore.getState().currentConversation();
    expect(conv?.messages.at(-1)?.content).toContain('Brief de rendez-vous');
    // Un événement que l'utilisateur n'a pas déclenché à cet instant ne change pas sa vue.
    expect(useNavigationStore.getState().activeView).toBe('crm');
    const notif = useStatusStore.getState().notifications.at(-1);
    expect(notif?.action?.label).toBe('Voir');
    notif?.action?.onClick();
    expect(useNavigationStore.getState().activeView).toBe('chat');
  });

  it('« Voir » ouvre la conversation du résultat concerné, pas la dernière créée (revue COCO 0.68.0)', () => {
    useStatusStore.setState({ notifications: [] });
    insertResultInChat(completedTask('task-coco-voir-a'));
    const idA = useChatStore.getState().currentConversationId;
    insertResultInChat({
      ...completedTask('task-coco-voir-b'),
      agent_name: 'Relance clients',
      result: 'Trois relances préparées.',
    });
    const idB = useChatStore.getState().currentConversationId;
    expect(idA).not.toBe(idB);
    const notifA = useStatusStore
      .getState()
      .notifications.find((n) => n.title?.startsWith('Préparation RDV'));
    expect(notifA?.action?.label).toBe('Voir');
    notifA?.action?.onClick();
    expect(useChatStore.getState().currentConversationId).toBe(idA);
    expect(useNavigationStore.getState().activeView).toBe('chat');
  });

  it('déjà sur le chat : aucune notification, le résultat est simplement visible', () => {
    useStatusStore.setState({ notifications: [] });
    useNavigationStore.setState({ activeView: 'chat', history: [] });
    insertResultInChat(completedTask('task-bug107-chat'));
    expect(useStatusStore.getState().notifications).toHaveLength(0);
  });
});
