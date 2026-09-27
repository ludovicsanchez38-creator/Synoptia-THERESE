/**
 * P-148 : la promesse de l'état vide devient exacte et complète. La fenêtre
 * d'un projet montre désormais ses conversations, documents, tâches et
 * contacts : c'est ce que la phrase annonce.
 */
import { cleanup, fireEvent, render, screen } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';

const api = vi.hoisted(() => ({ listProjects: vi.fn(), deleteProject: vi.fn() }));
vi.mock('../../services/api', () => api);
vi.mock('./ProjectModal', () => ({
  ProjectModal: ({ isOpen, onClose }: { isOpen: boolean; onClose: () => void }) =>
    isOpen ? <div role="dialog" aria-label="Nouveau projet"><button onClick={onClose}>Fermer</button></div> : null,
}));

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

  it('B-1727 : les deux boutons homonymes ont une identité distincte et ouvrent la même fenêtre', async () => {
    api.listProjects.mockResolvedValue([]);
    render(<ProjectsPanel />);
    const entete = await screen.findByTestId('nouveau-projet-entete');
    const vide = screen.getByTestId('nouveau-projet-etat-vide');
    expect(entete).toHaveAccessibleName('Nouveau projet');
    expect(vide).toHaveAccessibleName('Nouveau projet');
    fireEvent.click(entete);
    expect(screen.getByRole('dialog', { name: 'Nouveau projet' })).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: 'Fermer' }));
    fireEvent.click(vide);
    expect(screen.getByRole('dialog', { name: 'Nouveau projet' })).toBeInTheDocument();
  });
});
