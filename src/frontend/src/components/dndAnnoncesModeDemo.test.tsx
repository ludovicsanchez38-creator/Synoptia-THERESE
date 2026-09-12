/**
 * B-754 - les annonces de glisser ne doivent pas contourner le mode démo.
 *
 * Les cartes visibles passent déjà par le masque sur plusieurs tableaux,
 * mais le callback `accessibility.announcements` de dnd-kit reconstruit son
 * libellé depuis les objets bruts. Un lecteur d'écran prononce alors le vrai
 * nom au moment où la carte est saisie, même si l'écran montre son alias.
 *
 * La garde pilote le vrai `KeyboardSensor` et lit la vraie région live de
 * dnd-kit : elle couvre donc la sortie effectivement servie aux technologies
 * d'assistance, pas seulement l'utilitaire de formatage isolé.
 */
import { act, cleanup, fireEvent, render, waitFor } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';

import type { Task } from '../services/api';
import { useDemoStore } from '../stores/demoStore';
import { useTaskStore } from '../stores/taskStore';
import { PipelineView } from './crm/PipelineView';
import { OutlineTree } from './documents/OutlineTree';
import { ProjectsKanban } from './memory/ProjectsKanban';
import { TaskKanban } from './tasks/TaskKanban';

const TACHE = {
  id: 'tache-demo', title: 'Relancer Ruiz', description: null, status: 'todo',
  priority: 'medium', due_date: null, project_id: null, contact_id: null, tags: [],
  created_at: '2026-09-01T08:00:00Z', updated_at: '2026-09-01T08:00:00Z',
} as unknown as Task;

type CasAnnonce = {
  tableau: string;
  monter: () => void;
};

const CAS: CasAnnonce[] = [
  {
    tableau: 'TaskKanban',
    monter: () => {
      useTaskStore.setState({
        tasks: [TACHE],
        searchQuery: '',
        currentTaskId: null,
        isTaskFormOpen: false,
      });
      render(<TaskKanban />);
    },
  },
  {
    tableau: 'ProjectsKanban',
    monter: () => {
      render(
        <ProjectsKanban
          projects={[{
            id: 'projet-demo', name: 'Chantier Ruiz', description: null, status: 'active',
            contact_id: null, budget: null, notes: null, tags: null,
            created_at: '2026-09-01', updated_at: '2026-09-01',
          } as never]}
          onSelect={vi.fn()}
          onDelete={vi.fn()}
          onStatusChange={vi.fn().mockResolvedValue(undefined)}
        />,
      );
    },
  },
  {
    tableau: 'PipelineView',
    monter: () => {
      render(
        <PipelineView
          contacts={[{
            id: 'contact-demo', first_name: 'Sophie', last_name: 'Ruiz', company: null,
            email: null, phone: null, address: null, notes: null, tags: [], stage: 'contact',
            score: 50, source: 'local', last_interaction: null,
            created_at: '2026-09-01', updated_at: '2026-09-01',
          } as never]}
          onContactClick={vi.fn()}
          onStageChange={vi.fn()}
        />,
      );
    },
  },
  {
    tableau: 'OutlineTree',
    monter: () => {
      render(
        <OutlineTree
          sections={[{
            id: 'section-demo', document_id: 'document-demo', title: 'Synthèse Ruiz',
            brief: '', content: '', summary: '', status: 'vide', order: 10,
            depth: 0, orphan: false,
            created_at: '2026-09-01', updated_at: '2026-09-01',
          } as never]}
          activeSectionId={null}
          isLoading={false}
          error={null}
          onSelect={vi.fn()}
          onReorder={vi.fn()}
          onCreateSection={vi.fn()}
          onGenerateOutline={vi.fn()}
        />,
      );
    },
  },
];

function premiereCarteSortable(): HTMLElement {
  const carte = document.querySelector('[aria-roledescription="sortable"]');
  if (!(carte instanceof HTMLElement)) throw new Error('carte sortable introuvable');
  return carte;
}

function annonceRendue(): string {
  return document.querySelector<HTMLElement>('[aria-live="assertive"]')?.textContent ?? '';
}

afterEach(() => {
  // Démonter avant de réinitialiser les stores : leurs abonnés React ne
  // doivent plus recevoir une mise à jour hors `act` entre deux cas.
  cleanup();
  useDemoStore.setState({ enabled: false, replacementMap: new Map() });
  useTaskStore.setState({ tasks: [], currentTaskId: null, isTaskFormOpen: false });
});

describe('B-754 - les annonces dnd-kit respectent le mode démo', () => {
  it.each(CAS)('$tableau ne prononce que le libellé masqué pendant le glisser', async ({ monter }) => {
    useDemoStore.setState({
      enabled: true,
      replacementMap: new Map([['Ruiz', 'Moreau']]),
    });
    monter();

    const carte = premiereCarteSortable();
    fireEvent.focus(carte);
    fireEvent.keyDown(carte, { key: 'Enter', code: 'Enter' });

    await waitFor(() => expect(annonceRendue()).not.toBe(''));
    const annonce = annonceRendue();

    // Fermer le capteur avant l'assertion rouge, pour qu'un échec ne laisse
    // aucun listener clavier actif au cas suivant.
    await act(async () => {
      await new Promise((resoudre) => setTimeout(resoudre, 0));
    });
    fireEvent.keyDown(carte, { key: 'Escape', code: 'Escape' });
    await act(async () => {
      await new Promise((resoudre) => setTimeout(resoudre, 0));
    });

    expect(annonce).not.toContain('Ruiz');
    expect(annonce).toContain('Moreau');
  });
});
