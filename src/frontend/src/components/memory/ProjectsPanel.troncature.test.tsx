/**
 * B-098 : le plafond de 200 projets était présenté comme un total.
 *
 * `listProjects(0, 200)` demande exactement le maximum que l'API accepte
 * (`limit` est borné à 200 côté serveur : 201 est refusé en 422). L'écran
 * affichait ensuite `projects.length` en clair, « 200 projets », sans aucun
 * signal de troncature. Or à ce plafond l'écran ne PEUT pas connaître le
 * nombre réel : il ne lui reste qu'à le dire.
 *
 * Le motif existe déjà deux fois à côté : les contacts (`PLAFOND_CONTACTS` et
 * son bandeau « Liste incomplète ») et les fichiers de projet.
 */
import { render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import type { Project } from '../../services/api';

const mockListProjects = vi.fn();

vi.mock('../../services/api', async () => {
  const actual = await vi.importActual<typeof import('../../services/api')>('../../services/api');
  return {
    ...actual,
    listProjects: (...args: unknown[]) => mockListProjects(...args),
    deleteProject: vi.fn(),
    updateProject: vi.fn(),
  };
});

// Le kanban et la modale ne sont pas le sujet : on les remplace pour que le
// seul role="alert" observable soit celui du bandeau de troncature.
vi.mock('./ProjectsKanban', () => ({ ProjectsKanban: () => <div data-testid="kanban" /> }));
vi.mock('./ProjectModal', () => ({ ProjectModal: () => <div data-testid="project-modal" /> }));

import { ProjectsPanel } from './ProjectsPanel';

function projets(nombre: number): Project[] {
  return Array.from({ length: nombre }, (_, i) => ({
    id: `p-${i}`,
    name: `Projet ${i}`,
    description: null,
    status: 'active',
    created_at: '2026-08-01T00:00:00Z',
    updated_at: '2026-08-01T00:00:00Z',
  })) as unknown as Project[];
}

describe('B-098 : au plafond, la liste des projets dit qu’elle est incomplète', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('signale la troncature quand le plafond de 200 est atteint', async () => {
    mockListProjects.mockResolvedValue(projets(200));
    render(<ProjectsPanel />);

    await screen.findByTestId('kanban');
    const bandeau = await screen.findByRole('alert');
    expect(bandeau).toHaveTextContent(/Liste incomplète/i);

    // Et le compte cesse de se présenter comme un total.
    expect(screen.queryByText('200 projets')).not.toBeInTheDocument();
  });

  it('ne dit rien de tel sous le plafond', async () => {
    mockListProjects.mockResolvedValue(projets(199));
    render(<ProjectsPanel />);

    await screen.findByTestId('kanban');
    await waitFor(() => {
      expect(screen.getByText('199 projets')).toBeInTheDocument();
    });
    expect(screen.queryByRole('alert')).not.toBeInTheDocument();
  });
});
