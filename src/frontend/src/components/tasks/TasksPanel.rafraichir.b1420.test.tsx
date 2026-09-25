/**
 * B-1420 (couverture écran P-145, tri du 25/09) : « Rafraîchir les tâches »
 * relisait la liste sans rien montrer. Au clic, l'utilisateur ne savait pas
 * si son geste avait été pris en compte.
 */
import { act, fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

import * as api from '../../services/api';
import { useTaskStore } from '../../stores/taskStore';
import { TasksPanel } from './TasksPanel';

vi.mock('../../services/api', async () => {
  const actual = await vi.importActual<Record<string, unknown>>('../../services/api');
  return { ...actual, listTasks: vi.fn().mockResolvedValue([]), listProjects: vi.fn().mockResolvedValue([]) };
});

describe('B-1420 : Rafraîchir les tâches se voit', () => {
  it('dit que la liste a été relue après le clic', async () => {
    useTaskStore.setState({ tasks: [], searchQuery: '', currentTaskId: null, isTaskFormOpen: false });
    render(<TasksPanel standalone />);
    const bouton = await screen.findByRole('button', { name: 'Rafraîchir les tâches' });
    expect(screen.queryByText(/Liste relue à/)).toBeNull();
    await act(async () => { fireEvent.click(bouton); });
    const statut = await screen.findByText(/Liste relue à \d{2}:\d{2}/);
    expect(statut.closest('[role="status"]')).not.toBeNull();
  });

  it('le bouton est occupé pendant la relecture', async () => {
    let finir: (valeur: never[]) => void = () => {};
    useTaskStore.setState({ tasks: [], searchQuery: '', currentTaskId: null, isTaskFormOpen: false });
    render(<TasksPanel standalone />);
    const bouton = await screen.findByRole('button', { name: 'Rafraîchir les tâches' });
    vi.mocked(api.listTasks).mockImplementationOnce(() => new Promise((resoudre) => { finir = resoudre; }));
    await act(async () => { fireEvent.click(bouton); });
    expect(bouton).toHaveAttribute('aria-busy', 'true');
    await act(async () => { finir([]); });
    expect(bouton).toHaveAttribute('aria-busy', 'false');
  });

  it('un échec ne dit pas que la liste est relue', async () => {
    useTaskStore.setState({ tasks: [], searchQuery: '', currentTaskId: null, isTaskFormOpen: false });
    render(<TasksPanel standalone />);
    const bouton = await screen.findByRole('button', { name: 'Rafraîchir les tâches' });
    vi.mocked(api.listTasks).mockRejectedValueOnce(new Error('panne'));
    await act(async () => { fireEvent.click(bouton); });
    expect(screen.queryByText(/Liste relue à/)).toBeNull();
  });
});
