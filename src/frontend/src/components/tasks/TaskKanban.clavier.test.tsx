/**
 * B-209 - terminer une tâche sans souris.
 *
 * En vue Kanban, « Marquer en cours » et « Marquer terminé » n'entraient dans
 * le DOM que sur `onMouseEnter` de la carte. Le focus clavier ne les faisait
 * pas apparaître : elles n'existaient que pour la souris, et la seule voie
 * restante au clavier était d'ouvrir la tâche puis son formulaire. Une
 * commande qu'aucun clavier n'atteint n'est pas une commande.
 *
 * Le focus atterrit sur le conteneur `useSortable` (celui qui porte
 * `tabIndex=0` et les écouteurs de dnd-kit), pas sur la carte : c'est là que
 * la révélation doit être branchée, sinon rien ne se déclenche.
 */
import { fireEvent, render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import * as api from '../../services/api';
import type { Task } from '../../services/api';
import { useTaskStore } from '../../stores/taskStore';
import { TaskKanban } from './TaskKanban';

vi.mock('../../services/api', async () => {
  const actual = await vi.importActual<Record<string, unknown>>('../../services/api');
  return { ...actual, updateTask: vi.fn().mockResolvedValue({}) };
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

function carte(): HTMLElement {
  // Le conteneur focalisable posé par useSortable, au-dessus de la carte.
  const item = screen.getByTestId('task-item');
  const conteneur = item.parentElement;
  if (!conteneur) throw new Error('conteneur sortable introuvable');
  return conteneur;
}

describe('B-209 - les commandes de la carte Kanban existent aussi au clavier', () => {
  beforeEach(() => {
    useTaskStore.setState({
      tasks: [TACHE],
      searchQuery: '',
      currentTaskId: null,
      isTaskFormOpen: false,
    });
  });

  it('le focus sur la carte révèle « Marquer terminé »', () => {
    render(<TaskKanban />);

    expect(screen.queryByRole('button', { name: 'Marquer terminé' })).toBeNull();
    fireEvent.focus(carte());
    expect(screen.getByRole('button', { name: 'Marquer terminé' })).toBeInTheDocument();
  });

  it('l’activer termine la tâche, sans ouvrir son formulaire', () => {
    render(<TaskKanban />);
    fireEvent.focus(carte());

    fireEvent.click(screen.getByRole('button', { name: 'Marquer terminé' }));

    // La commande part vraiment ; et le clic ne traverse pas jusqu'à la
    // carte, qui ouvrirait le formulaire à la place.
    expect(api.updateTask).toHaveBeenCalledWith(TACHE.id, { status: 'done' });
    expect(useTaskStore.getState().isTaskFormOpen).toBe(false);
  });

  it('quitter la carte au clavier referme les commandes', () => {
    render(<TaskKanban />);
    fireEvent.focus(carte());
    expect(screen.getByRole('button', { name: 'Marquer terminé' })).toBeInTheDocument();

    // `relatedTarget` hors de la carte : le focus part vraiment ailleurs.
    fireEvent.blur(carte(), { relatedTarget: document.body });
    expect(screen.queryByRole('button', { name: 'Marquer terminé' })).toBeNull();
  });

  /**
   * DA lot 6 : la rangée de commandes reste MONTÉE, cachée par `invisible` et
   * `aria-hidden`, pour que la hauteur de la carte ne bouge pas au survol. Le
   * Tab de la carte vers « Marquer terminé » passe donc par un `blur` dont la
   * `relatedTarget` est le bouton lui-même : sans la garde `contains`, la
   * cible du focus se retirerait de l'arbre d'accessibilité sous la main.
   */
  it('passer de la carte à sa commande ne la fait pas disparaître', () => {
    render(<TaskKanban />);
    fireEvent.focus(carte());

    const bouton = screen.getByRole('button', { name: 'Marquer terminé' });
    fireEvent.blur(carte(), { relatedTarget: bouton });

    expect(screen.queryByRole('button', { name: 'Marquer terminé' })).not.toBeNull();
  });
});

/**
 * B-750 - Entrée sur une commande révélée démarre un GLISSER, pas le bouton.
 *
 * Le `KeyboardSensor` de dnd-kit écoute `onKeyDown` sur le conteneur
 * `useSortable`, et un keydown parti d'un bouton de la carte y remonte. La
 * seule garde prévue par la bibliothèque compare la cible à l'`activatorNode`
 * (`@dnd-kit/core/dist/core.esm.js`, autour de `event.target !== activator`) :
 * tant que `setActivatorNodeRef` n'est jamais appelé, `activatorNode.current`
 * vaut `null`, la garde ne s'applique pas, et le capteur saisit la carte en
 * appelant `event.preventDefault()`.
 *
 * Recette du dépôt principal, `.cartography-work/validation/da-lot6/
 * apres-mesures.json`, cas `entree-sur-commande` : zéro requête, titre rendu
 * deux fois (la carte de survol du glisser), focus retombé sur `body`.
 *
 * jsdom n'implémente pas l'activation par défaut d'un bouton au clavier, et
 * le projet n'a pas `user-event` : le clic que le navigateur émet après un
 * keydown NON empêché est rejoué à la main. C'est exactement ce que le
 * `preventDefault` du capteur supprime chez l'utilisateur.
 */
describe('B-750 - Entrée sur une commande active le bouton, sans glisser', () => {
  beforeEach(() => {
    vi.mocked(api.updateTask).mockClear();
  });

  it('Entrée sur « Marquer terminé » termine la tâche et ne saisit pas la carte', () => {
    render(<TaskKanban />);
    fireEvent.focus(carte());

    const bouton = screen.getByRole('button', { name: 'Marquer terminé' });
    const nonEmpeche = fireEvent.keyDown(bouton, { key: 'Enter', code: 'Enter' });

    // Le capteur n'a pas confisqué la frappe : le navigateur activerait le bouton.
    expect(nonEmpeche).toBe(true);
    fireEvent.click(bouton);
    expect(api.updateTask).toHaveBeenCalledWith(TACHE.id, { status: 'done' });

    // Aucun glisser : le `DragOverlay` doublerait le titre de la tâche.
    expect(screen.getAllByText(TACHE.title)).toHaveLength(1);
  });

  it('Espace sur « Marquer en cours » passe la tâche en cours, sans glisser', () => {
    render(<TaskKanban />);
    fireEvent.focus(carte());

    const bouton = screen.getByRole('button', { name: 'Marquer en cours' });
    const nonEmpeche = fireEvent.keyDown(bouton, { key: ' ', code: 'Space' });

    expect(nonEmpeche).toBe(true);
    fireEvent.click(bouton);
    expect(api.updateTask).toHaveBeenCalledWith(TACHE.id, { status: 'in_progress' });
    expect(screen.getAllByText(TACHE.title)).toHaveLength(1);
  });
});
