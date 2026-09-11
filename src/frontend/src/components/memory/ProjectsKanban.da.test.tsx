/**
 * DA « Application affinée », lot 6 : les groupes du kanban des projets
 * (`docs/plans/2026-09-11-da-lot6-projets-design.md`, § 7 et § 9).
 */
import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

import type { Project } from '../../services/api';
import { ProjectsKanban } from './ProjectsKanban';

const ALPHA: Project = {
  id: 'p-1',
  name: 'Projet Alpha',
  status: 'active',
  description: 'Aménagement de l’accueil',
  contact_id: null,
  budget: null,
  notes: null,
  tags: null,
  created_at: '2026-06-01T00:00:00Z',
  updated_at: '2026-06-01T00:00:00Z',
};

const LIBELLES = ['Actif', 'En attente', 'Terminé', 'Annulé'];

function monter(projects: Project[] = [ALPHA]) {
  const onSelect = vi.fn();
  const onDelete = vi.fn();
  const rendu = render(
    <ProjectsKanban
      projects={projects}
      onSelect={onSelect}
      onDelete={onDelete}
      onStatusChange={vi.fn().mockResolvedValue(undefined)}
    />,
  );
  return { ...rendu, onSelect, onDelete };
}

describe('Lot 6 DA : les têtes des quatre groupes', () => {
  it('chaque libellé est une Etiquette en casse de phrase, sans couleur d’agent', () => {
    monter();

    for (const libelle of LIBELLES) {
      const etiquette = screen.getByText(libelle);
      expect(etiquette, libelle).toHaveAttribute('data-etiquette');
      expect(etiquette.className, libelle).not.toMatch(/\buppercase\b/);
      const tete = etiquette.parentElement as HTMLElement;
      expect(tete.className, libelle).not.toMatch(/bg-agent-/);
      expect(tete.className, libelle).not.toMatch(/text-agent-/);
    }
  });

  it('le compte est nu, sans parenthèses', () => {
    monter();

    const tete = (screen.getByText('Actif').parentElement) as HTMLElement;
    expect(tete.textContent).not.toMatch(/[()]/);
    expect(tete.textContent).toContain('1');
    const compte = Array.from(tete.querySelectorAll('span')).find((s) => s.textContent === '1');
    expect(compte?.className).toMatch(/\btabular-nums\b/);
    expect(compte?.className).toMatch(/\btext-sm\b/);
  });
});

describe('Lot 6 DA : la carte de projet', () => {
  it('un clic sur le nom ouvre toujours le projet', () => {
    const { onSelect } = monter();

    fireEvent.click(screen.getByText('Projet Alpha'));
    expect(onSelect).toHaveBeenCalledTimes(1);
    expect(onSelect.mock.calls[0][0].id).toBe('p-1');
  });

  it('la corbeille se révèle au survol ET au focus, depuis une carte qui est un group', () => {
    monter();

    const supprimer = screen.getByRole('button', { name: 'Supprimer Projet Alpha' });
    const enveloppe = supprimer.parentElement as HTMLElement;
    expect(enveloppe.className).toMatch(/\bopacity-0\b/);
    expect(enveloppe.className).toMatch(/group-hover:opacity-100/);
    expect(enveloppe.className).toMatch(/group-focus-within:opacity-100/);

    const carte = supprimer.closest('[class~="group"]');
    expect(carte).not.toBeNull();
  });

  it('la description vit à 14 px, pas au plancher des métadonnées', () => {
    monter();
    expect(screen.getByText('Aménagement de l’accueil').className).toMatch(/\btext-sm\b/);
  });
});

describe('Lot 6 DA : filet du kanban monté à vide', () => {
  it('rend un état vide nommé, sans geste', () => {
    monter([]);

    expect(screen.getByRole('heading', { level: 3, name: 'Aucun projet' })).toBeInTheDocument();
    expect(screen.queryByRole('button')).toBeNull();
  });
});
