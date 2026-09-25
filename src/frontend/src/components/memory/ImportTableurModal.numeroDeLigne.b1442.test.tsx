/**
 * B-1442 (recette P-146, lot 2, O10) : les lignes signalées de l'import
 * étaient numérotées depuis la première ligne de DONNÉES : « Ligne 1 » était
 * la ligne 2 du tableur (l'en-tête n'est pas compté). Dans un CSV ou un
 * classeur, le numéro affiché est celui du tableur ; dans un JSON, c'est le
 * rang de l'élément.
 */
import { fireEvent, render, screen, within } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

const apiMocks = vi.hoisted(() => ({ apercuImportContacts: vi.fn(), importerContactsTableur: vi.fn() }));
vi.mock('../../services/api', async (importOriginal) => ({
  ...(await importOriginal<typeof import('../../services/api')>()),
  apercuImportContacts: apiMocks.apercuImportContacts,
  importerContactsTableur: apiMocks.importerContactsTableur,
}));

import { ImportTableurModal } from './ImportTableurModal';

function apercu() {
  apiMocks.apercuImportContacts.mockResolvedValue({
    total_rows: 2, sample_rows: [], detected_columns: ['Prénom'], column_mapping: { 'Prénom': 'first_name' },
    validation_errors: [{ row: 1, column: 'email', message: 'E-mail invalide', data: null }], can_import: true,
  });
}

async function choisir(nom: string) {
  render(<ImportTableurModal onFermer={vi.fn()} onImporte={vi.fn()} />);
  const fenetre = screen.getByRole('dialog', { name: 'Importer des contacts depuis un tableur' });
  fireEvent.change(within(fenetre).getByLabelText(/Choisir un fichier/), { target: { files: [new File(['x'], nom)] } });
  await within(fenetre).findByText('2 lignes lues.');
  return fenetre;
}

describe('B-1442 : le numéro de ligne est celui du fichier', () => {
  it('CSV : la première ligne de données est la ligne 2 du tableur', async () => {
    apercu();
    const fenetre = await choisir('prospects.csv');
    expect(within(fenetre).getByText('Ligne 2 du tableur : E-mail invalide')).toBeInTheDocument();
  });

  it('JSON : le rang de l’élément', async () => {
    apercu();
    const fenetre = await choisir('prospects.json');
    expect(within(fenetre).getByText('Élément 1 : E-mail invalide')).toBeInTheDocument();
  });
});
