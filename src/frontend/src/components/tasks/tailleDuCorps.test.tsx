/**
 * B-134 : sur l'écran des tâches, 12 px n'était plus une exception.
 *
 * L'audit de l'application lancée a compté 387 textes à 12 px contre 85 à
 * 14 px sur `tasks.open`. La cause est dans la carte de tâche, répétée une
 * fois par tâche : le titre est à 14 px, tout le reste à 12 px, y compris la
 * DESCRIPTION, qui est le corps de la carte et non une métadonnée.
 *
 * La règle que ce test fixe est celle du bug : 12 px est réservé aux
 * métadonnées (priorité, échéance, étiquettes), le corps vit à 14 px au
 * moins. D'où les deux assertions par vue - sans la seconde, le test
 * passerait au vert en poussant TOUT l'écran à 14 px, ce qui effacerait la
 * hiérarchie au lieu de la rétablir.
 */
import { render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it } from 'vitest';

import type { Task } from '../../services/api';
import { useTaskStore } from '../../stores/taskStore';
import { TaskKanban } from './TaskKanban';
import { TaskList } from './TaskList';

const TITRE = 'Relancer le devis Moreau';
const DESCRIPTION = 'Reprendre le devis DEV-2026-014 et rappeler la cliente avant vendredi.';

const tache: Task = {
  id: 't-1',
  title: TITRE,
  description: DESCRIPTION,
  status: 'todo',
  priority: 'medium',
  due_date: '2026-09-18T00:00:00Z',
  tags: ['facturation'],
  project_id: null,
  completed_at: null,
  created_at: '2026-09-01T00:00:00Z',
  updated_at: '2026-09-01T00:00:00Z',
};

/** La classe de taille effectivement portée par l'élément rendu. */
const classes = (element: HTMLElement) => element.className;

describe('B-134 : le corps de la carte de tâche n’est pas à la taille des métadonnées', () => {
  beforeEach(() => {
    useTaskStore.setState({
      tasks: [tache],
      searchQuery: '',
      currentTaskId: null,
      isTaskFormOpen: false,
    });
  });

  it('vue liste : la description est à 14 px, la priorité reste à 12 px', () => {
    render(<TaskList />);

    const description = screen.getByText(DESCRIPTION);
    expect(
      classes(description),
      `la description est le corps de la carte : ${classes(description)}`,
    ).not.toMatch(/\btext-xs\b/);
    expect(classes(description)).toMatch(/\btext-sm\b/);

    const priorite = screen.getByText('Moyenne');
    expect(
      classes(priorite),
      'la priorité est une métadonnée : elle doit rester à 12 px',
    ).toMatch(/\btext-xs\b/);
  });

  it('vue kanban : la description est à 14 px, la priorité reste à 12 px', () => {
    render(<TaskKanban />);

    const description = screen.getByText(DESCRIPTION);
    expect(
      classes(description),
      `la description est le corps de la carte : ${classes(description)}`,
    ).not.toMatch(/\btext-xs\b/);
    expect(classes(description)).toMatch(/\btext-sm\b/);

    const priorite = screen.getByText('Moyenne');
    expect(
      classes(priorite),
      'la priorité est une métadonnée : elle doit rester à 12 px',
    ).toMatch(/\btext-xs\b/);
  });
});
