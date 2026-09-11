/**
 * DA « Application affinée », lot 6 : l'écran Projets
 * (`docs/plans/2026-09-11-da-lot6-projets-design.md`, § 6, § 8 et § 9).
 */
import { readFileSync } from 'node:fs';
import { join } from 'node:path';

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

vi.mock('./ProjectsKanban', () => ({ ProjectsKanban: () => <div data-testid="kanban" /> }));
vi.mock('./ProjectModal', () => ({ ProjectModal: () => <div data-testid="project-modal" /> }));

import { ProjectsPanel } from './ProjectsPanel';

const SOURCE = readFileSync(join(__dirname, 'ProjectsPanel.tsx'), 'utf-8');

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

function dansUnSousArbreMuet(noeud: Element | null): boolean {
  let courant: Element | null = noeud;
  while (courant) {
    if (courant.getAttribute('aria-hidden') === 'true') return true;
    courant = courant.parentElement;
  }
  return false;
}

function rangeesSquelette(racine: HTMLElement): Element[] {
  return Array.from(racine.querySelectorAll('div[aria-hidden="true"]')).filter((n) => {
    const c = typeof n.className === 'string' ? n.className : '';
    return /\bgap-3\b/.test(c) && /\bitems-center\b/.test(c);
  });
}

beforeEach(() => {
  vi.clearAllMocks();
  mockListProjects.mockResolvedValue(projets(3));
});

describe('Lot 6 DA : en-tête de ProjectsPanel', () => {
  it('le compteur reste exact sous le plafond et se marque au plafond', async () => {
    mockListProjects.mockResolvedValue(projets(199));
    const { unmount } = render(<ProjectsPanel />);
    await screen.findByTestId('kanban');
    await waitFor(() => expect(screen.getByText('199 projets')).toBeInTheDocument());
    expect(screen.queryByRole('alert')).toBeNull();
    unmount();

    mockListProjects.mockResolvedValue(projets(200));
    render(<ProjectsPanel />);
    await screen.findByTestId('kanban');
    expect(await screen.findByRole('alert')).toHaveTextContent(/Liste incomplète/i);
    expect(screen.queryByText('200 projets')).toBeNull();
  });

  it('« Nouveau projet » est un geste de 36 px, et aucun overlay n’est en bg-black', async () => {
    render(<ProjectsPanel />);
    const geste = await screen.findByRole('button', { name: /Nouveau projet/ });
    expect(geste.className).toMatch(/\bh-9\b/);
    expect(SOURCE).not.toMatch(/bg-black\//);
    expect(SOURCE).not.toMatch(/size="sm"/);
  });
});

describe('Lot 6 DA : les états de ProjectsPanel', () => {
  it('la panne montre un seul « Réessayer », le reste zéro', async () => {
    mockListProjects.mockRejectedValueOnce(new Error('panne'));
    const { unmount } = render(<ProjectsPanel />);
    expect(await screen.findByRole('alert')).toHaveTextContent('Impossible de charger les projets.');
    expect(screen.getAllByRole('button', { name: 'Réessayer' })).toHaveLength(1);
    unmount();

    mockListProjects.mockResolvedValue(projets(3));
    render(<ProjectsPanel />);
    await screen.findByTestId('kanban');
    expect(screen.queryByRole('button', { name: 'Réessayer' })).toBeNull();
  });

  it('sans projet, un état vide nommé, et le kanban n’est pas monté', async () => {
    mockListProjects.mockResolvedValue([]);
    render(<ProjectsPanel />);

    expect(
      await screen.findByRole('heading', { level: 3, name: 'Aucun projet' }),
    ).toBeInTheDocument();
    expect(screen.queryByTestId('kanban')).toBeNull();
    expect(screen.queryByRole('button', { name: 'Réessayer' })).toBeNull();
  });

  it('au chargement, l’attente s’annonce et les squelettes restent muets', () => {
    mockListProjects.mockImplementation(() => new Promise(() => {}));
    const { container } = render(<ProjectsPanel />);

    const annonce = screen.getByRole('status');
    expect(annonce).toHaveTextContent('Chargement des projets…');
    expect(annonce).not.toHaveAttribute('aria-hidden', 'true');
    expect(dansUnSousArbreMuet(annonce.parentElement)).toBe(false);
    expect(rangeesSquelette(container)).toHaveLength(3);
  });
});
