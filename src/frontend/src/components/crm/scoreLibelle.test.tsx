/**
 * Campagne dix personas (28/08), finding F6 de la dirigeante d'organisme de
 * formation : « Le score "de 0 à 100" monte à 125 ».
 *
 * L'infobulle ET l'aria-label du pipeline annonçaient une échelle 0-100. Le
 * calcul (`scoring.py`) n'est borné qu'en bas — `max(0, score)` — pour un
 * maximum théorique de 170. Les journaux de la campagne montrent 4 contacts
 * sur 8 au-dessus de 100, dont trois à 145, sans aucune activité.
 *
 * Correctif retenu : on corrige le LIBELLÉ, pas le calcul. Les deux relecteurs
 * ont convergé là-dessus — `min(100, ...)` écraserait 120 et 145 sur la même
 * valeur et détruirait la discrimination que le score sert à produire, et une
 * migration par recalcul effacerait les scores saisis à la main (aucun champ
 * de provenance ne permet de les distinguer).
 *
 * Test de RENDU : c'est l'infobulle vue par l'utilisateur et l'étiquette lue
 * par les lecteurs d'écran qui mentaient.
 */
import { render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

import { PipelineView } from './PipelineView';

const CONTACT = {
  id: 'c1',
  display_name: 'Alain Moreau',
  first_name: 'Alain',
  last_name: 'Moreau',
  company: 'Moreau SARL',
  stage: 'contact',
  score: 145,          // la valeur réellement observée pendant la campagne
  created_at: '2026-08-28T10:00:00Z',
  updated_at: '2026-08-28T10:00:00Z',
} as never;

describe('Le score n’annonce plus une échelle que le calcul ne tient pas', () => {
  it('n’affiche plus « de 0 à 100 » dans l’infobulle ni l’étiquette', () => {
    render(
      <PipelineView contacts={[CONTACT]} onContactClick={vi.fn()} onStageChange={vi.fn()} />,
    );

    expect(screen.queryByTitle(/de 0 à 100/i)).toBeNull();
    expect(screen.queryByLabelText(/de 0 à 100/i)).toBeNull();
  });

  it('affiche le score tel qu’il est, sans le plafonner', () => {
    render(
      <PipelineView contacts={[CONTACT]} onContactClick={vi.fn()} onStageChange={vi.fn()} />,
    );

    // 145 doit rester 145 : borner à l'affichage laisserait l'API, les
    // exports et les moyennes du pipeline dire autre chose que l'écran.
    expect(screen.getByText('145')).toBeInTheDocument();
  });
});
