/**
 * B-1491 : ouverte depuis la vue Projets, la fenêtre d'un projet se fermait à
 * Échap sans poser « Abandonner les modifications ? » (B-1392). La vue
 * empilait son propre gestionnaire d'Échap après celui de la fenêtre (l'effet
 * du parent passe après celui de l'enfant) : seul le dernier inscrit agit.
 */
import { act, cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import type { Project } from '../../services/api';

const api = vi.hoisted(() => ({
  listProjects: vi.fn(), deleteProject: vi.fn(),
  listContacts: vi.fn(), listProjectFiles: vi.fn(), etatSync: vi.fn(),
  updateProject: vi.fn(), createProject: vi.fn(), deleteFile: vi.fn(), uploadProjectFile: vi.fn(),
  definirRacineSync: vi.fn(), retirerRacineSync: vi.fn(),
  preparerPlanSync: vi.fn(), appliquerPlanSync: vi.fn(), journalSync: vi.fn(),
}));
vi.mock('../../services/api', () => api);
vi.mock('../../services/api/crm-extended', async (importOriginal) => ({
  ...(await importOriginal<object>()),
  listDeliverables: vi.fn().mockResolvedValue([]),
  createDeliverable: vi.fn(),
}));

import { _clearEscapeHandlers, runTopEscapeHandler } from '../../lib/escapeStack';
import { ProjectsPanel } from './ProjectsPanel';

const PROJET: Project = {
  id: 'projet-b1491', name: 'Cuisine Roux', description: null, contact_id: null, status: 'active',
  budget: null, notes: null, tags: null, created_at: '2026-09-23T10:00:00Z', updated_at: '2026-09-23T10:00:00Z',
};
const QUESTION = 'Abandonner les modifications ?';

async function ouvrirLaFenetre() {
  render(<ProjectsPanel />);
  fireEvent.click(await screen.findByText(PROJET.name));
  return screen.findByLabelText(/Nom du projet/);
}

describe('B-1491 : Échap dans la fenêtre projet ouverte depuis la vue Projets', () => {
  beforeEach(() => {
    _clearEscapeHandlers();
    Object.values(api).forEach((mock) => mock.mockReset());
    api.listProjects.mockResolvedValue([PROJET]);
    api.listContacts.mockResolvedValue([]);
    api.listProjectFiles.mockResolvedValue({ files: [], truncated: false });
    api.etatSync.mockResolvedValue(null);
  });
  afterEach(() => { cleanup(); _clearEscapeHandlers(); });

  it('une saisie modifiée pose la question au lieu de fermer', async () => {
    const champ = await ouvrirLaFenetre();
    fireEvent.change(champ, { target: { value: 'Cuisine Roux et fils' } });

    act(() => { runTopEscapeHandler(); });

    expect(screen.getByText(QUESTION)).toBeInTheDocument();
    expect(screen.getByLabelText(/Nom du projet/)).toHaveValue('Cuisine Roux et fils');
  });

  it('une saisie intacte se ferme à Échap, sans laisser la touche à la vue du dessous', async () => {
    await ouvrirLaFenetre();
    let consomme = false;
    act(() => { consomme = runTopEscapeHandler(); });

    expect(consomme).toBe(true);
    await waitFor(() => expect(screen.queryByLabelText(/Nom du projet/)).toBeNull());
    expect(screen.queryByText(QUESTION)).toBeNull();
  });
});
