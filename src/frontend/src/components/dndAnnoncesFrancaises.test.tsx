/**
 * B-217 - les tableaux glisser-déposer annoncent en français, par les noms.
 *
 * Aucun des quatre `DndContext` (Tâches, Projets, Pipeline, Trame de
 * document) ne fournissait `accessibility` : @dnd-kit servait ses textes
 * anglais par défaut - « To pick up a draggable item, press the space bar… » -
 * et ses annonces désignaient l'objet déplacé par son identifiant technique
 * (« Draggable item 3f2a-… was dropped over droppable area done »). Dans une
 * application française, un UUID lu à voix haute ne désigne rien.
 *
 * Deux mesures : le texte réellement rendu dans l'élément que chaque carte
 * désigne par `aria-describedby` (le seul endroit où l'on voit ce que
 * @dnd-kit sert vraiment), et les annonces elles-mêmes, qui doivent nommer
 * l'objet et sa cible.
 */
import { render } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

import type { Task } from '../services/api';
import { annoncesGlisserDeposer } from '../lib/accessibiliteGlisserDeposer';
import { useTaskStore } from '../stores/taskStore';
import { TaskKanban } from './tasks/TaskKanban';
import { ProjectsKanban } from './memory/ProjectsKanban';
import { PipelineView } from './crm/PipelineView';
import { OutlineTree } from './documents/OutlineTree';

vi.mock('../services/api', async () => {
  const actual = await vi.importActual<Record<string, unknown>>('../services/api');
  return { ...actual, updateTask: vi.fn().mockResolvedValue({}) };
});

const TACHE = {
  id: 'tache-1', title: 'Relancer Sophie Moreau', description: null, status: 'todo',
  priority: 'medium', due_date: null, project_id: null, contact_id: null, tags: [],
  created_at: '2026-09-01T08:00:00Z', updated_at: '2026-09-01T08:00:00Z',
} as unknown as Task;

/** Le texte que @dnd-kit sert aux technologies d'assistance. */
function instructionsRendues(): string {
  const carte = document.querySelector('[aria-describedby]');
  if (!carte) throw new Error('aucune carte déplaçable rendue');
  const id = carte.getAttribute('aria-describedby') as string;
  const element = document.getElementById(id);
  if (!element) throw new Error(`élément ${id} introuvable`);
  return element.textContent || '';
}

const TABLEAUX: [string, () => void][] = [
  ['Tâches', () => {
    useTaskStore.setState({ tasks: [TACHE], searchQuery: '', currentTaskId: null, isTaskFormOpen: false });
    render(<TaskKanban />);
  }],
  ['Projets', () => {
    render(
      <ProjectsKanban
        projects={[{
          id: 'projet-1', name: 'Refonte du site', description: null, status: 'active',
          contact_id: null, created_at: '2026-09-01', updated_at: '2026-09-01',
        } as never]}
        onSelect={vi.fn()}
        onDelete={vi.fn()}
        onStatusChange={vi.fn()}
      />,
    );
  }],
  ['Pipeline', () => {
    render(
      <PipelineView
        contacts={[{
          id: 'contact-1', first_name: 'Sophie', last_name: 'Moreau', company: null,
          email: null, phone: null, address: null, notes: null, tags: [], stage: 'contact',
          score: 50, source: 'local', last_interaction: null,
          created_at: '2026-09-01', updated_at: '2026-09-01',
        } as never]}
        onContactClick={vi.fn()}
        onStageChange={vi.fn()}
      />,
    );
  }],
  ['Trame', () => {
    render(
      <OutlineTree
        sections={[{
          id: 'section-1', document_id: 'doc-1', title: 'Introduction', brief: null,
          content: null, status: 'vide', position: 0, depth: 0, orphan: false,
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
  }],
];

describe('B-217 - les tableaux glisser-déposer parlent français', () => {
  it.each(TABLEAUX)('%s : les instructions rendues sont en français', (_nom, monter) => {
    monter();

    const texte = instructionsRendues();
    expect(texte).toMatch(/barre d’espace|barre d'espace/);
    expect(texte).not.toMatch(/press the space bar/i);
  });
});

describe('B-217 - les annonces nomment l’objet, pas son identifiant', () => {
  const libelle = (id: unknown) =>
    ({ 'tache-1': 'Relancer Sophie Moreau', done: 'Terminé' })[String(id)] ?? null;

  it('la saisie et le dépôt citent les noms', () => {
    const annonces = annoncesGlisserDeposer(libelle);
    const active = { id: 'tache-1' } as never;
    const over = { id: 'done' } as never;

    expect(annonces.onDragStart({ active })).toContain('Relancer Sophie Moreau');
    expect(annonces.onDragEnd({ active, over })).toContain('Terminé');
    expect(annonces.onDragEnd({ active, over })).not.toContain('tache-1');
  });

  it('un identifiant inconnu ne fuit pas à l’oreille', () => {
    const annonces = annoncesGlisserDeposer(() => null);
    const active = { id: '3f2a-8b71-inconnu' } as never;

    expect(annonces.onDragStart({ active })).not.toContain('3f2a');
  });
});
