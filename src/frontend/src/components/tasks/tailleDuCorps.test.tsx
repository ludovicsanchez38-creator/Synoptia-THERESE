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
 *
 * DA lot 6 (11/09/2026), alignement de FORME : la priorité n'est plus un mot
 * mais une barre nommée (`role="img"`, `w-1`), dans les DEUX vues. La seconde
 * assertion tient donc désormais sur l'échéance et l'étiquette, les deux
 * métadonnées qui restent du texte. Aucune assertion n'est retirée.
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

/**
 * Les métadonnées de la carte, dans la vue montée. La priorité est une barre
 * nommée : on la lit par son nom accessible, pas par un mot. L'échéance et
 * l'étiquette, elles, sont bien du texte et restent à 12 px - c'est ce qui
 * empêche de rendre ce test vert en poussant tout l'écran à 14 px.
 */
function verifierLesMetadonnees() {
  const barre = screen.getByLabelText('Priorité moyenne');
  expect(barre, 'la priorité est un aplat nommé, pas un mot').toHaveAttribute('role', 'img');
  expect(classes(barre)).toMatch(/\bw-1\b/);
  expect(classes(barre), 'un aplat ne porte pas de taille de texte').not.toMatch(/\btext-xs\b/);
  expect(screen.queryByText('Moyenne')).toBeNull();

  const echeance = screen.getByText(/18 sept/);
  expect(
    classes(echeance),
    'l’échéance est une métadonnée : elle doit rester à 12 px',
  ).toMatch(/\btext-xs\b/);

  const etiquette = screen.getByText('facturation');
  expect(
    classes(etiquette),
    'une étiquette est une métadonnée : elle doit rester à 12 px',
  ).toMatch(/\btext-xs\b/);
}

describe('B-134 : le corps de la carte de tâche n’est pas à la taille des métadonnées', () => {
  beforeEach(() => {
    useTaskStore.setState({
      tasks: [tache],
      searchQuery: '',
      currentTaskId: null,
      isTaskFormOpen: false,
    });
  });

  it('vue liste : la description est à 14 px, les métadonnées restent à 12 px', () => {
    render(<TaskList />);

    const description = screen.getByText(DESCRIPTION);
    expect(
      classes(description),
      `la description est le corps de la carte : ${classes(description)}`,
    ).not.toMatch(/\btext-xs\b/);
    expect(classes(description)).toMatch(/\btext-sm\b/);

    verifierLesMetadonnees();
  });

  it('vue kanban : la description est à 14 px, les métadonnées restent à 12 px', () => {
    render(<TaskKanban />);

    const description = screen.getByText(DESCRIPTION);
    expect(
      classes(description),
      `la description est le corps de la carte : ${classes(description)}`,
    ).not.toMatch(/\btext-xs\b/);
    expect(classes(description)).toMatch(/\btext-sm\b/);

    verifierLesMetadonnees();
  });
});
