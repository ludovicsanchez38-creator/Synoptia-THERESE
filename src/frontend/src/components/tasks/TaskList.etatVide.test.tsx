/**
 * Un écran vide propose une sortie.
 *
 * « Aucune tâche », seul au milieu de l'écran. Rien à cliquer, rien qui
 * explique. Le bouton « Nouvelle tâche » existe, mais dans la barre du haut,
 * loin du regard de quelqu'un qui vient de constater qu'il n'a rien.
 *
 * Un état vide est le moment où l'on a le PLUS besoin d'être guidé : c'est
 * souvent la première fois qu'on ouvre l'écran.
 */
import { render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

const mockListTasks = vi.fn();
vi.mock('../../services/api', async (importOriginal) => ({
  ...(await importOriginal<object>()),
  listTasks: (...a: unknown[]) => mockListTasks(...a),
}));

import { TaskList } from './TaskList';

describe('L’écran des tâches vide propose une sortie', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockListTasks.mockResolvedValue([]);
  });

  it('explique la situation plutôt que de constater le vide', () => {
    render(<TaskList />);

    expect(screen.getByText(/Aucune tâche/)).toBeInTheDocument();
    expect(
      screen.getByText(/première|commence|créer|ajouter/i),
    ).toBeInTheDocument();
  });

  it('propose de créer une tâche, là où l’on regarde', async () => {
    const { useTaskStore } = await import('../../stores/taskStore');
    render(<TaskList />);

    screen.getByRole('button', { name: /Créer une tâche/i }).click();

    // Le composant a déjà le geste par son store : inutile de lui passer une
    // prop pour ça.
    expect(useTaskStore.getState().isTaskFormOpen).toBe(true);
  });
});
