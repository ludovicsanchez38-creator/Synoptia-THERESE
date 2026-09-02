/**
 * B-226 : un contact sans source disparaissait du Pipeline SANS RIEN DIRE.
 *
 * Le CRM est une vue filtrée du store unique : `allContacts.filter(c => !!c.source)`.
 * Le filtre est un choix produit assumé (éviter les doublons avec la Mémoire) et
 * n'est pas en cause ici. Ce qui l'est : la règle n'existait que dans un
 * commentaire de code, et l'en-tête comptait la liste DÉJÀ filtrée. Un contact
 * créé depuis Contacts (le formulaire n'offre aucun champ « source ») ressort de
 * l'API avec source=null et stage="contact" : il n'apparaît nulle part, et
 * l'écran annonce « 0 contact » face à une base qui en détient un.
 *
 * Le contrat fermé ici est la DIVULGATION : quand des contacts sont écartés, le
 * critère et le total réel doivent être lisibles à l'écran.
 */
import { render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import { useCRMStore } from '../../stores/crmStore';
import { useContactsStore } from '../../stores/contactsStore';
import type { ContactResponse } from '../../services/api';

vi.mock('../../services/api', async () => {
  const reel = await vi.importActual<typeof import('../../services/api')>('../../services/api');
  return {
    ...reel,
    listProjects: vi.fn().mockResolvedValue([]),
    listActivities: vi.fn().mockResolvedValue([]),
    listContacts: vi.fn().mockRejectedValue(new Error('hors réseau')),
  };
});

import { CRMPanel } from './CRMPanel';

function contact(patch: Partial<ContactResponse>): ContactResponse {
  return {
    id: 'ct-1',
    first_name: 'Marie',
    last_name: 'Lefèvre',
    company: null,
    email: null,
    phone: null,
    address: null,
    notes: null,
    tags: null,
    stage: 'contact',
    score: 0,
    source: null,
    last_interaction: null,
    created_at: '2026-09-01T10:00:00Z',
    updated_at: '2026-09-01T10:00:00Z',
    ...patch,
  } as ContactResponse;
}

describe("B-226 : le Pipeline dit ce qu'il ne montre pas", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    useCRMStore.setState({ projects: [], activeTab: 'pipeline' });
    useContactsStore.setState({ contacts: [], selectedContactId: null, truncated: false });
  });

  it('un contact sans source ne disparaît pas en silence : le critère et le total réel sont à l’écran', async () => {
    // Deux contacts, dont UN SEUL est masqué : sans cela, masqués et total
    // vaudraient tous deux 1 et une phrase n'affichant que le nombre masqué
    // passerait le test sans jamais dire le total.
    useContactsStore.setState({
      contacts: [
        contact({ id: 'ct-1', source: null }),
        contact({ id: 'ct-2', first_name: 'Paul', last_name: 'Girard', source: 'site-web' }),
      ],
    });

    render(<CRMPanel standalone />);

    // Le critère doit être NOMMÉ à l'écran, pas seulement dans un commentaire.
    const mention = await screen.findByText(/source/i);
    expect(mention).toBeInTheDocument();

    // Et le total réel de la base doit y figurer : « 1 contact » seul contredit
    // une base qui en détient deux, sans jamais pouvoir se contredire lui-même
    // (le compteur compte la vue déjà filtrée).
    expect(mention.textContent ?? '').toMatch(/\b2\b/);
  });

  it("aucune mention parasite quand tous les contacts sont dans le pipeline", async () => {
    useContactsStore.setState({ contacts: [contact({ source: 'site-web' })] });

    render(<CRMPanel standalone />);

    await screen.findByRole('tablist');
    expect(screen.queryByText(/seuls les contacts ayant une source/i)).toBeNull();
  });
});
