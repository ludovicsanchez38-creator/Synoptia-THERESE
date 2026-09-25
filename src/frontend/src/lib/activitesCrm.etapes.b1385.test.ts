/**
 * B-1385 (persona Nathalie, cycle 13) : les codes internes des étapes
 * s'affichaient encore après B-1353 : « Stage: contact → discovery »,
 * « Changement de stage dans le pipeline commercial », « · discovery ».
 * Les étapes se lisent avec les libellés des colonnes du Pipeline.
 */
import { describe, expect, it } from 'vitest';
import type { ActivityResponse } from '../services/api';
import { presenterActivite } from './activitesCrm';
import { libelleDEtape } from '../components/crm/pipelineEtapes';

const changement = (extra: string | null, title = 'Stage: contact -> discovery'): ActivityResponse => ({
  id: 'a1', contact_id: 'c1', type: 'stage_change', title,
  description: 'Changement de stage dans le pipeline commercial', extra_data: extra,
  created_at: '2026-09-25T10:00:00Z',
} as ActivityResponse);

describe('B-1385 : les étapes se lisent en français', () => {
  it('un changement d’étape dit « Étape : Contact → Découverte »', () => {
    const { titre, description } = presenterActivite(changement('{"old_stage": "contact", "new_stage": "discovery"}'));
    expect(titre).toBe('Étape : Contact → Découverte');
    expect(description).toBe('Changement d’étape dans le pipeline');
  });

  it('sans données structurées, le titre ancien est traduit aussi', () => {
    expect(presenterActivite(changement(null)).titre).toBe('Étape : Contact → Découverte');
  });

  it('libelleDEtape rend le libellé de colonne, et l’identifiant inconnu tel quel', () => {
    expect(libelleDEtape('discovery')).toBe('Découverte');
    expect(libelleDEtape('proposition')).toBe('Proposition');
    expect(libelleDEtape('etape-maison')).toBe('etape-maison');
  });
});
