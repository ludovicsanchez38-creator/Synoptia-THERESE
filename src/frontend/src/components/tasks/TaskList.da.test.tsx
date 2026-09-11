/**
 * DA « Application affinée », lot 6 : la liste de l'écran Tâches
 * (`docs/plans/2026-09-11-da-lot6-projets-design.md`, § 4 et § 9).
 */
import { fireEvent, render, screen, within } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import type { Task } from '../../services/api';
import { useDemoStore } from '../../stores/demoStore';
import { useTaskStore } from '../../stores/taskStore';

const api = vi.hoisted(() => ({ listTasks: vi.fn(), deleteTask: vi.fn() }));
vi.mock('../../services/api', async (importOriginal) => ({
  ...(await importOriginal<object>()),
  listTasks: (...a: unknown[]) => api.listTasks(...a),
  deleteTask: (...a: unknown[]) => api.deleteTask(...a),
}));

import { TaskList } from './TaskList';

function tache(patch: Partial<Task> & Pick<Task, 'id' | 'title'>): Task {
  return {
    description: null,
    status: 'todo',
    priority: 'medium',
    due_date: null,
    project_id: null,
    contact_id: null,
    tags: [],
    created_at: '2026-09-01T08:00:00Z',
    updated_at: '2026-09-01T08:00:00Z',
    ...patch,
  } as unknown as Task;
}

function poser(taches: Task[], searchQuery = '') {
  useTaskStore.setState({
    tasks: taches,
    searchQuery,
    currentTaskId: null,
    isTaskFormOpen: false,
  });
}

const RUIZ = tache({ id: 't1', title: 'Relancer Ruiz' });

beforeEach(() => {
  vi.clearAllMocks();
  api.listTasks.mockResolvedValue([]);
  api.deleteTask.mockResolvedValue(undefined);
  useDemoStore.setState({ enabled: false, replacementMap: new Map() });
  poser([RUIZ]);
});

describe('Lot 6 DA : la rangée de la liste', () => {
  it('est une grille 2.25rem 1fr auto, sans rôle ni tabIndex sur la rangée', () => {
    render(<TaskList />);

    const rangee = screen.getByTestId('task-item');
    expect(rangee.className).toMatch(/grid-cols-\[2\.25rem_1fr_auto\]/);
    expect(rangee.tagName).not.toBe('BUTTON');
    expect(rangee).not.toHaveAttribute('role');
    expect(rangee).not.toHaveAttribute('tabindex');
  });

  it('la priorité est la même barre nommée que dans les colonnes', () => {
    render(<TaskList />);

    const rangee = screen.getByTestId('task-item');
    const barre = within(rangee).getByLabelText('Priorité moyenne');
    expect(barre).toHaveAttribute('role', 'img');
    expect(barre.className).toMatch(/\bbg-info-fill\b/);
    expect(barre.className).toMatch(/\bw-1\b/);
    expect(within(rangee).queryByText('Moyenne')).toBeNull();
  });

  /**
   * Recette du lot 6 : la commande « Ouvrir la tâche » est un bouton texte
   * de 21 px, comme l'était le bouton Client du lot 5 (revue, point 3) :
   * une cible plus basse que tout le reste de l'écran. `min-h-9` la met à
   * la hauteur de la rangée sans changer le texte.
   */
  it('la commande « Ouvrir la tâche » a la hauteur des autres interactifs (min-h-9)', () => {
    render(<TaskList />);
    const bouton = screen.getByRole('button', { name: 'Ouvrir la tâche Relancer Ruiz' });
    expect(bouton.className).toMatch(/\bmin-h-9\b/);
  });

  it('D105 et D106 : ouvrir, cocher et supprimer gardent leurs noms', () => {
    render(<TaskList />);

    expect(screen.getByRole('button', { name: 'Ouvrir la tâche Relancer Ruiz' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Marquer la tâche Relancer Ruiz terminée' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Supprimer la tâche Relancer Ruiz' })).toBeInTheDocument();
  });

  /**
   * Le mode démo masque le texte VISIBLE (`maskText(task.title)`), mais les
   * trois `aria-label` interpolaient `task.title` brut : le vrai nom du
   * client sortait par le nom accessible, que lit tout lecteur d'écran et
   * que rapporte toute capture d'arbre d'accessibilité. Une démonstration
   * masquée à l'œil et nue à l'oreille.
   */
  it('D105 et D106 : en mode démo, les trois noms portent le titre MASQUÉ', () => {
    useDemoStore.setState({ enabled: true, replacementMap: new Map([['Ruiz', 'Moreau']]) });
    render(<TaskList />);

    expect(screen.getByRole('button', { name: 'Ouvrir la tâche Relancer Moreau' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Marquer la tâche Relancer Moreau terminée' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Supprimer la tâche Relancer Moreau' })).toBeInTheDocument();
    expect(screen.queryAllByRole('button', { name: /Ruiz/ })).toEqual([]);
  });

  it('un clic sur la rangée, hors des trois commandes, ouvre la tâche', () => {
    render(<TaskList />);

    fireEvent.click(screen.getByTestId('task-item'));
    expect(useTaskStore.getState().currentTaskId).toBe('t1');
    expect(useTaskStore.getState().isTaskFormOpen).toBe(true);
  });

  it('la confirmation de suppression n’est pas une alerte', () => {
    render(<TaskList />);
    fireEvent.click(screen.getByRole('button', { name: 'Supprimer la tâche Relancer Ruiz' }));

    const question = screen.getByText(/Supprimer « Relancer Ruiz » \?/);
    expect(question.closest('[role="alert"]')).toBeNull();
    expect(screen.getByText('Cette action est irréversible.')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Conserver la tâche' }).className).toMatch(/\bh-9\b/);
    expect(screen.getByRole('button', { name: 'Supprimer définitivement' }).className).toMatch(/\bh-9\b/);
  });
});

describe('Lot 6 DA : l’état vide de la liste', () => {
  it('sans requête : titre en h3 et sortie « Créer une tâche » en 36 px', () => {
    poser([]);
    render(<TaskList />);

    expect(
      screen.getByRole('heading', { level: 3, name: 'Aucune tâche pour l’instant' }),
    ).toBeInTheDocument();
    expect(
      screen.getByText(/Note ce que tu ne veux pas oublier/),
    ).toBeInTheDocument();

    const creer = screen.getByRole('button', { name: 'Créer une tâche' });
    expect(creer.className).toMatch(/\bh-9\b/);
    fireEvent.click(creer);
    expect(useTaskStore.getState().isTaskFormOpen).toBe(true);
  });

  it('avec une requête : le titre et le corps disent ce qui a été cherché', () => {
    poser([], 'facture');
    render(<TaskList />);

    expect(
      screen.getByRole('heading', { level: 3, name: 'Aucune tâche ne correspond' }),
    ).toBeInTheDocument();
    expect(screen.getByText(/Rien ne correspond à « facture »/)).toBeInTheDocument();
  });
});
