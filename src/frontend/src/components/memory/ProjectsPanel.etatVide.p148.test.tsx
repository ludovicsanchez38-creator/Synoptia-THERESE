/**
 * P-148 : la promesse de l'état vide devient exacte et complète. La fenêtre
 * d'un projet montre désormais ses conversations, documents, tâches et
 * contacts : c'est ce que la phrase annonce.
 */
import { cleanup, render, screen } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';

const api = vi.hoisted(() => ({ listProjects: vi.fn(), deleteProject: vi.fn() }));
vi.mock('../../services/api', () => api);
vi.mock('./ProjectModal', () => ({ ProjectModal: () => null }));

import { ProjectsPanel } from './ProjectsPanel';

describe('P-148 : l’état vide de la vue Projets', () => {
  afterEach(() => cleanup());

  it('annonce les quatre familles que la fenêtre du projet rassemble', async () => {
    api.listProjects.mockResolvedValue([]);
    render(<ProjectsPanel />);
    expect(await screen.findByText(
      'Crée ton premier projet pour rassembler les conversations, documents, tâches et contacts d’une même affaire.',
    )).toBeInTheDocument();
  });
});
