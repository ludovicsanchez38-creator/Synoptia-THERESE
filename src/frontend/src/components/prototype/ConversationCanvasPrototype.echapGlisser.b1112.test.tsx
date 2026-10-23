import { act, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, expect, it, vi } from 'vitest';
import { useChatStore } from '../../stores/chatStore';
import { useNavigationStore } from '../../stores/navigationStore';
import { usePanelStore } from '../../stores/panelStore';
import { usePersonalisationStore } from '../../stores/personalisationStore';
import { useTaskStore } from '../../stores/taskStore';
import { CLIENT_ACTION_EVENT } from '../../lib/clientActions';
import { _clearEscapeHandlers } from '../../lib/escapeStack';
import { ConversationCanvasPrototype } from './ConversationCanvasPrototype';
import type { Task } from '../../services/api';

const donnees = vi.hoisted(() => ({ titre: 'Relancer le couvreur', updateTask: vi.fn() }));
vi.mock('../../services/api', async (original) => ({
  ...await original<object>(),
  listTasks: vi.fn(async () => [{ id: 't1', title: donnees.titre, status: 'todo', priority: 'medium', tags: [] }]),
  getTaskStats: vi.fn(async () => ({ total: 1, todo: 1, in_progress: 0, done: 0 })),
  updateTask: donnees.updateTask,
}));

beforeEach(() => {
  window.history.replaceState({}, '', '/?interface=conversation-canvas');
  useChatStore.setState({ conversations: [], currentConversationId: null, isStreaming: false });
  useNavigationStore.setState(useNavigationStore.getInitialState());
  usePanelStore.setState(usePanelStore.getInitialState());
  usePersonalisationStore.setState({ skipDashboard: false });
  useTaskStore.setState({ ...useTaskStore.getInitialState(), viewMode: 'kanban', tasks: [
    { id: 't1', title: donnees.titre, status: 'todo', priority: 'medium', tags: [] } as Task,
  ] });
  _clearEscapeHandlers();
  vi.clearAllMocks();
});

it.each(['clavier', 'pointeur'])('B-1112 : la vraie coque consomme une annulation au %s, puis reprend Échap', async (mode) => {
  // jsdom ne fournit pas PointerEvent ; garder les coordonnées et isPrimary.
  class Pointeur extends MouseEvent {
    pointerId = 1;
    isPrimary = true;
  }
  vi.stubGlobal('PointerEvent', Pointeur);
  try {
    render(<ConversationCanvasPrototype />);
    await act(async () => { window.dispatchEvent(new CustomEvent(CLIENT_ACTION_EVENT, { detail: { actionId: 'tasks.open' } })); });
    const poignee = await screen.findByRole('button', { name: `Déplacer ${donnees.titre}` }, { timeout: 5000 });
    act(() => poignee.focus());
    if (mode === 'clavier') {
      fireEvent.keyDown(poignee, { key: ' ', code: 'Space' });
    } else {
      fireEvent.pointerDown(poignee, { button: 0, clientX: 10, clientY: 10 });
      fireEvent.pointerMove(document, { clientX: 40, clientY: 40 });
    }
    await waitFor(() => expect(poignee).toHaveAttribute('aria-pressed', 'true'));
    await act(async () => { await new Promise((resolve) => setTimeout(resolve, 10)); });
    fireEvent.keyDown(document, { key: 'Escape', code: 'Escape' });
    expect(screen.getByTestId('conversation-canvas-prototype')).toHaveAttribute('data-embedded-view', 'tasks');
    await waitFor(() => expect(poignee).not.toHaveAttribute('aria-pressed', 'true'));
    expect(await screen.findByText(`Déplacement annulé : ${donnees.titre} retrouve sa place.`)).toBeInTheDocument();
    expect(donnees.updateTask).not.toHaveBeenCalled();
    fireEvent.keyDown(document, { key: 'Escape', code: 'Escape' });
    await waitFor(() => expect(screen.getByTestId('conversation-canvas-prototype')).toHaveAttribute('data-embedded-view', 'accueil'));
  } finally {
    vi.unstubAllGlobals();
  }
});
