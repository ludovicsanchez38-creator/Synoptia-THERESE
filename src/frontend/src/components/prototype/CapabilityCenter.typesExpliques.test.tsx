/**
 * P-128 (persona Hugo, cycle 13) : 7 « Parcours », 19 « Vue », 4 « Demande
 * relue » ; seule explication, une phrase en pied qui ne distinguait pas un
 * Parcours d'une Vue. Et la carte « Agenda » ouvrait « Préparer un
 * rendez-vous », la carte « Email » le mode « Écrire » : la carte ne disait
 * pas ce qu'elle ouvre. La légende dit ce que chaque type ouvre, le badge le
 * redit en infobulle, et ces deux cartes portent le nom de leur écran.
 */
import { render, screen, within } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

import { CapabilityCenter, capabilities } from './CapabilityCenter';
import { EXPLICATION_DU_TYPE } from './typeCapacite';

describe('P-128 : les types de capacités sont expliqués', () => {
  it('la légende dit ce que chaque type ouvre', () => {
    render(<CapabilityCenter onClose={vi.fn()} onChoose={vi.fn()} />);
    const legende = screen.getByRole('dialog').querySelector('footer')?.textContent ?? '';
    for (const explication of Object.values(EXPLICATION_DU_TYPE)) expect(legende).toContain(explication);
    expect(EXPLICATION_DU_TYPE.Vue).toMatch(/écran/);
    expect(EXPLICATION_DU_TYPE.Parcours).toMatch(/Accueil/);
  });

  it('chaque badge porte l’explication de son type en infobulle', () => {
    render(<CapabilityCenter onClose={vi.fn()} onChoose={vi.fn()} />);
    const carte = screen.getAllByRole('button').find((b) => b.querySelector('b'))!;
    const badge = within(carte).getByText(/^(Parcours|Vue|Demande relue)$/);
    expect(badge.getAttribute('title')).toBe(EXPLICATION_DU_TYPE[badge.textContent as keyof typeof EXPLICATION_DU_TYPE]);
  });

  it('les cartes Agenda et Email portent le nom de l’écran qu’elles ouvrent', () => {
    const titres = Object.fromEntries(capabilities.map((c) => [c.id, c.title]));
    expect(titres.calendar).toBe('Préparer un rendez-vous');
    expect(titres.email).toBe('Écrire un e-mail');
    const motsAgenda = capabilities.find((c) => c.id === 'calendar')!.keywords;
    expect(motsAgenda).toContain('agenda');
  });
});
