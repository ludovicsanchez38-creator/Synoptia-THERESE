/**
 * P-115 (persona Claire, cycle 13) : « je ne sais pas où vivent mes clients ».
 * La liste n'affichait aucun périmètre, « Conv. » était abrégé, et le filtre
 * « Projet » répondait « Aucun contact » sans dire comment y ranger quelqu'un.
 */
import { fireEvent, render, screen, within } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { MemoryPanel } from './MemoryPanel';
import { useStatusStore } from '../../stores/statusStore';
import { useContactsStore } from '../../stores/contactsStore';

vi.mock('../../services/api/memory', async () => {
  const actual = await vi.importActual<typeof import('../../services/api/memory')>('../../services/api/memory');
  return { ...actual, listContacts: vi.fn().mockResolvedValue([]), searchMemory: vi.fn().mockResolvedValue({ contacts: [] }) };
});
vi.mock('../../services/api', async () => {
  const actual = await vi.importActual<typeof import('../../services/api')>('../../services/api');
  return { ...actual, listContactsWithScope: vi.fn().mockResolvedValue([]), listFiles: vi.fn().mockResolvedValue([]), getRGPDStats: vi.fn().mockResolvedValue(null) };
});
vi.mock('../../hooks', () => ({ useDemoMask: () => ({ enabled: false, maskContact: (c: unknown) => c, populateMap: vi.fn() }) }));
vi.mock('../files/FileBrowser', () => ({ FileBrowser: () => <div data-testid="file-browser" /> }));

const fiche = (id: string, prenom: string, scope: string) => ({
  id, first_name: prenom, last_name: 'Exemple', name: `${prenom} Exemple`, email: null, company: null, scope,
  created_at: '2026-09-01T00:00:00Z', updated_at: '2026-09-01T00:00:00Z',
});

function ligneDe(prenom: string): HTMLElement {
  // Ligne : racine > colonne du libellé > bouton du titre.
  return screen.getByText(`${prenom} Exemple`).parentElement!.parentElement as HTMLElement;
}

describe('P-115 : où vit un contact', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    useStatusStore.setState({ notifications: [] });
    useContactsStore.setState({
      contacts: [fiche('a', 'Hélène', 'global'), fiche('b', 'Julien', 'project'), fiche('c', 'Sophie', 'conversation')] as never,
      searchResults: null, loading: false, selectedContactId: null, truncated: false,
      fetchContacts: vi.fn().mockResolvedValue(undefined),
    } as never);
  });

  it('le filtre dit « Conversation » en entier, et une aide explique les périmètres', async () => {
    render(<MemoryPanel isOpen onClose={vi.fn()} />);
    await screen.findByText('Hélène Exemple');
    const filtres = screen.getByRole('group', { name: 'Périmètre des contacts' });
    expect(within(filtres).getByRole('button', { name: 'Conversation' })).toBeInTheDocument();
    expect(within(filtres).queryByRole('button', { name: 'Conv.' })).toBeNull();
    expect(screen.getByTestId('aide-perimetre')).toHaveTextContent(/visible dans toutes les conversations/);
    expect(screen.getByTestId('aide-perimetre')).toHaveTextContent(/conversation rattachée à un projet/);
    // Relecture : un contact de projet se voit aussi en mode « Tous les projets »
    // (memory_tools._cloison_contacts), et une fiche de conversation nulle part ailleurs.
    expect(screen.getByTestId('aide-perimetre')).toHaveTextContent(/« Tous les projets »/);
    expect(screen.getByTestId('aide-perimetre')).toHaveTextContent(/dans cette conversation seulement/);
  });

  it('un contact rangé dans un projet ou une conversation le montre sur sa ligne', async () => {
    render(<MemoryPanel isOpen onClose={vi.fn()} />);
    await screen.findByText('Hélène Exemple');
    expect(ligneDe('Julien')).toHaveTextContent(/Projet/);
    expect(ligneDe('Sophie')).toHaveTextContent(/Conversation/);
    expect(ligneDe('Hélène')).not.toHaveTextContent(/Projet|Conversation/);
  });

  it('un périmètre vide dit comment y ranger quelqu’un', async () => {
    useContactsStore.setState({ contacts: [fiche('a', 'Hélène', 'global')] as never } as never);
    render(<MemoryPanel isOpen onClose={vi.fn()} />);
    await screen.findByText('Hélène Exemple');
    fireEvent.click(within(screen.getByRole('group', { name: 'Périmètre des contacts' })).getByRole('button', { name: 'Projet' }));
    expect(await screen.findByText(/Un contact entre dans un projet quand tu le crées depuis une conversation rattachée à ce projet/)).toBeInTheDocument();
  });
});
