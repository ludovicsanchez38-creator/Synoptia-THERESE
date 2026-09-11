/**
 * B-750 - au clavier, Entrée sur une commande de la carte démarre un GLISSER.
 *
 * `SortableProjectCard` pose `{...listeners}` de `useSortable` sur son
 * enveloppe, mais n'appelle jamais `setActivatorNodeRef`. La garde du
 * `KeyboardSensor` de dnd-kit (`@dnd-kit/core/dist/core.esm.js`, autour de
 * `event.target !== activator`) ne s'applique qu'avec un `activatorNode`
 * posé : sans lui, tout keydown Entrée ou Espace remonté d'un bouton de la
 * carte saisit le projet, et `event.preventDefault()` confisque l'activation
 * du bouton visé.
 *
 * jsdom n'active pas un bouton sur Entrée et le projet n'a pas `user-event` :
 * le clic que le navigateur émet après un keydown NON empêché est rejoué à la
 * main, puisque c'est précisément lui que le `preventDefault` supprime.
 */

import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import { ProjectsKanban } from './ProjectsKanban';
import type { Project } from '../../services/api';

const PROJET: Project = {
  id: 'p-alpha',
  name: 'Projet Alpha',
  status: 'active',
  description: null,
  contact_id: null,
  budget: null,
  notes: null,
  tags: null,
  created_at: '2026-06-01T00:00:00Z',
  updated_at: '2026-06-01T00:00:00Z',
};

function monter() {
  const onSelect = vi.fn();
  const onDelete = vi.fn();
  const onStatusChange = vi.fn().mockResolvedValue(undefined);
  render(
    <ProjectsKanban
      projects={[PROJET]}
      onSelect={onSelect}
      onDelete={onDelete}
      onStatusChange={onStatusChange}
    />
  );
  return { onSelect, onDelete };
}

/** Le bouton du NOM, pas l'enveloppe sortable, qui porte aussi `role="button"`. */
function boutonDuNom(): HTMLElement {
  const bouton = screen.getByText(PROJET.name).closest('button');
  if (!(bouton instanceof HTMLElement)) throw new Error('bouton du nom introuvable');
  return bouton;
}

describe('B-750 - Entrée sur une commande du projet active le bouton', () => {
  it('Entrée sur le nom ouvre le projet et ne saisit pas la carte', () => {
    const { onSelect } = monter();

    const bouton = boutonDuNom();
    const nonEmpeche = fireEvent.keyDown(bouton, { key: 'Enter', code: 'Enter' });

    expect(nonEmpeche).toBe(true);
    fireEvent.click(bouton);
    expect(onSelect).toHaveBeenCalledTimes(1);
    expect(onSelect.mock.calls[0][0].id).toBe(PROJET.id);

    // Aucun glisser : le `DragOverlay` doublerait le nom du projet.
    expect(screen.getAllByText(PROJET.name)).toHaveLength(1);
  });

  it('Espace sur « Supprimer » demande la suppression, sans glisser', () => {
    const { onDelete } = monter();

    const bouton = screen.getByRole('button', { name: `Supprimer ${PROJET.name}` });
    const nonEmpeche = fireEvent.keyDown(bouton, { key: ' ', code: 'Space' });

    expect(nonEmpeche).toBe(true);
    fireEvent.click(bouton);
    expect(onDelete).toHaveBeenCalledTimes(1);
    expect(screen.getAllByText(PROJET.name)).toHaveLength(1);
  });
});
