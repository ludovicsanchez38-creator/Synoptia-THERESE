/**
 * Revue Codex n°13 du cycle 11 (23/09/2026), tâches.
 *
 * B-988 (R-1) : « Rafraîchir les tâches » (ou un filtre) sur une liste vide
 * remplaçait le formulaire ouvert par le squelette de chargement : la tâche
 * en cours de saisie disparaissait sans question.
 *
 * B-989 (R-2) : « Nouvelle tâche » pendant la modification d'une tâche
 * passait en création sans question, avec les champs de la tâche ouverte.
 */
import { StrictMode } from 'react';
import { act, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import type { Task } from '../../services/api';
import { _clearEscapeHandlers } from '../../lib/escapeStack';
import { useTaskStore } from '../../stores/taskStore';

const { mockListTasks, mockUpdateTask, mockCreateTask } = vi.hoisted(() => ({
  mockListTasks: vi.fn(), mockUpdateTask: vi.fn(), mockCreateTask: vi.fn(),
}));

vi.mock('../../services/api', async () => {
  const actual = await vi.importActual<Record<string, unknown>>('../../services/api');
  return {
    ...actual,
    listTasks: (...args: unknown[]) => mockListTasks(...args),
    updateTask: (...args: unknown[]) => mockUpdateTask(...args),
    createTask: (...args: unknown[]) => mockCreateTask(...args),
    listProjects: vi.fn().mockResolvedValue([]),
    listContacts: vi.fn().mockResolvedValue([]),
  };
});

import { TasksPanel } from './TasksPanel';

const TACHE = {
  id: 'tache-1', title: 'Relancer Ruiz', description: 'Devis', status: 'todo', priority: 'high',
  due_date: null, project_id: null, contact_id: null, tags: [],
  created_at: '2026-09-01T08:00:00Z', updated_at: '2026-09-01T08:00:00Z',
} as unknown as Task;

function poser(taches: Task[], currentTaskId: string | null) {
  useTaskStore.setState({
    tasks: taches, searchQuery: '', currentTaskId, isTaskFormOpen: true, viewMode: 'list',
    filterStatus: null, filterPriority: null, filterProjectId: null,
  } as never);
}

const titre = () => screen.getByLabelText(/Titre/) as HTMLInputElement;

beforeEach(() => {
  vi.clearAllMocks();
  _clearEscapeHandlers();
});

describe('B-988 : un rafraîchissement ne démonte pas le formulaire', () => {
  it('liste vide, titre saisi, « Rafraîchir les tâches » : la saisie reste', async () => {
    let repondre: (v: Task[]) => void = () => {};
    mockListTasks.mockResolvedValueOnce([]);
    poser([], null);
    render(<TasksPanel isOpen onClose={() => {}} standalone />);
    await waitFor(() => expect(titre()).toBeInTheDocument());
    fireEvent.change(titre(), { target: { value: 'Rappeler le garage' } });

    mockListTasks.mockImplementationOnce(() => new Promise<Task[]>((r) => { repondre = r; }));
    await act(async () => { fireEvent.click(screen.getByRole('button', { name: 'Rafraîchir les tâches' })); });
    expect(titre()).toHaveValue('Rappeler le garage');
    await act(async () => { repondre([]); });
    expect(titre()).toHaveValue('Rappeler le garage');
  });
});

describe('B-989 : « Nouvelle tâche » pendant une modification', () => {
  beforeEach(() => { mockListTasks.mockResolvedValue([TACHE]); });

  it('tâche intacte : le formulaire repart vierge', async () => {
    poser([TACHE], 'tache-1');
    render(<TasksPanel isOpen onClose={() => {}} standalone />);
    await waitFor(() => expect(titre()).toHaveValue('Relancer Ruiz'));
    await act(async () => { fireEvent.click(screen.getByRole('button', { name: /Nouvelle tâche/ })); });
    await waitFor(() => expect(titre()).toHaveValue(''));
    expect((screen.getByLabelText(/Description/) as HTMLTextAreaElement).value).toBe('');
  });

  it('tâche modifiée : la question est posée et la saisie reste', async () => {
    poser([TACHE], 'tache-1');
    render(<TasksPanel isOpen onClose={() => {}} standalone />);
    await waitFor(() => expect(titre()).toHaveValue('Relancer Ruiz'));
    fireEvent.change(titre(), { target: { value: 'Relancer Ruiz jeudi' } });
    await act(async () => { fireEvent.click(screen.getByRole('button', { name: /Nouvelle tâche/ })); });
    expect(screen.getByText(/Abandonner les modifications/)).toBeInTheDocument();
    expect(titre()).toHaveValue('Relancer Ruiz jeudi');
    expect(useTaskStore.getState().currentTaskId).toBe('tache-1');
  });
});

describe('B-995 et B-996 : la question se dit, et le focus ne se perd pas', () => {
  beforeEach(() => { mockListTasks.mockResolvedValue([]); });

  async function ouvrirUneSaisie() {
    poser([], null);
    useTaskStore.setState({ isTaskFormOpen: false } as never);
    render(<TasksPanel isOpen onClose={() => {}} standalone />);
    const nouvelle = await screen.findByRole('button', { name: /Nouvelle tâche/ });
    nouvelle.focus();
    await act(async () => { fireEvent.click(nouvelle); });
    await waitFor(() => expect(titre()).toBeInTheDocument());
    titre().focus();
    fireEvent.change(titre(), { target: { value: 'Rappeler le garage' } });
    return nouvelle;
  }

  it('B-995 : la question est annoncée et le focus va sur « Continuer la saisie », puis revient au champ', async () => {
    await ouvrirUneSaisie();
    const { runTopEscapeHandler } = await import('../../lib/escapeStack');
    act(() => { runTopEscapeHandler(); });
    expect(screen.getByRole('alert')).toHaveTextContent('Abandonner les modifications ?');
    expect(screen.getByRole('button', { name: 'Continuer la saisie' })).toHaveFocus();
    act(() => { runTopEscapeHandler(); });
    expect(screen.queryByRole('alert')).toBeNull();
    expect(titre()).toHaveFocus();
  });

  it('B-996 : « Abandonner » rend le focus au bouton qui avait ouvert le formulaire', async () => {
    const nouvelle = await ouvrirUneSaisie();
    fireEvent.click(screen.getByRole('button', { name: 'Retour' }));
    await act(async () => { fireEvent.click(screen.getByRole('button', { name: 'Abandonner' })); });
    await waitFor(() => expect(screen.getByRole('button', { name: /Nouvelle tâche/ })).toHaveFocus());
    expect(document.body).not.toHaveFocus();
    expect(nouvelle.isConnected).toBe(true);
  });
});

describe('B-998 : enregistrer une tâche sortie de la liste par un filtre', () => {
  it('filtre posé pendant la modification : « Enregistrer » met à jour, sans créer de copie', async () => {
    mockListTasks.mockResolvedValueOnce([TACHE]).mockResolvedValue([]);
    mockUpdateTask.mockResolvedValue({ ...TACHE, title: 'Relancer Ruiz jeudi' });
    mockCreateTask.mockResolvedValue({ ...TACHE, id: 'tache-copie' });
    poser([TACHE], 'tache-1');
    render(<TasksPanel isOpen onClose={() => {}} standalone />);
    await waitFor(() => expect(titre()).toHaveValue('Relancer Ruiz'));
    fireEvent.change(titre(), { target: { value: 'Relancer Ruiz jeudi' } });
    await act(async () => { useTaskStore.getState().setFilterStatus('done'); });
    await waitFor(() => expect(useTaskStore.getState().tasks).toHaveLength(0));

    await act(async () => { fireEvent.click(screen.getByRole('button', { name: 'Enregistrer' })); });
    await waitFor(() => expect(mockUpdateTask).toHaveBeenCalled());
    expect(mockUpdateTask.mock.calls[0][0]).toBe('tache-1');
    expect(mockCreateTask).not.toHaveBeenCalled();
  });
});

describe('B-1009 : le double montage de StrictMode ne déplace pas le focus', () => {
  it('ouverture du formulaire : le minuteur de B-996 ne s’exécute pas pour un faux démontage', async () => {
    const { TaskForm } = await import('./TaskForm');
    poser([], null);
    (document.activeElement as HTMLElement | null)?.blur();
    render(
      <StrictMode>
        <div data-testid="tasks-panel"><button type="button">Colonnes</button><TaskForm /></div>
      </StrictMode>,
    );
    await act(async () => { await new Promise((fin) => setTimeout(fin, 20)); });
    expect(screen.getByRole('button', { name: 'Colonnes' })).not.toHaveFocus();
  });
});
