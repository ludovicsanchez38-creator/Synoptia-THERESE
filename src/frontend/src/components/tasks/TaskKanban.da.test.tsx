/**
 * DA « Application affinée », lot 6 : les colonnes de l'écran Tâches
 * (`docs/plans/2026-09-11-da-lot6-projets-design.md`, § 3 et § 9).
 */
import { fireEvent, render, screen, within } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import type { Task } from '../../services/api';
import { useTaskStore } from '../../stores/taskStore';
import { TaskKanban } from './TaskKanban';

vi.mock('../../services/api', async () => {
  const actual = await vi.importActual<Record<string, unknown>>('../../services/api');
  return { ...actual, updateTask: vi.fn().mockResolvedValue({}) };
});

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

function poser(taches: Task[]) {
  useTaskStore.setState({
    tasks: taches,
    searchQuery: '',
    currentTaskId: null,
    isTaskFormOpen: false,
  });
}

const SEULE = tache({ id: 't-1', title: 'Relancer Sophie Moreau' });

function conteneurSortable(): HTMLElement {
  const parent = screen.getByTestId('task-item').parentElement;
  if (!parent) throw new Error('conteneur sortable introuvable');
  return parent;
}

beforeEach(() => {
  vi.clearAllMocks();
  poser([SEULE]);
});

describe('Lot 6 DA : têtes de colonnes', () => {
  it('trois h3, chacun une Etiquette et un compte nu', () => {
    render(<TaskKanban />);

    const titres = screen.getAllByRole('heading', { level: 3 });
    expect(titres).toHaveLength(3);
    for (const titre of titres) {
      expect(titre.querySelector('[data-etiquette]')).not.toBeNull();
      expect(titre.textContent ?? '').not.toMatch(/[()]/);
    }
    expect(within(titres[0]).getByText('À faire')).toHaveAttribute('data-etiquette');
    expect(within(titres[1]).getByText('En cours')).toHaveAttribute('data-etiquette');
    expect(within(titres[2]).getByText('Terminé')).toHaveAttribute('data-etiquette');
    expect(titres[0].textContent).toContain('1');
  });

  it('la grille garde deux colonnes sous 1023 px, sur deux rangées 1fr', () => {
    const { container } = render(<TaskKanban />);

    const grille = container.querySelector('[class*="grid-cols-3"]') as HTMLElement;
    expect(grille).not.toBeNull();
    expect(grille.className).not.toMatch(/grid-cols-1/);
    expect(grille.className).toMatch(/max-\[1023px\]:grid-cols-2/);
    expect(grille.className).toMatch(/max-\[1023px\]:grid-rows-2/);
    expect(grille.className).toMatch(/max-\[1023px\]:auto-rows-fr/);

    const liste = screen.getByTestId('task-item').closest('[class*="overflow-y-auto"]') as HTMLElement;
    expect(liste).not.toBeNull();
    expect(liste.className).toMatch(/\b(space-y-2|gap-2)\b/);
    expect(liste.className).toMatch(/\bmin-h-0\b/);
  });
});

describe('Lot 6 DA : la carte de tâche', () => {
  it('la priorité est une barre nommée, plus un mot, et chaque niveau a sa teinte', () => {
    poser([
      tache({ id: 't-u', title: 'Payer l’URSSAF', priority: 'urgent' }),
      tache({ id: 't-h', title: 'Relire le devis', priority: 'high' }),
      tache({ id: 't-m', title: 'Préparer la séance', priority: 'medium' }),
    ]);
    render(<TaskKanban />);

    const urgente = screen.getByLabelText('Priorité urgente');
    const haute = screen.getByLabelText('Priorité haute');
    const moyenne = screen.getByLabelText('Priorité moyenne');
    expect(urgente).toHaveAttribute('role', 'img');
    expect(urgente.className).toMatch(/\bbg-error-fill\b/);
    expect(haute.className).toMatch(/\bbg-warning-fill\b/);
    expect(moyenne.className).toMatch(/\bbg-info-fill\b/);
    expect(urgente.className).not.toBe(haute.className);

    expect(screen.queryByText('Urgent')).toBeNull();
    expect(screen.queryByText('Haute')).toBeNull();
    expect(screen.queryByText('Moyenne')).toBeNull();
  });

  it('« En retard » est une Etiquette, sans compte de jours', () => {
    poser([tache({ id: 't-r', title: 'Relancer Claire Roux', due_date: '2020-01-02T00:00:00Z' })]);
    render(<TaskKanban />);

    expect(screen.getByText('En retard')).toHaveAttribute('data-etiquette');
    expect(screen.queryByText(/En retard de/)).toBeNull();
  });

  it('task-item est sur la carte, jamais sur celle du glisser', () => {
    render(<TaskKanban />);
    expect(screen.getAllByTestId('task-item')).toHaveLength(1);

    const titre = screen.getByText(SEULE.title);
    fireEvent.pointerDown(titre, { button: 0, isPrimary: true, pointerId: 1, clientX: 5, clientY: 5 });
    fireEvent.pointerMove(document, { pointerId: 1, clientX: 5, clientY: 40 });

    expect(screen.getAllByText(SEULE.title)).toHaveLength(2);
    expect(screen.getAllByTestId('task-item')).toHaveLength(1);
    // La rangée de commandes n'est pas montée sur la carte de survol.
    expect(document.querySelectorAll('button[aria-label="Marquer terminé"]')).toHaveLength(1);

    fireEvent.pointerUp(document, { pointerId: 1 });
    fireEvent.click(document);
  });
});

describe('Lot 6 DA : les commandes de la carte', () => {
  it('la rangée vit dans le flux, montée mais hors de l’arbre d’accessibilité', () => {
    const { container } = render(<TaskKanban />);

    const bouton = container.querySelector('button[aria-label="Marquer terminé"]') as HTMLElement;
    expect(bouton).not.toBeNull();
    const rangee = bouton.parentElement as HTMLElement;
    expect(rangee.className).toMatch(/\bmt-2\b/);
    expect(rangee.className).not.toMatch(/\babsolute\b/);
    expect(rangee.className).toMatch(/\binvisible\b/);
    expect(rangee.className).toMatch(/\bpointer-events-none\b/);
    expect(rangee).toHaveAttribute('aria-hidden', 'true');
    expect(screen.queryByRole('button', { name: 'Marquer terminé' })).toBeNull();
  });

  it('le focus sur une tâche à faire révèle « Marquer en cours » et « Marquer terminé »', () => {
    render(<TaskKanban />);
    fireEvent.focus(conteneurSortable());

    expect(screen.getByRole('button', { name: 'Marquer en cours' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Marquer terminé' })).toBeInTheDocument();
  });

  it('le focus sur une tâche terminée révèle « Rouvrir »', () => {
    poser([tache({ id: 't-f', title: 'Finir le dossier', status: 'done' })]);
    render(<TaskKanban />);
    fireEvent.focus(conteneurSortable());

    expect(screen.getByRole('button', { name: 'Rouvrir' })).toBeInTheDocument();
  });

  it('passer de la carte au bouton ne le fait pas disparaître sous la main', () => {
    render(<TaskKanban />);
    const conteneur = conteneurSortable();
    fireEvent.focus(conteneur);

    const bouton = screen.getByRole('button', { name: 'Marquer terminé' });
    fireEvent.blur(conteneur, { relatedTarget: bouton });

    expect(screen.queryByRole('button', { name: 'Marquer terminé' })).not.toBeNull();
  });
});
