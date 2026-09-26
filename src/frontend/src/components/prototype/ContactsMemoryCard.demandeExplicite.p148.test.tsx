/**
 * Revue P-148, passe 2, constat 1 : une demande explicite de fiche (« Ouvrir
 * la fiche de Camille » depuis un projet, la palette, Cette semaine) montrait
 * une autre personne quand une recherche tapée plus tôt était encore active
 * dans le panneau Contacts, resté monté : le premier résultat de la recherche
 * prenait la place de la fiche demandée.
 *
 * La coque émet un jeton à chaque demande explicite ; le panneau vide sa
 * recherche à chaque nouveau jeton. Une sélection faite dans la liste du
 * panneau n'émet pas de jeton : la recherche en cours garde la main (test
 * « recherche localement » de ContactsMemoryCard.test.tsx).
 */
import { act, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import type { Contact } from '../../services/api/memory';

const api = vi.hoisted(() => ({ getContact: vi.fn(), listActivities: vi.fn(), listerLesSeancesDuContact: vi.fn() }));
vi.mock('../../services/api', async (importOriginal) => ({
  ...(await importOriginal<typeof import('../../services/api')>()),
  ...api,
}));

import { ContactsMemoryCanvas } from './ContactsMemoryCard';

function fiche(id: string, prenom: string): Contact {
  return {
    id, first_name: prenom, last_name: 'Martin', company: 'Synoptïa', email: `${prenom.toLowerCase()}@exemple.test`,
    phone: null, address: null, notes: `Notes de ${prenom}`, tags: [], stage: 'client', score: 0,
    source: 'local', last_interaction: null, created_at: '2026-09-20T09:00:00Z', updated_at: '2026-09-20T09:00:00Z',
  };
}
const CAMILLE = fiche('c1', 'Camille');
const ALEX = fiche('c2', 'Alex');

function panneau(selectedContactId: string | null, demande: number) {
  return (
    <ContactsMemoryCanvas
      resource={{ status: 'ready', error: null, data: [CAMILLE, ALEX] }}
      selectedContactId={selectedContactId}
      demande={demande}
      onSelectContact={vi.fn()}
      onRetry={vi.fn()}
      onOpenClassic={vi.fn()}
    />
  );
}

const titreDeLaFiche = () => screen.queryAllByRole('heading', { level: 3 })[0]?.textContent ?? null;
const recherche = () => screen.getByLabelText('Rechercher un contact');

describe('Revue P-148, passe 2, constat 1 : une demande explicite l’emporte sur une recherche active', () => {
  beforeEach(() => {
    Object.values(api).forEach((mock) => mock.mockReset());
    api.listActivities.mockResolvedValue([]);
    api.listerLesSeancesDuContact.mockResolvedValue([]);
  });

  it('recherche « Alex » active, demande de c1 : la fiche Camille s’affiche et la recherche est vide', () => {
    const { rerender } = render(panneau(null, 0));
    fireEvent.change(recherche(), { target: { value: 'Alex' } });
    expect(titreDeLaFiche()).toBe('Alex Martin');

    rerender(panneau('c1', 1));

    expect(titreDeLaFiche()).toBe('Camille Martin');
    expect(recherche()).toHaveValue('');
  });

  it('la même fiche redemandée pendant une recherche revient, et la recherche est vidée', () => {
    const { rerender } = render(panneau('c1', 1));
    fireEvent.change(recherche(), { target: { value: 'Alex' } });
    expect(titreDeLaFiche()).toBe('Alex Martin');

    rerender(panneau('c1', 2));

    expect(titreDeLaFiche()).toBe('Camille Martin');
    expect(recherche()).toHaveValue('');
  });

  it('une fiche hors du carnet demandée pendant une recherche est lue, sans fiche d’emprunt', async () => {
    api.getContact.mockResolvedValue(fiche('c-loin', 'Julien'));
    const { rerender } = render(panneau(null, 0));
    fireEvent.change(recherche(), { target: { value: 'Alex' } });

    await act(async () => { rerender(panneau('c-loin', 1)); });

    expect(recherche()).toHaveValue('');
    await waitFor(() => expect(titreDeLaFiche()).toBe('Julien Martin'));
    expect(api.getContact).toHaveBeenCalledWith('c-loin');
  });

  it('sans nouveau jeton, la recherche garde la main', () => {
    const { rerender } = render(panneau('c1', 1));
    fireEvent.change(recherche(), { target: { value: 'Alex' } });
    rerender(panneau('c1', 1));
    expect(titreDeLaFiche()).toBe('Alex Martin');
    expect(recherche()).toHaveValue('Alex');
  });
});
