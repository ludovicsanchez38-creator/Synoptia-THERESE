/**
 * B-1443 (recette P-146, lot 2, O4) : un contact sans prénom ni nom, créé
 * avec sa seule entreprise (« Sans Nom SA » importée d'un tableur), s'appelait
 * « Sans nom » dans la liste et « Contact » dans le Pipeline, le libellé même
 * de l'étape. Partout, le nom affiché retombe sur l'entreprise puis l'e-mail
 * (`contactDisplayName`).
 */
import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';

import type { ContactResponse } from '../../services/api';
import { PipelineView } from './PipelineView';

const SOCIETE = {
  id: 'ct-sa', first_name: null, last_name: null, company: 'Sans Nom SA', email: null, phone: null,
  address: null, notes: null, tags: null, stage: 'contact', score: 0, source: null,
  last_interaction: null, created_at: '2026-09-01T10:00:00Z', updated_at: '2026-09-01T10:00:00Z',
} as unknown as ContactResponse;

describe('B-1443 : une fiche sans nom s’appelle par son entreprise', () => {
  it('la carte du Pipeline porte le nom de l’entreprise', () => {
    render(<PipelineView contacts={[SOCIETE]} onContactClick={() => {}} onStageChange={() => {}} />);
    expect(screen.getByRole('button', { name: /Sans Nom SA/ })).toBeInTheDocument();
  });
});

describe('B-1443 : le titre visible de la carte', () => {
  it('affiche l’entreprise une seule fois, en titre', () => {
    render(<PipelineView contacts={[SOCIETE]} onContactClick={() => {}} onStageChange={() => {}} />);
    const affiches = screen.getAllByText('Sans Nom SA');
    expect(affiches).toHaveLength(1);
    // Le titre de la carte (div), pas le sous-titre de l'entreprise (p).
    expect(affiches[0].tagName).toBe('DIV');
  });
});
