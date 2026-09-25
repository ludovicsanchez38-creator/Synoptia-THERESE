/**
 * P-123 (persona Hugo, cycle 13) : trois projets créés avec des tags
 * (« asso, web », « orion, api », « veille ») ; aucune carte ne les affichait
 * et la liste ne se filtrait pas. Avec quinze projets, c'est une liste qu'on
 * ne peut plus parcourir.
 */
import { fireEvent, render, screen, within } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import type { Project } from '../../services/api';

const mockListProjects = vi.fn();
vi.mock('../../services/api', async () => {
  const actual = await vi.importActual<typeof import('../../services/api')>('../../services/api');
  return { ...actual, listProjects: (...args: unknown[]) => mockListProjects(...args), deleteProject: vi.fn(), updateProject: vi.fn() };
});
vi.mock('./ProjectModal', () => ({ ProjectModal: () => null }));

import { ProjectsPanel } from './ProjectsPanel';

function projet(id: string, name: string, tags: string[] | null, description: string | null = null): Project {
  return {
    id, name, description, contact_id: null, status: 'active', budget: null, notes: null, tags,
    created_at: '2026-09-01T00:00:00Z', updated_at: '2026-09-01T00:00:00Z',
  } as Project;
}

describe('P-123 : tags visibles et liste filtrable', () => {
  beforeEach(() => {
    mockListProjects.mockResolvedValue([
      projet('p1', 'Site de l’association', ['asso', 'web']),
      projet('p2', 'API client Orion', ['orion', 'api'], 'Intégration du flux de commandes'),
      projet('p3', 'Veille IA', ['veille']),
    ]);
  });

  it('chaque carte montre ses tags', async () => {
    render(<ProjectsPanel />);
    const carte = (await screen.findByText('API client Orion')).closest('.group') as HTMLElement;
    expect(within(carte).getByText('orion')).toBeInTheDocument();
    expect(within(carte).getByText('api')).toBeInTheDocument();
  });

  it('le filtre porte sur le nom, la description et les tags, sans tenir compte des accents', async () => {
    render(<ProjectsPanel />);
    await screen.findByText('Veille IA');
    const filtre = screen.getByRole('searchbox', { name: 'Filtrer les projets' });

    fireEvent.change(filtre, { target: { value: 'web' } });
    expect(screen.getByText('Site de l’association')).toBeInTheDocument();
    expect(screen.queryByText('Veille IA')).toBeNull();

    fireEvent.change(filtre, { target: { value: 'COMMANDES' } });
    expect(screen.getByText('API client Orion')).toBeInTheDocument();
    expect(screen.queryByText('Site de l’association')).toBeNull();

    fireEvent.change(filtre, { target: { value: 'veillé' } });
    expect(screen.getByText('Veille IA')).toBeInTheDocument();
  });

  it('un filtre sans résultat le dit et se lève', async () => {
    render(<ProjectsPanel />);
    await screen.findByText('Veille IA');
    fireEvent.change(screen.getByRole('searchbox', { name: 'Filtrer les projets' }), { target: { value: 'zorro' } });
    expect(screen.getByText('Aucun projet ne correspond à « zorro ».')).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: 'Effacer le filtre' }));
    expect(screen.getByText('Veille IA')).toBeInTheDocument();
  });
});
