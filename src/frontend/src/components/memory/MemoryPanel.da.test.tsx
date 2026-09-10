/**
 * DA « Application affinée », lot 4 : l'écran Contacts
 * (`docs/plans/2026-09-11-da-lot4-contacts-design.md`, § 9).
 */
import { fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import { useContactsStore } from '../../stores/contactsStore';
import { useStatusStore } from '../../stores/statusStore';
import type { Contact } from '../../services/api';

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

vi.mock('../../services/api', async () => {
  const actual = await vi.importActual<typeof import('../../services/api')>('../../services/api');
  return {
    ...actual,
    listContactsWithScope: vi.fn().mockResolvedValue([]),
    listFiles: vi.fn().mockResolvedValue([]),
    getRGPDStats: vi.fn().mockResolvedValue(null),
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

const fetchContactsReel = useContactsStore.getState().fetchContacts;

const marie = {
  id: 'ct-1',
  first_name: 'Marie',
  last_name: 'Lefevre',
  company: 'Lefevre Conseil',
  email: 'marie@lefevre.test',
  phone: null,
  notes: null,
  tags: null,
  scope: 'global',
  created_at: '2026-08-01T00:00:00Z',
  updated_at: '2026-08-01T00:00:00Z',
} as unknown as Contact;

function classesDUnNoeud(n: Element): string {
  const brut = (n as HTMLElement).className;
  if (typeof brut === 'string') return brut;
  const svg = (n as SVGElement).className;
  return typeof svg === 'object' && svg && 'baseVal' in svg ? svg.baseVal : '';
}

function interactifsSousLePlancher(racine: HTMLElement): string[] {
  const fautifs: string[] = [];
  for (const el of racine.querySelectorAll('button, input, select, textarea, a, [role="button"]')) {
    const noeuds = [el, ...Array.from(el.querySelectorAll('*'))];
    for (const n of noeuds) {
      if (/\btext-xs\b/.test(classesDUnNoeud(n))) {
        fautifs.push(((el as HTMLElement).textContent ?? el.tagName).trim().slice(0, 48));
        break;
      }
    }
  }
  return fautifs;
}

function poserLeCarnet(contacts: Contact[], extra: { error?: string | null } = {}) {
  mockListContacts.mockResolvedValue(contacts);
  mockSearchMemory.mockResolvedValue({ contacts: [] });
  useContactsStore.setState({
    contacts,
    searchResults: null,
    loading: false,
    loaded: true,
    error: extra.error ?? null,
    selectedContactId: null,
    truncated: false,
    fetchContacts:
      contacts.length > 0 ? vi.fn().mockResolvedValue(undefined) : fetchContactsReel,
  });
}

beforeEach(() => {
  vi.clearAllMocks();
  useStatusStore.setState({ notifications: [] });
  poserLeCarnet([]);
});

describe('Lot 4 DA : liste Contacts', () => {
  it('une fiche est une Ligne : une commande, grille 2rem 1fr auto', async () => {
    poserLeCarnet([marie]);
    const onEditContact = vi.fn();
    render(<MemoryPanel standalone onEditContact={onEditContact} />);
    const titre = await screen.findByRole('button', { name: 'Marie Lefevre' });
    const rangee = titre.closest('[class*="grid-cols-[2rem_1fr_auto]"]') as HTMLElement;
    expect(rangee).not.toBeNull();
    expect(rangee.tagName).not.toBe('BUTTON');
    fireEvent.click(titre);
    expect(onEditContact).toHaveBeenCalledTimes(1);
  });

  it('EtatVide transmet contacts-etat-vide', async () => {
    render(<MemoryPanel standalone />);
    const vide = await screen.findByTestId('contacts-etat-vide');
    expect(within(vide).getByRole('heading', { level: 3, name: 'Aucun contact' })).toBeInTheDocument();
  });
});

describe('Lot 4 DA : un seul Réessayer', () => {
  it('la panne a un Réessayer, le vide constaté n’en a pas', async () => {
    mockListContacts.mockRejectedValueOnce(new Error('boom')).mockResolvedValue([]);
    render(<MemoryPanel standalone />);
    expect(await screen.findByRole('alert')).toHaveTextContent(/Impossible de charger les contacts/);
    expect(screen.getAllByRole('button', { name: 'Réessayer' })).toHaveLength(1);

    fireEvent.click(screen.getByRole('button', { name: 'Réessayer' }));
    await waitFor(() => expect(screen.queryByRole('alert')).toBeNull());
    expect(await screen.findByTestId('contacts-etat-vide')).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: 'Réessayer' })).toBeNull();
  });
});

describe('Lot 4 DA : crochets conservés', () => {
  it('memory-search-input, memory-add-contact-btn et les title des trois actions', async () => {
    render(<MemoryPanel standalone onNewContact={vi.fn()} />);
    expect(await screen.findByTestId('memory-search-input')).toBeInTheDocument();
    expect(screen.getByTestId('memory-add-contact-btn')).toBeInTheDocument();
    expect(screen.getByLabelText('Retrouver un contact')).toBe(screen.getByTestId('memory-search-input'));
    expect(screen.getByTitle('Importer des contacts (.vcf)')).toBeInTheDocument();
    expect(screen.getByTitle('Exporter les contacts (.vcf)')).toBeInTheDocument();
    expect(screen.getByTitle('Nouveau contact')).toBeInTheDocument();
  });

  it('aucun interactif n’est sous 14 px', async () => {
    poserLeCarnet([marie]);
    render(<MemoryPanel standalone onNewContact={vi.fn()} />);
    await screen.findByText('Marie Lefevre');
    expect(interactifsSousLePlancher(screen.getByTestId('memory-panel'))).toEqual([]);
  });
});
