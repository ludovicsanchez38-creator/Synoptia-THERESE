/**
 * Tests ProjectsKanban - régression BUG-041.
 *
 * Le drag & drop des projets entre rubriques (statuts) était inopérant pour
 * l'utilisateur : les listeners de useSortable n'étaient posés que sur la
 * poignée GripVertical (16px, quasi invisible), pas sur la carte. Attraper
 * la carte par son corps - le geste naturel - ne démarrait aucun drag.
 * Ces tests vérifient que le drag s'active depuis le corps de la carte
 * (pointeur et clavier) et que le clic simple continue d'ouvrir le projet.
 */

import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import { ProjectsKanban } from './ProjectsKanban';
import type { Project } from '../../services/api';

function makeProject(overrides: Partial<Project> & Pick<Project, 'id' | 'name' | 'status'>): Project {
  return {
    description: null,
    contact_id: null,
    budget: null,
    notes: null,
    tags: null,
    created_at: '2026-06-01T00:00:00Z',
    updated_at: '2026-06-01T00:00:00Z',
    ...overrides,
  };
}

const projects: Project[] = [
  makeProject({ id: 'p-alpha', name: 'Projet Alpha', status: 'active' }),
  makeProject({ id: 'p-gamma', name: 'Projet Gamma', status: 'on_hold' }),
];

function renderKanban() {
  const onSelect = vi.fn();
  const onDelete = vi.fn();
  const onStatusChange = vi.fn().mockResolvedValue(undefined);
  render(
    <ProjectsKanban
      projects={projects}
      onSelect={onSelect}
      onDelete={onDelete}
      onStatusChange={onStatusChange}
    />
  );
  return { onSelect, onDelete, onStatusChange };
}

/** Le wrapper sortable de la carte (élément portant role + tabIndex posés par useSortable). */
function getSortableWrapper(projectName: string): HTMLElement {
  const title = screen.getByText(projectName);
  const wrapper = title.closest('[aria-roledescription="sortable"]');
  if (!(wrapper instanceof HTMLElement)) {
    throw new Error(`Wrapper sortable introuvable pour ${projectName}`);
  }
  return wrapper;
}

describe('ProjectsKanban drag & drop (BUG-041)', () => {
  it('démarre un drag au pointeur depuis le corps de la carte (pas seulement la poignée)', () => {
    renderKanban();

    // Geste utilisateur : attraper la carte par son titre, puis bouger au-delà
    // de l'activationConstraint (distance 8px).
    const title = screen.getByText('Projet Alpha');
    fireEvent.pointerDown(title, {
      button: 0,
      isPrimary: true,
      pointerId: 1,
      clientX: 5,
      clientY: 5,
    });
    fireEvent.pointerMove(document, { pointerId: 1, clientX: 5, clientY: 40 });

    // Drag actif = le DragOverlay rend une seconde carte du même projet.
    expect(screen.getAllByText('Projet Alpha')).toHaveLength(2);

    fireEvent.pointerUp(document, { pointerId: 1 });
  });

  it('démarre un drag au clavier depuis la carte focusée (Entrée)', async () => {
    renderKanban();

    const wrapper = getSortableWrapper('Projet Gamma');
    wrapper.focus();
    fireEvent.keyDown(wrapper, { code: 'Enter' });

    expect(screen.getAllByText('Projet Gamma')).toHaveLength(2);

    // Terminer proprement le drag, sinon son état pollue le test suivant.
    // Le KeyboardSensor attache son listener keydown au document dans un
    // setTimeout(0) : il faut laisser passer un tick avant d'annuler.
    await new Promise((resolve) => setTimeout(resolve, 0));
    fireEvent.keyDown(wrapper, { code: 'Escape' });
    await waitFor(() => expect(screen.getAllByText('Projet Gamma')).toHaveLength(1));
  });

  it('un clic simple sur le titre ouvre toujours le projet (pas de drag parasite)', () => {
    const { onSelect } = renderKanban();

    fireEvent.click(screen.getByText('Projet Alpha'));

    expect(onSelect).toHaveBeenCalledTimes(1);
    expect(onSelect.mock.calls[0][0].id).toBe('p-alpha');
  });
});
