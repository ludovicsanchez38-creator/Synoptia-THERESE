/** P-148, lot 5 : `openEditProject`, jumeau de `openEditContact`, pose le projet et ouvre sa fenêtre. */
import { beforeEach, describe, expect, it } from 'vitest';
import type { Project } from '../services/api';
import { usePanelStore } from './panelStore';

const PROJET: Project = {
  id: 'p-cuisine', name: 'Cuisine Roux', description: null, contact_id: null, status: 'active',
  budget: null, notes: null, tags: null, created_at: '2026-09-20T10:00:00Z', updated_at: '2026-09-20T10:00:00Z',
};

describe('P-148 : openEditProject', () => {
  beforeEach(() => { usePanelStore.setState({ showProjectModal: false, editingProject: null }); });

  it('pose le projet et ouvre la fenêtre ; la fermer les retire', () => {
    usePanelStore.getState().openEditProject(PROJET);
    expect(usePanelStore.getState().editingProject).toEqual(PROJET);
    expect(usePanelStore.getState().showProjectModal).toBe(true);

    usePanelStore.getState().closeProjectModal();
    expect(usePanelStore.getState().editingProject).toBeNull();
    expect(usePanelStore.getState().showProjectModal).toBe(false);
  });
});
