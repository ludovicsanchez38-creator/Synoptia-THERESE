/**
 * B-755 - Entrée sur le bouton d'une section doit sélectionner, pas glisser.
 *
 * Le `KeyboardSensor` écoute le keydown sur l'enveloppe `useSortable`. La
 * frappe partie du bouton enfant y remonte : sans `setActivatorNodeRef` posé
 * sur cette enveloppe, la garde native de dnd-kit ne reconnaît pas la cible
 * comme une commande interne, saisit la ligne et appelle `preventDefault()`.
 * C'est le même contrat utilisateur que B-750 sur TaskKanban et
 * ProjectsKanban.
 *
 * jsdom ne synthétise pas le clic produit par un navigateur après Entrée. Le
 * test le rejoue seulement si le keydown n'a pas été empêché, afin de mesurer
 * exactement la confiscation qui bloque l'utilisateur réel.
 */
import { act, fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

import type { DocumentSection } from '../../services/api/documents';
import { OutlineTree } from './OutlineTree';

const SECTION: DocumentSection = {
  id: 'section-clavier',
  document_id: 'document-1',
  title: 'Introduction',
  brief: '',
  order: 10,
  depth: 0,
  content: '',
  summary: '',
  status: 'vide',
  orphan: false,
  created_at: '2026-09-01T08:00:00Z',
  updated_at: '2026-09-01T08:00:00Z',
};

function monter() {
  const onSelect = vi.fn();
  render(
    <OutlineTree
      sections={[SECTION]}
      activeSectionId={null}
      isLoading={false}
      error={null}
      onSelect={onSelect}
      onReorder={vi.fn()}
      onCreateSection={vi.fn()}
      onGenerateOutline={vi.fn()}
    />,
  );
  return { onSelect };
}

function boutonDeSection(): HTMLElement {
  const bouton = screen.getByText(SECTION.title).closest('button');
  if (!(bouton instanceof HTMLElement)) throw new Error('bouton de section introuvable');
  return bouton;
}

describe('B-755 - Entrée sur une section active son bouton, sans glisser', () => {
  it('sélectionne la section et ne monte aucun DragOverlay', async () => {
    const { onSelect } = monter();
    const bouton = boutonDeSection();

    const nonEmpeche = fireEvent.keyDown(bouton, { key: 'Enter', code: 'Enter' });

    // Le défaut attendu a démarré un capteur asynchrone. On l'annule avant
    // l'assertion rouge afin de ne pas laisser de mise à jour React pendante.
    await act(async () => {
      await new Promise((resoudre) => setTimeout(resoudre, 0));
    });
    fireEvent.keyDown(bouton, { key: 'Escape', code: 'Escape' });
    await act(async () => {
      await new Promise((resoudre) => setTimeout(resoudre, 0));
    });

    expect(nonEmpeche).toBe(true);
    fireEvent.click(bouton);
    expect(onSelect).toHaveBeenCalledTimes(1);
    expect(onSelect).toHaveBeenCalledWith(SECTION.id);
    expect(screen.getAllByText(SECTION.title)).toHaveLength(1);
  });
});
