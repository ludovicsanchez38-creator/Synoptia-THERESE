/**
 * Revue P-148, constat 5 : « Ouvrir la fiche de X », depuis la vue d'ensemble
 * d'un projet, montrait la fiche d'une AUTRE personne quand X n'était pas
 * parmi les 200 contacts chargés du carnet : le canevas retombait sur
 * `filteredContacts[0]`. Les contacts rangés dans un projet peu actif sont les
 * premiers concernés.
 *
 * Une fiche demandée se lit par son identifiant, ou se dit introuvable ; elle
 * n'est jamais remplacée par la première du carnet.
 */
import { act, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import type { Contact } from '../../services/api/memory';
import { useDemoStore } from '../../stores/demoStore';

const api = vi.hoisted(() => ({
  getContact: vi.fn(),
  listActivities: vi.fn(),
  listerLesSeancesDuContact: vi.fn(),
}));
vi.mock('../../services/api', async (importOriginal) => ({
  ...(await importOriginal<typeof import('../../services/api')>()),
  ...api,
}));

import { ApiError } from '../../services/api';
import { maskContact } from '../../lib/demoMask';
import { contactDisplayName } from './prototypeReadModels';
import { ContactsMemoryCanvas } from './ContactsMemoryCard';

function fiche(id: string, prenom: string, nom: string, entreprise: string): Contact {
  return {
    id, first_name: prenom, last_name: nom, company: entreprise, email: `${prenom.toLowerCase()}@exemple.test`,
    phone: null, address: null, notes: `${prenom} ${nom} suit le chantier.`, tags: [], stage: 'client', score: 0,
    source: 'local', last_interaction: null, created_at: '2026-09-20T09:00:00Z', updated_at: '2026-09-20T09:00:00Z',
  };
}

const HELENE = fiche('c-helene', 'Hélène', 'Ménard', 'Ménard Conseil');
const JULIEN = fiche('c-julien', 'Julien', 'Garnier', 'Garnier Bois');

function rendre(selectedContactId: string | null) {
  return render(
    <ContactsMemoryCanvas
      resource={{ status: 'ready', error: null, data: [HELENE] }}
      selectedContactId={selectedContactId}
      onSelectContact={vi.fn()}
      onRetry={vi.fn()}
      onOpenClassic={vi.fn()}
    />,
  );
}

/** Le titre de la fiche affichée (le premier h3 ; l'historique vide en porte un second). */
function titreDeLaFiche(): string | null {
  return screen.queryAllByRole('heading', { level: 3 })[0]?.textContent ?? null;
}

describe('Revue P-148, constat 5 : une fiche demandée hors du carnet', () => {
  beforeEach(() => {
    Object.values(api).forEach((mock) => mock.mockReset());
    api.listActivities.mockResolvedValue([]);
    api.listerLesSeancesDuContact.mockResolvedValue([]);
  });
  afterEach(() => {
    useDemoStore.setState({ enabled: false, replacementMap: new Map() });
  });

  it('est lue par son identifiant, et la première du carnet n’apparaît jamais à sa place', async () => {
    let livrer: (c: Contact) => void = () => {};
    api.getContact.mockReturnValue(new Promise<Contact>((resolve) => { livrer = resolve; }));
    rendre(JULIEN.id);

    // Pendant la lecture : aucune fiche d'emprunt.
    expect(api.getContact).toHaveBeenCalledWith(JULIEN.id);
    expect(titreDeLaFiche()).toBeNull();
    expect(screen.getByRole('status')).toHaveTextContent('Lecture de la fiche');

    await act(async () => { livrer(JULIEN); });
    await waitFor(() => expect(titreDeLaFiche()).toBe('Julien Garnier'));
    expect(screen.getByText('Julien Garnier suit le chantier.')).toBeInTheDocument();
  });

  it('une fiche qui n’existe plus se dit introuvable, sans fiche d’emprunt', async () => {
    api.getContact.mockRejectedValue(new ApiError(404, 'Not Found', 'Contact not found'));
    rendre('c-disparu');
    expect(await screen.findByText('Fiche introuvable')).toBeInTheDocument();
    expect(titreDeLaFiche()).toBeNull();
    expect(screen.queryByText(/Ménard Conseil/)).toBeNull();
  });

  it('une lecture en panne le dit, et « Réessayer » relit la même fiche', async () => {
    api.getContact.mockRejectedValueOnce(new TypeError('Failed to fetch')).mockResolvedValueOnce(JULIEN);
    rendre(JULIEN.id);
    const reessayer = await screen.findByRole('button', { name: 'Réessayer' });
    expect(screen.getByText('La fiche n’a pas pu être lue.')).toBeInTheDocument();
    expect(titreDeLaFiche()).toBeNull();

    fireEvent.click(reessayer);
    await waitFor(() => expect(titreDeLaFiche()).toBe('Julien Garnier'));
    expect(api.getContact).toHaveBeenCalledTimes(2);
    expect(api.getContact).toHaveBeenLastCalledWith(JULIEN.id);
  });

  it('en démonstration, la fiche lue hors du carnet ne sort jamais en clair', async () => {
    useDemoStore.setState({ enabled: true, replacementMap: new Map() });
    api.getContact.mockResolvedValue(JULIEN);
    const { container } = rendre(JULIEN.id);
    // C'est bien la fiche demandée qui s'affiche, sous son pseudonyme.
    await waitFor(() => expect(titreDeLaFiche()).toBe(contactDisplayName(maskContact(JULIEN))));
    expect(api.getContact).toHaveBeenCalledWith(JULIEN.id);
    await waitFor(() => expect(screen.queryByText(/suit le chantier/)).not.toBeNull());
    expect(container.textContent).not.toMatch(/Julien|Garnier|julien@/);
  });

  it('une fiche du carnet s’affiche sans lecture supplémentaire', () => {
    rendre(HELENE.id);
    expect(titreDeLaFiche()).toBe('Hélène Ménard');
    expect(api.getContact).not.toHaveBeenCalled();
  });

  it('sans fiche demandée, la première du carnet reste proposée', () => {
    rendre(null);
    expect(titreDeLaFiche()).toBe('Hélène Ménard');
    expect(api.getContact).not.toHaveBeenCalled();
  });
});
