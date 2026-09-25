/**
 * B-1383 (persona Nathalie, cycle 13) : après avoir déposé une carte au
 * clavier dans une autre colonne, le focus tombait sur `BODY`. Il fallait
 * repartir du haut de la page pour déplacer la carte suivante.
 *
 * Cause : dnd-kit rend le focus à la carte au moment du dépôt, mais la carte
 * change de colonne seulement quand le moteur a répondu ; elle est alors
 * rendue sous un autre parent, donc démontée puis remontée, et le focus part
 * avec l'ancien nœud. jsdom ne mesure aucun rectangle : le dépôt est simulé
 * en appelant le `onDragEnd` réel reçu par `DndContext`.
 */
import { act, render, screen } from '@testing-library/react';
import { useState } from 'react';
import { describe, expect, it, vi } from 'vitest';
import type { DragEndEvent } from '@dnd-kit/core';

import type { ContactResponse } from '../../services/api';

const capture: { onDragEnd?: (event: DragEndEvent) => void } = {};

vi.mock('@dnd-kit/core', async () => {
  const reel = await vi.importActual<typeof import('@dnd-kit/core')>('@dnd-kit/core');
  return {
    ...reel,
    DndContext: (props: Parameters<typeof reel.DndContext>[0]) => {
      capture.onDragEnd = props.onDragEnd;
      return <reel.DndContext {...props} />;
    },
  };
});

import { PipelineView } from './PipelineView';

function contact(patch: Partial<ContactResponse> = {}): ContactResponse {
  return {
    id: 'ct-1',
    first_name: 'Élodie',
    last_name: 'Martin',
    company: null,
    email: null,
    phone: null,
    address: null,
    notes: null,
    tags: null,
    stage: 'contact',
    score: 50,
    source: null,
    last_interaction: null,
    created_at: '2026-09-01T10:00:00Z',
    updated_at: '2026-09-01T10:00:00Z',
    ...patch,
  } as ContactResponse;
}

let resoudreLeMoteur: (() => void) | null = null;

function Harnais() {
  const [contacts, setContacts] = useState<ContactResponse[]>([
    contact(),
    contact({ id: 'ct-2', first_name: 'Karim', last_name: 'Benali' }),
  ]);
  return (
    <PipelineView
      contacts={contacts}
      onContactClick={() => {}}
      onStageChange={(id, stage) => {
        // Comme CRMPanel : la liste change quand le moteur a répondu.
        resoudreLeMoteur = () =>
          setContacts((liste) => liste.map((c) => (c.id === id ? { ...c, stage } : c)));
      }}
    />
  );
}

describe('B-1383 : le focus reste sur la carte déposée', () => {
  it('la carte déplacée dans une autre colonne reprend le focus', async () => {
    render(<Harnais />);
    const carte = screen.getByRole('button', { name: 'Élodie Martin' });
    carte.focus();

    act(() => {
      capture.onDragEnd?.({ active: { id: 'ct-1' }, over: { id: 'discovery' } } as unknown as DragEndEvent);
    });
    // Le nœud d'origine perd le focus quand la carte change de parent.
    await act(async () => {
      resoudreLeMoteur?.();
    });

    // L'ancienne carte peut rester montée le temps de sa sortie animée.
    const deplacee = screen.getAllByRole('button', { name: 'Élodie Martin' }).find((n) => n !== carte);
    expect(deplacee).toBeDefined();
    expect(document.activeElement).toBe(deplacee);
  });

  it("ne vole pas le focus s'il est ailleurs quand la liste change", async () => {
    render(
      <>
        <Harnais />
        <input aria-label="ailleurs" />
      </>,
    );
    screen.getByRole('button', { name: 'Élodie Martin' }).focus();
    act(() => {
      capture.onDragEnd?.({ active: { id: 'ct-1' }, over: { id: 'discovery' } } as unknown as DragEndEvent);
    });
    const ailleurs = screen.getByRole('textbox', { name: 'ailleurs' });
    ailleurs.focus();
    await act(async () => {
      resoudreLeMoteur?.();
    });

    expect(document.activeElement).toBe(ailleurs);
  });
});
