/**
 * B-237 : le pipeline promettait un glissé au clavier qu'il ne tenait pas.
 *
 * Trois moitiés, toutes mesurées ici :
 *
 * 1. `useSensor(KeyboardSensor)` sans second argument. Le `coordinateGetter`
 *    par défaut de @dnd-kit/core déplace le pointeur virtuel de 25 px par
 *    flèche, dans des colonnes larges de 288 px (`w-72`) : douze appuis avant
 *    le moindre recouvrement, donc la carte reste au-dessus d'elle-même et
 *    aucune cible n'est jamais annoncée. `sortableKeyboardCoordinates` saute
 *    de conteneur en conteneur, c'est le getter prévu par @dnd-kit/sortable.
 *    jsdom ne peut pas mesurer le déplacement (tous ses rectangles valent
 *    zéro) : le test porte donc sur le CÂBLAGE réel du capteur, pas sur une
 *    lecture du fichier source.
 *
 * 2. Les consignes lues par un lecteur d'écran étaient les consignes ANGLAISES
 *    par défaut de dnd-kit, dans une application française.
 *
 * 3. Échap pendant un glissé fermait la vue CRM entière : la cascade de la
 *    coque descend jusqu'à `collapseEmbeddedView()` sans jamais consulter un
 *    glissé actif. Le pipeline s'inscrit désormais dans la pile Échap tant
 *    qu'une carte est saisie — et s'en retire à l'annulation, sans quoi tous
 *    les Échap suivants seraient avalés.
 */
import { act, fireEvent, render, screen } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { KeyboardSensor, useSensor } from '@dnd-kit/core';
import { sortableKeyboardCoordinates } from '@dnd-kit/sortable';

import { _clearEscapeHandlers, runTopEscapeHandler } from '../../lib/escapeStack';
import type { ContactResponse } from '../../services/api';

vi.mock('@dnd-kit/core', async () => {
  const reel = await vi.importActual<typeof import('@dnd-kit/core')>('@dnd-kit/core');
  return { ...reel, useSensor: vi.fn(reel.useSensor) };
});

import { PipelineView } from './PipelineView';

function contact(patch: Partial<ContactResponse> = {}): ContactResponse {
  return {
    id: 'ct-1',
    first_name: 'Sophie',
    last_name: 'Durand',
    company: null,
    email: null,
    phone: null,
    address: null,
    notes: null,
    tags: null,
    stage: 'discovery',
    score: 0,
    source: 'site-web',
    last_interaction: null,
    created_at: '2026-09-01T10:00:00Z',
    updated_at: '2026-09-01T10:00:00Z',
    ...patch,
  } as ContactResponse;
}

describe('B-237 : le pipeline se pilote au clavier, en français', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    _clearEscapeHandlers();
  });

  afterEach(() => {
    _clearEscapeHandlers();
  });

  it('le KeyboardSensor reçoit sortableKeyboardCoordinates', () => {
    render(<PipelineView contacts={[contact()]} onContactClick={() => {}} onStageChange={() => {}} />);

    expect(useSensor).toHaveBeenCalledWith(
      KeyboardSensor,
      expect.objectContaining({ coordinateGetter: sortableKeyboardCoordinates }),
    );
  });

  it('les consignes lues à la saisie sont en français', () => {
    render(<PipelineView contacts={[contact()]} onContactClick={() => {}} onStageChange={() => {}} />);

    const carte = screen.getByRole('button', { name: /Sophie Durand/i });
    const consigne =
      document.getElementById(carte.getAttribute('aria-describedby') || '')?.textContent || '';

    expect(consigne).not.toMatch(/press the space bar/i);
    expect(consigne).toMatch(/barre d[’']espace/i);
  });

  it("Échap pendant un glissé est consommé par le pipeline, puis rendu à la coque", async () => {
    render(<PipelineView contacts={[contact()]} onContactClick={() => {}} onStageChange={() => {}} />);

    // Au repos, le pipeline ne réclame rien : Échap appartient à la coque.
    expect(runTopEscapeHandler()).toBe(false);

    const carte = screen.getByRole('button', { name: /Sophie Durand/i });
    carte.focus();
    fireEvent.keyDown(carte, { key: ' ', code: 'Space' });

    // dnd-kit n'attache son écouteur clavier qu'au tour de boucle suivant
    // (`setTimeout` dans KeyboardSensor.attach) : sans cette attente, Échap ne
    // serait consulté par personne et le test mesurerait autre chose.
    await act(async () => {
      await new Promise((resoudre) => setTimeout(resoudre, 0));
    });

    // Glissé actif : la pile Échap a un preneur, la vue CRM ne se ferme donc pas.
    expect(runTopEscapeHandler()).toBe(true);

    // Et l'annulation le retire : sans cela, tous les Échap suivants seraient
    // avalés et plus rien ne fermerait la vue.
    fireEvent.keyDown(carte, { key: 'Escape', code: 'Escape' });
    expect(runTopEscapeHandler()).toBe(false);
  });
});
