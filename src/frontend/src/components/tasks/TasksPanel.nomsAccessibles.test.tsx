/**
 * B-209, seconde moitié - un bouton sans nom n'est pas annonçable.
 *
 * Sur l'écran Tâches, trois commandes n'avaient pour tout contenu qu'une
 * icône `lucide` : filtrer, rafraîchir, fermer. Ni `aria-label`, ni `title`,
 * ni texte - un lecteur d'écran annonce « bouton », et rien d'autre. Les
 * bascules Kanban / Liste voisines portaient déjà un `title` : l'écart était
 * interne au même en-tête.
 *
 * Le balayage porte sur TOUS les boutons rendus plutôt que sur les trois
 * connus : une liste de trois se périme au quatrième bouton ajouté.
 */
import { render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import type { Task } from '../../services/api';
import { useTaskStore } from '../../stores/taskStore';
import { TasksPanel } from './TasksPanel';

vi.mock('../../services/api', async () => {
  const actual = await vi.importActual<Record<string, unknown>>('../../services/api');
  return { ...actual, listTasks: vi.fn().mockResolvedValue([]) };
});

const TACHE: Task = {
  id: 'tache-1',
  title: 'Relancer Sophie Moreau',
  description: null,
  status: 'todo',
  priority: 'medium',
  due_date: null,
  project_id: null,
  contact_id: null,
  tags: [],
  created_at: '2026-09-01T08:00:00Z',
  updated_at: '2026-09-01T08:00:00Z',
} as unknown as Task;

describe('B-209 - aucun bouton anonyme sur l’écran Tâches', () => {
  beforeEach(() => {
    useTaskStore.setState({
      tasks: [TACHE],
      searchQuery: '',
      currentTaskId: null,
      isTaskFormOpen: false,
    });
  });

  it('chaque bouton porte un nom accessible', () => {
    render(<TasksPanel standalone />);

    // `name: /\S/` fait calculer le nom accessible par testing-library :
    // ce qui manque à l'appel est exactement ce qu'aucun lecteur d'écran
    // ne saurait annoncer.
    const nommes = screen.queryAllByRole('button', { name: /\S/ });
    const anonymes = screen
      .getAllByRole('button')
      .filter((bouton) => !nommes.includes(bouton))
      .map((bouton) => bouton.innerHTML.slice(0, 60));

    expect(anonymes).toEqual([]);
  });

  it('témoin : l’écran rend bien une poignée de boutons', () => {
    render(<TasksPanel standalone />);

    expect(screen.getAllByRole('button').length).toBeGreaterThan(4);
  });

  /**
   * B-231, reliquat : `title` n'est qu'un DERNIER recours du calcul de nom
   * accessible. Il est visible à la souris, absent de plusieurs technologies
   * d'assistance, et jamais annoncé sur un mobile tactile. Les bascules
   * Kanban / Liste ne tenaient que par lui - la règle ci-dessus, qui interroge
   * le nom calculé, ne pouvait donc pas les voir.
   */
  it('aucun bouton ne tient son nom du seul attribut title', () => {
    render(<TasksPanel standalone />);

    const surTitreSeul = screen
      .getAllByRole('button')
      .filter(
        (bouton) =>
          !bouton.getAttribute('aria-label') &&
          !bouton.getAttribute('aria-labelledby') &&
          !(bouton.textContent ?? '').trim(),
      )
      .map((bouton) => bouton.getAttribute('title') ?? bouton.innerHTML.slice(0, 40));

    expect(surTitreSeul).toEqual([]);
  });
});
