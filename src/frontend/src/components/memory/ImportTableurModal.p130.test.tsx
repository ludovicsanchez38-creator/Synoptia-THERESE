/**
 * P-130 (persona Nathalie, cycle 13) : aucune entrée pour importer un fichier
 * Excel ou CSV, alors que le moteur sait prévisualiser et importer (colonnes
 * reconnues, lignes écartées). « Importer (.vcf) » refusait son fichier.
 */
import { fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { MemoryPanel } from './MemoryPanel';
import { _clearEscapeHandlers, runTopEscapeHandler } from '../../lib/escapeStack';
import { useStatusStore } from '../../stores/statusStore';
import { useContactsStore } from '../../stores/contactsStore';

const apiMocks = vi.hoisted(() => ({ apercuImportContacts: vi.fn(), importerContactsTableur: vi.fn() }));
vi.mock('../../services/api/memory', async () => {
  const actual = await vi.importActual<typeof import('../../services/api/memory')>('../../services/api/memory');
  return { ...actual, listContacts: vi.fn().mockResolvedValue([]), searchMemory: vi.fn().mockResolvedValue({ contacts: [] }) };
});
vi.mock('../../services/api', async () => {
  const actual = await vi.importActual<typeof import('../../services/api')>('../../services/api');
  return {
    ...actual,
    apercuImportContacts: apiMocks.apercuImportContacts,
    importerContactsTableur: apiMocks.importerContactsTableur,
    listContactsWithScope: vi.fn().mockResolvedValue([]),
    listFiles: vi.fn().mockResolvedValue([]),
    getRGPDStats: vi.fn().mockResolvedValue(null),
  };
});
vi.mock('../../hooks', () => ({ useDemoMask: () => ({ enabled: false, maskContact: (c: unknown) => c, populateMap: vi.fn(), maskText: (t: string) => t }) }));
vi.mock('../files/FileBrowser', () => ({ FileBrowser: () => <div data-testid="file-browser" /> }));

const fetchContacts = vi.fn().mockResolvedValue(undefined);

describe('P-130 : importer un tableur de contacts', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    useStatusStore.setState({ notifications: [] });
    useContactsStore.setState({ contacts: [], searchResults: null, loading: false, selectedContactId: null, truncated: false, loaded: true, fetchContacts } as never);
    apiMocks.apercuImportContacts.mockResolvedValue({
      total_rows: 3,
      sample_rows: [{ first_name: 'Nadia', last_name: 'Roux', company: 'Roux Conseil', email: 'nadia@roux.test' }],
      detected_columns: ['Prénom', 'Nom', 'Entreprise', 'Email', 'Commentaire'],
      column_mapping: { 'Prénom': 'first_name', Nom: 'last_name', Entreprise: 'company', Email: 'email' },
      validation_errors: [{ row: 3, column: 'stage', message: 'Étape « inconnue » inconnue du pipeline, non enregistrée', data: null }],
      can_import: true,
    });
    apiMocks.importerContactsTableur.mockResolvedValue({
      success: true, created: 2, updated: 1, skipped: 0, errors: [], total_rows: 3, message: '2 contacts créés, 1 mis à jour',
    });
  });

  it('aperçu : colonnes reconnues, colonnes ignorées, lignes écartées ; puis import et relecture', async () => {
    render(<MemoryPanel standalone onClose={vi.fn()} />);
    fireEvent.click(await screen.findByRole('button', { name: /Importer un tableur/ }));
    const fenetre = screen.getByRole('dialog', { name: 'Importer des contacts depuis un tableur' });
    const fichier = new File(['Prénom,Nom\nNadia,Roux\n'], 'prospects.csv', { type: 'text/csv' });
    fireEvent.change(within(fenetre).getByLabelText(/Choisir un fichier/), { target: { files: [fichier] } });

    expect(await within(fenetre).findByText('3 lignes lues.')).toBeInTheDocument();
    expect(within(fenetre).getByText(/Prénom → Prénom/)).toBeInTheDocument();
    expect(within(fenetre).getByText(/Commentaire/)).toBeInTheDocument();
    expect(within(fenetre).getByText(/Ligne 3 : Étape « inconnue » inconnue du pipeline/)).toBeInTheDocument();
    expect(apiMocks.apercuImportContacts).toHaveBeenCalledWith(fichier);

    fireEvent.click(within(fenetre).getByRole('button', { name: 'Importer 3 lignes' }));
    expect(await within(fenetre).findByText('2 contacts créés, 1 mis à jour')).toBeInTheDocument();
    expect(apiMocks.importerContactsTableur).toHaveBeenCalledWith(fichier);
    await waitFor(() => expect(fetchContacts).toHaveBeenCalled());
  });

  it('un aperçu refusé n’autorise pas l’import', async () => {
    apiMocks.apercuImportContacts.mockResolvedValue({
      total_rows: 0, sample_rows: [], detected_columns: [], column_mapping: {},
      validation_errors: [{ row: 0, column: null, message: 'Aucune donnee trouvee', data: null }], can_import: false,
    });
    render(<MemoryPanel standalone onClose={vi.fn()} />);
    fireEvent.click(await screen.findByRole('button', { name: /Importer un tableur/ }));
    const fenetre = screen.getByRole('dialog', { name: 'Importer des contacts depuis un tableur' });
    fireEvent.change(within(fenetre).getByLabelText(/Choisir un fichier/), { target: { files: [new File([''], 'vide.csv')] } });
    expect(await within(fenetre).findByText(/Aucune donnee trouvee/)).toBeInTheDocument();
    expect(within(fenetre).queryByRole('button', { name: /^Importer \d/ })).toBeNull();
  });

  it('Échap ferme la fenêtre d’import, pas la vue Contacts dessous', async () => {
    _clearEscapeHandlers();
    render(<MemoryPanel standalone onClose={vi.fn()} />);
    fireEvent.click(await screen.findByRole('button', { name: /Importer un tableur/ }));
    expect(screen.getByRole('dialog', { name: 'Importer des contacts depuis un tableur' })).toBeInTheDocument();
    expect(runTopEscapeHandler()).toBe(true);
    await waitFor(() => expect(screen.queryByRole('dialog', { name: 'Importer des contacts depuis un tableur' })).toBeNull());
  });
});
