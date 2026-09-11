/**
 * B-752 - en mode démo, le kanban des projets montrait les vrais noms.
 *
 * `ProjectsPanel` passe les projets BRUTS (`ProjectsPanel.tsx`, rendu de
 * `<ProjectsKanban projects={projects} …/>`) : rien dans la chaîne n'appelle
 * `useDemoMask`. `ProjectCard` rendait donc `{project.name}` tel quel, et
 * l'`aria-label` de la corbeille interpolait lui aussi le vrai nom - masqué à
 * l'œil nulle part, et nu à l'oreille. Même défaut que celui réparé pour
 * `TaskList` (D105 et D106) : une démonstration chez un prospect exposait le
 * nom du dossier d'un autre client.
 */

import { fireEvent, render, screen } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { ProjectsKanban } from './ProjectsKanban';
import { useDemoStore } from '../../stores/demoStore';
import type { Project } from '../../services/api';

const PROJET: Project = {
  id: 'p-alpha',
  name: 'Chantier Ruiz',
  status: 'active',
  description: 'Devis à relancer pour Ruiz',
  contact_id: null,
  budget: null,
  notes: null,
  tags: null,
  created_at: '2026-06-01T00:00:00Z',
  updated_at: '2026-06-01T00:00:00Z',
};

function monter() {
  const onDelete = vi.fn();
  render(
    <ProjectsKanban
      projects={[PROJET]}
      onSelect={vi.fn()}
      onDelete={onDelete}
      onStatusChange={vi.fn().mockResolvedValue(undefined)}
    />
  );
  return { onDelete };
}

afterEach(() => {
  // Le store démo est un singleton de module : sans remise à zéro, le masque
  // déborderait sur les fichiers voisins.
  useDemoStore.setState({ enabled: false, replacementMap: new Map() });
});

describe('B-752 - le kanban des projets masque les noms en mode démo', () => {
  it('le nom visible, sa description et le nom de la corbeille passent par le masque', () => {
    useDemoStore.setState({
      enabled: true,
      replacementMap: new Map([['Chantier Ruiz', 'Chantier Moreau'], ['Ruiz', 'Moreau']]),
    });
    const { onDelete } = monter();

    expect(screen.getByText('Chantier Moreau')).toBeInTheDocument();
    expect(screen.getByText('Devis à relancer pour Moreau')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Supprimer Chantier Moreau' })).toBeInTheDocument();

    // Le vrai nom ne sort ni par le texte, ni par un nom accessible.
    expect(screen.queryAllByText(/Ruiz/)).toEqual([]);
    expect(screen.queryAllByRole('button', { name: /Ruiz/ })).toEqual([]);

    // La commande masquée reste la commande du BON projet.
    fireEvent.click(screen.getByRole('button', { name: 'Supprimer Chantier Moreau' }));
    expect(onDelete).toHaveBeenCalledTimes(1);
    expect(onDelete.mock.calls[0][0].id).toBe(PROJET.id);
  });

  it('hors mode démo, le vrai nom reste affiché tel quel', () => {
    monter();

    expect(screen.getByText('Chantier Ruiz')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Supprimer Chantier Ruiz' })).toBeInTheDocument();
  });
});
