/**
 * B-1398 (persona Zoé, cycle 13) : chaque carte de projet était un bouton sans
 * nom (le conteneur déplaçable de dnd-kit, `role="button"`), contenant deux
 * autres boutons. Comme les cartes du Pipeline (B-877), le conteneur porte le
 * nom de l'objet.
 */
import { render, screen } from '@testing-library/react';
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


describe('B-1398 : la carte de projet a un nom', () => {
  it('le conteneur déplaçable porte le nom du projet', () => {
    render(
      <ProjectsKanban
        projects={[makeProject({ id: 'p-veille', name: 'Veille IA', status: 'active' })]}
        onSelect={vi.fn()} onDelete={vi.fn()} onStatusChange={vi.fn().mockResolvedValue(undefined)}
      />,
    );
    const carte = document.querySelector('[aria-roledescription]') as HTMLElement;
    expect(carte).not.toBeNull();
    expect(carte.getAttribute('aria-label')).toBe('Veille IA');
    expect(screen.getAllByRole('button').filter((b) => !(b.getAttribute('aria-label') || b.textContent?.trim()))).toHaveLength(0);
  });
});
