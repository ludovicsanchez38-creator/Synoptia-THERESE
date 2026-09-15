/**
 * B-845 (cycle 9) : en mode démonstration, la carte du pipeline affichait le
 * vrai nom du contact (`{contact.first_name} {contact.last_name}` brut), son
 * entreprise et son adresse, alors que l'annonce de déplacement passait bien
 * par le masque. Un vrai client apparaissait donc à l'écran pendant une démo.
 */
import { render, screen } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { _clearEscapeHandlers } from '../../lib/escapeStack';
import type { ContactResponse } from '../../services/api';
import { useDemoStore } from '../../stores/demoStore';
import { PipelineView } from './PipelineView';

function contact(patch: Partial<ContactResponse> = {}): ContactResponse {
  return {
    id: 'ct-1',
    first_name: 'Alain',
    last_name: 'Moreau',
    company: 'Moreau SARL',
    email: 'alain@moreau.test',
    phone: null,
    address: null,
    notes: null,
    tags: null,
    stage: 'contact',
    score: 145,
    source: 'site-web',
    last_interaction: null,
    created_at: '2026-08-28T10:00:00Z',
    updated_at: '2026-08-28T10:00:00Z',
    ...patch,
  } as ContactResponse;
}

beforeEach(() => {
  _clearEscapeHandlers();
  useDemoStore.setState({
    enabled: true,
    replacementMap: new Map([
      ['Alain Moreau', 'Camille Bernard'],
      ['Alain', 'Camille'],
      ['Moreau', 'Bernard'],
      ['Moreau SARL', 'Bernard Conseil'],
      ['alain@moreau.test', 'camille@bernard.test'],
    ]),
  });
});

afterEach(() => {
  useDemoStore.setState({ enabled: false, replacementMap: new Map() });
  _clearEscapeHandlers();
});

describe('B-845 : la carte du pipeline respecte le mode démonstration', () => {
  it('masque le nom, l’entreprise et l’adresse du contact', () => {
    render(<PipelineView contacts={[contact()]} onContactClick={vi.fn()} onStageChange={vi.fn()} />);
    const carte = screen.getByTestId('crm-contact-item');
    const texte = carte.textContent ?? '';
    expect(texte).toContain('Camille Bernard');
    expect(texte).toContain('Bernard Conseil');
    expect(texte).toContain('camille@bernard.test');
    expect(texte).not.toMatch(/Alain|Moreau|alain@/);
  });
});
