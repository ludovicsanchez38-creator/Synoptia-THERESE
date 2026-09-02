/**
 * B-240 : « Aucun contact » disait la même chose dans trois situations.
 *
 * Un carnet vraiment vide, une recherche sans résultat et un périmètre filtré
 * rendaient la même phrase au caractère près. Avec deux cents fiches et une
 * faute de frappe dans la recherche, l'écran affirmait que le carnet était
 * vide. L'information manquait pourtant à deux composants de distance :
 * `isSearching` et `scopeFilter` vivent dans MemoryPanel, l'état vide vit dans
 * ContactsList et n'en recevait rien.
 *
 * Ce test exige que les trois phrases diffèrent, que la recherche soit citée
 * et qu'un moyen d'effacer le filtre soit offert ET fonctionne.
 */
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import { useContactsStore } from '../../stores/contactsStore';
import { useStatusStore } from '../../stores/statusStore';
import type { Contact } from '../../services/api';

// Le panneau recharge ses contacts au montage : sans ce double, `fetchContacts`
// écraserait le carnet posé par le test avec une liste vide.
const { mockListContacts, mockSearchMemory } = vi.hoisted(() => ({
  mockListContacts: vi.fn(),
  mockSearchMemory: vi.fn(),
}));

vi.mock('../../services/api/memory', async () => {
  const actual = await vi.importActual<typeof import('../../services/api/memory')>(
    '../../services/api/memory',
  );
  return {
    ...actual,
    listContacts: (...args: unknown[]) => mockListContacts(...args),
    searchMemory: (...args: unknown[]) => mockSearchMemory(...args),
  };
});

const mockListContactsWithScope = vi.fn();
const mockGetRGPDStats = vi.fn();

vi.mock('../../services/api', async () => {
  const actual = await vi.importActual<typeof import('../../services/api')>('../../services/api');
  return {
    ...actual,
    listContactsWithScope: (...args: unknown[]) => mockListContactsWithScope(...args),
    listFiles: vi.fn().mockResolvedValue([]),
    getRGPDStats: (...args: unknown[]) => mockGetRGPDStats(...args),
    downloadVCFFile: vi.fn(),
  };
});

vi.mock('../../hooks', () => ({
  useDemoMask: () => ({
    enabled: false,
    maskContact: (contact: unknown) => contact,
    populateMap: vi.fn(),
  }),
}));

import { MemoryPanel } from './MemoryPanel';

const marie = {
  id: 'ct-1',
  first_name: 'Marie',
  last_name: 'Lefevre',
  company: 'Lefevre Conseil',
  email: null,
  phone: null,
  notes: null,
  tags: null,
  scope: 'global',
  created_at: '2026-08-01T00:00:00Z',
  updated_at: '2026-08-01T00:00:00Z',
} as unknown as Contact;

function poserLeCarnet(contacts: Contact[]) {
  mockListContacts.mockResolvedValue(contacts);
  mockSearchMemory.mockResolvedValue({ contacts: [] });
  useContactsStore.setState({
    contacts,
    searchResults: null,
    loading: false,
    loaded: true,
    error: null,
    selectedContactId: null,
    truncated: false,
  });
}

/**
 * Le texte de l'état vide, quelle que soit sa forme. Le repli sur « Aucun
 * contact » laisse le test lire l'ancien écran : sans lui, la version fautive
 * échouerait sur un identifiant manquant plutôt que sur le vrai défaut, à
 * savoir deux situations différentes qui rendent la même phrase.
 */
function messageEtatVide(): string {
  const cible = screen.queryByTestId('contacts-etat-vide') ?? screen.queryByText(/Aucun contact/);
  if (!cible) throw new Error('aucun état vide rendu');
  return cible.textContent ?? '';
}

/** Le premier rendu affiche un indicateur de chargement : on l'attend. */
async function attendreEtatVide(): Promise<string> {
  let texte = '';
  await waitFor(() => { texte = messageEtatVide(); });
  return texte;
}

describe('B-240 : l’état vide dit laquelle des trois causes s’applique', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockListContactsWithScope.mockResolvedValue([]);
    mockGetRGPDStats.mockResolvedValue(null);
    useStatusStore.setState({ notifications: [] });
    poserLeCarnet([]);
  });

  it('un carnet vide et une recherche sans résultat ne disent pas la même chose', async () => {
    const carnetVide = render(<MemoryPanel standalone />);
    const messageCarnetVide = await attendreEtatVide();
    expect(messageCarnetVide).toContain('Aucun contact');
    carnetVide.unmount();

    poserLeCarnet([marie]);
    render(<MemoryPanel standalone />);
    fireEvent.change(screen.getByTestId('memory-search-input'), { target: { value: 'zzzqqq' } });

    await waitFor(() => {
      expect(screen.queryByText('Marie Lefevre')).not.toBeInTheDocument();
    });
    const messageRecherche = messageEtatVide();

    expect(messageRecherche).not.toBe(messageCarnetVide);
    expect(messageRecherche).toContain('zzzqqq');
  });

  it('offre d’effacer la recherche, et l’effacement ramène le contact', async () => {
    poserLeCarnet([marie]);
    render(<MemoryPanel standalone />);
    fireEvent.change(screen.getByTestId('memory-search-input'), { target: { value: 'zzzqqq' } });

    const effacer = await screen.findByRole('button', { name: /Effacer la recherche/i });
    fireEvent.click(effacer);

    expect(await screen.findByText('Marie Lefevre')).toBeInTheDocument();
  });

  it('un périmètre sans contact le dit, au lieu d’annoncer un carnet vide', async () => {
    poserLeCarnet([marie]);
    render(<MemoryPanel standalone />);
    // Marie est en périmètre « global » : filtrer sur « Projet » vide la liste
    // sans que le carnet soit vide.
    fireEvent.click(screen.getByRole('button', { name: 'Projet' }));

    await waitFor(() => {
      expect(screen.queryByText('Marie Lefevre')).not.toBeInTheDocument();
    });
    expect(messageEtatVide()).toContain('Projet');
    expect(messageEtatVide()).not.toBe('Aucun contact');

    fireEvent.click(screen.getByRole('button', { name: /Voir tous les périmètres/i }));
    expect(await screen.findByText('Marie Lefevre')).toBeInTheDocument();
  });
});
