/**
 * DA « Application affinée », lot 6 : l'écran Projets et tâches
 * (`docs/plans/2026-09-11-da-lot6-projets-design.md`, § 9).
 *
 * En-tête, filtres, états et plancher de taille de `TasksPanel`.
 */
import { readFileSync } from 'node:fs';
import { join } from 'node:path';

import { fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import type { Task } from '../../services/api';
import { useTaskStore } from '../../stores/taskStore';

const { mockListTasks, mockListProjects } = vi.hoisted(() => ({
  mockListTasks: vi.fn(),
  mockListProjects: vi.fn(),
}));

vi.mock('../../services/api', async () => {
  const actual = await vi.importActual<Record<string, unknown>>('../../services/api');
  return {
    ...actual,
    listTasks: (...args: unknown[]) => mockListTasks(...args),
    listProjects: (...args: unknown[]) => mockListProjects(...args),
    listContacts: vi.fn().mockResolvedValue([]),
  };
});

import { TasksPanel } from './TasksPanel';

const SOURCE = readFileSync(join(__dirname, 'TasksPanel.tsx'), 'utf-8');

function tache(id: string, patch: Partial<Task> = {}): Task {
  return {
    id,
    title: `Tâche ${id}`,
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

function poser(taches: Task[], extra: { isTaskFormOpen?: boolean; viewMode?: 'list' | 'kanban' } = {}) {
  useTaskStore.setState({
    tasks: taches,
    searchQuery: '',
    currentTaskId: null,
    isTaskFormOpen: extra.isTaskFormOpen ?? false,
    viewMode: extra.viewMode ?? 'kanban',
    filterStatus: null,
    filterPriority: null,
    filterProjectId: null,
  });
}

function classesDUnNoeud(n: Element): string {
  const brut = (n as HTMLElement).className;
  if (typeof brut === 'string') return brut;
  const svg = (n as SVGElement).className;
  return typeof svg === 'object' && svg && 'baseVal' in svg ? svg.baseVal : '';
}

function interactifsSousLePlancher(racine: HTMLElement): string[] {
  const fautifs: string[] = [];
  for (const el of racine.querySelectorAll('button, input, select, textarea, a, [role="button"]')) {
    const noeuds = [el, ...Array.from(el.querySelectorAll('*'))];
    for (const n of noeuds) {
      if (/\btext-xs\b/.test(classesDUnNoeud(n))) {
        fautifs.push(((el as HTMLElement).textContent ?? el.tagName).trim().slice(0, 48));
        break;
      }
    }
  }
  return fautifs;
}

/** Les rangées de squelette du § 8 : `flex gap-3 items-center px-4 py-3`, muettes. */
function rangeesSquelette(racine: HTMLElement): Element[] {
  return Array.from(racine.querySelectorAll('div[aria-hidden="true"]')).filter((n) => {
    const c = classesDUnNoeud(n);
    return /\bgap-3\b/.test(c) && /\bitems-center\b/.test(c) && /\bpy-3\b/.test(c);
  });
}

function libelles(select: HTMLElement): (string | null)[] {
  return Array.from(select.querySelectorAll('option')).map((o) => o.textContent);
}

beforeEach(() => {
  vi.clearAllMocks();
  mockListTasks.mockResolvedValue([]);
  mockListProjects.mockResolvedValue([]);
  poser([]);
});

describe('Lot 6 DA : en-tête de TasksPanel', () => {
  it('la bascule de vue est un groupe de segments nommé, aria-pressed suit viewMode', async () => {
    render(<TasksPanel standalone />);

    const groupe = await screen.findByRole('group', { name: 'Vue des tâches' });
    const colonnes = within(groupe).getByRole('button', { name: 'Colonnes' });
    const liste = within(groupe).getByRole('button', { name: 'Liste' });
    expect(colonnes).toHaveAttribute('aria-pressed', 'true');
    expect(liste).toHaveAttribute('aria-pressed', 'false');

    fireEvent.click(liste);
    expect(useTaskStore.getState().viewMode).toBe('list');
    await waitFor(() => {
      expect(screen.getByRole('button', { name: 'Liste' })).toHaveAttribute('aria-pressed', 'true');
      expect(screen.getByRole('button', { name: 'Colonnes' })).toHaveAttribute('aria-pressed', 'false');
    });
  });

  it('le compteur dit « 0 tâche » au singulier', async () => {
    render(<TasksPanel standalone />);
    expect(await screen.findByText(/^0 tâche$/)).toBeInTheDocument();
  });

  it('le compteur dit « 2 tâches », et la forme sans accent n’apparaît nulle part', async () => {
    poser([tache('t1'), tache('t2')]);
    const { container } = render(<TasksPanel standalone />);

    expect(await screen.findByText(/^2 tâches$/)).toBeInTheDocument();
    expect(container.innerHTML).not.toMatch(/\btaches?\b/i);
  });

  it('« Filtrer » garde son nom accessible et déplie les mêmes listes', async () => {
    render(<TasksPanel standalone />);

    const filtrer = await screen.findByRole('button', { name: 'Filtrer les tâches' });
    expect(filtrer).toHaveTextContent('Filtrer');
    expect(filtrer).toHaveAttribute('aria-expanded', 'false');

    fireEvent.click(filtrer);
    expect(filtrer).toHaveAttribute('aria-expanded', 'true');
    expect(libelles(screen.getByLabelText('Filtrer par statut'))).toEqual([
      'Tous les statuts', 'À faire', 'En cours', 'Terminé', 'Annulé',
    ]);
    expect(libelles(screen.getByLabelText('Filtrer par priorité'))).toEqual([
      'Toutes les priorités', 'Urgent', 'Haute', 'Moyenne', 'Basse',
    ]);
    // Sans projet ni tag, les deux autres listes n'existent pas, comme aujourd'hui.
    expect(screen.queryByLabelText('Filtrer par projet')).toBeNull();
    expect(screen.queryByLabelText('Filtrer par étiquette')).toBeNull();
  });
});

describe('Lot 6 DA : plancher de taille et jetons', () => {
  it('aucun interactif sous 14 px, aucun Button sm, aucun bg-black', async () => {
    poser([tache('t1', { tags: ['facturation'], due_date: '2026-09-18T00:00:00Z' })]);
    render(<TasksPanel standalone />);
    await screen.findByTestId('tasks-panel');

    expect(interactifsSousLePlancher(screen.getByTestId('tasks-panel'))).toEqual([]);
    expect(SOURCE).not.toMatch(/size="sm"/);
    expect(SOURCE).not.toMatch(/bg-black\//);
  });
});

describe('Lot 6 DA : les états de TasksPanel', () => {
  it('zéro « Réessayer » quand le chargement échoue sans cache', async () => {
    mockListTasks.mockRejectedValue(new Error('panne'));
    render(<TasksPanel standalone />);

    expect(await screen.findByRole('alert')).toHaveTextContent('Impossible de charger les tâches');
    expect(screen.queryByRole('button', { name: 'Réessayer' })).toBeNull();
  });

  it('zéro « Réessayer » non plus quand le rafraîchissement échoue sur un cache', async () => {
    poser([tache('t1')]);
    mockListTasks.mockRejectedValue(new Error('panne'));
    render(<TasksPanel standalone />);

    expect(await screen.findByRole('alert')).toHaveTextContent('périmée');
    expect(screen.queryByRole('button', { name: 'Réessayer' })).toBeNull();
  });

  it('l’erreur est un frère : un échec de rafraîchissement ne cache pas le formulaire ouvert', async () => {
    poser([tache('t1')], { isTaskFormOpen: true });
    mockListTasks.mockRejectedValue(new Error('panne'));
    render(<TasksPanel standalone />);

    expect(await screen.findByRole('alert')).toHaveTextContent('périmée');
    expect(screen.getByRole('heading', { name: 'Nouvelle tâche' })).toBeInTheDocument();
  });

  it('le chargement pose trois rangées de squelette, muettes et sans nouvelle chaîne', async () => {
    let liberer: (valeur: Task[]) => void = () => {};
    mockListTasks.mockImplementation(() => new Promise<Task[]>((resolve) => { liberer = resolve; }));
    const { container } = render(<TasksPanel standalone />);

    const rangees = rangeesSquelette(container);
    expect(rangees).toHaveLength(3);
    expect(container.textContent).not.toMatch(/Chargement/);

    liberer([]);
    await waitFor(() => expect(rangeesSquelette(container)).toHaveLength(0));
  });
});
