/**
 * B-1477 : dans « Travaux », la ligne d'une action guidée rouvre son
 * résultat, panneau Actions fermé depuis longtemps.
 */
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

const api = vi.hoisted(() => ({
  fetchActions: vi.fn().mockResolvedValue([]),
  runAction: vi.fn(),
  fetchTask: vi.fn(),
  fetchTasks: vi.fn().mockResolvedValue([]),
  cancelTask: vi.fn(),
}));
vi.mock('../../services/api/actions', async (importOriginal) => ({
  ...(await importOriginal<object>()),
  ...api,
}));

import { _clearEscapeHandlers } from '../../lib/escapeStack';
import { useActionsStore } from '../../stores/actionsStore';
import { useChatStore } from '../../stores/chatStore';
import { useProcessingTasksStore } from '../../stores/processingTasksStore';
import { ConversationCanvasPrototype } from './ConversationCanvasPrototype';
import { TraitementsPanel } from '../traitements/TraitementsPanel';

describe('B-1477 : la ligne d’une action guidée rouvre son résultat', () => {
  beforeEach(() => {
    window.history.replaceState({}, '', '/?interface=conversation-canvas');
    useChatStore.setState({ conversations: [], currentConversationId: null, isStreaming: false });
    useActionsStore.setState({ isPanelOpen: false, activeTask: null, selectedAgent: null, tasks: [], error: null });
    _clearEscapeHandlers();
    api.fetchTask.mockResolvedValue({
      task_id: 'tache-1', agent_id: 'audit-tresorerie', agent_name: 'Audit trésorerie', status: 'completed',
      params: {}, steps: [], result: 'Trésorerie saine.', created_at: null, started_at: null, completed_at: null,
      error: null, progress: 1,
    });
    useProcessingTasksStore.setState({
      traitements: [{
        id: 'tr-1', type: 'action', label: 'Audit trésorerie', state: 'done', step: null, progress: null,
        project_id: null, conversation_id: null, entity_id: 'tache-1', error: null, created_at: null,
        started_at: null, finished_at: null, can_cancel: false,
      }],
      erreur: null,
    } as never);
  });

  it('un clic sur la ligne ouvre le panneau Actions sur la tâche', async () => {
    render(<><ConversationCanvasPrototype /><TraitementsPanel /></>);
    fireEvent.click(screen.getByRole('button', { name: 'Ouvrir Audit trésorerie' }));
    await waitFor(() => expect(useActionsStore.getState().activeTask?.task_id).toBe('tache-1'));
    expect(useActionsStore.getState().isPanelOpen).toBe(true);
  });
});
