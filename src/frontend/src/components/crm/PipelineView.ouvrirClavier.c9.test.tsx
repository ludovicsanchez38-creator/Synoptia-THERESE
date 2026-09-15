/**
 * B-877 (cycle 9, relecteur U2) : dans le pipeline, l'ouverture d'une fiche
 * tenait à un `onClick` sur un div intérieur non focusable, sous un conteneur
 * dnd-kit qui réserve Entrée et Espace au glisser : aucune fiche ne s'ouvrait
 * au clavier.
 */
import { fireEvent, render, screen } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { _clearEscapeHandlers } from '../../lib/escapeStack';
import type { ContactResponse } from '../../services/api';
import { PipelineView } from './PipelineView';

const contact = {
  id: 'ct-1', first_name: 'Alain', last_name: 'Moreau', company: 'Moreau SARL', email: 'alain@moreau.test', phone: null,
  address: null, notes: null, tags: null, stage: 'contact', score: 145, source: 'site-web', last_interaction: null,
  created_at: '2026-08-28T10:00:00Z', updated_at: '2026-08-28T10:00:00Z',
} as ContactResponse;

beforeEach(() => _clearEscapeHandlers());
afterEach(() => _clearEscapeHandlers());

describe('PipelineView - B-877, une fiche s’ouvre au clavier', () => {
  it('chaque carte porte un vrai bouton « Ouvrir la fiche » qui appelle onContactClick, et garde son nom', () => {
    const onContactClick = vi.fn();
    render(<PipelineView contacts={[contact]} onContactClick={onContactClick} onStageChange={vi.fn()} />);
    const ouvrir = screen.getByRole('button', { name: 'Ouvrir la fiche' });
    expect(ouvrir.tagName).toBe('BUTTON');
    fireEvent.keyDown(ouvrir, { key: 'Enter' });
    fireEvent.click(ouvrir);
    expect(onContactClick).toHaveBeenCalledWith(contact);
    expect(screen.getAllByRole('button', { name: /Alain Moreau/ })).toHaveLength(1);
  });
});
