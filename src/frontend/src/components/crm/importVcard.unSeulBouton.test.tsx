/**
 * B-1381 (persona Nathalie, cycle 13) : les deux boutons « Importer (.vcf) »,
 * au Pipeline et dans Contacts, appelaient deux routes aux règles et aux
 * messages différents ; Contacts remplaçait en outre la raison d'un refus
 * (« Le fichier doit être au format .vcf ») par « L'import a échoué ». Les deux
 * écrans passent désormais par le même import et disent la raison d'un refus,
 * jamais le texte brut d'une exception.
 */
import { fireEvent, render, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import { useCRMStore } from '../../stores/crmStore';
import { useContactsStore } from '../../stores/contactsStore';
import { useStatusStore } from '../../stores/statusStore';

const api = vi.hoisted(() => ({ importVCFFile: vi.fn() }));

vi.mock('../../services/api/memory', async () => {
  const reel = await vi.importActual<typeof import('../../services/api/memory')>('../../services/api/memory');
  return {
    ...reel,
    listContacts: vi.fn().mockResolvedValue([]),
    searchMemory: vi.fn().mockResolvedValue({ contacts: [] }),
    importVCFFile: (...a: unknown[]) => api.importVCFFile(...a),
  };
});
vi.mock('../../services/api', async () => {
  const reel = await vi.importActual<typeof import('../../services/api')>('../../services/api');
  return {
    ...reel,
    listProjects: vi.fn().mockResolvedValue([]),
    listActivities: vi.fn().mockResolvedValue([]),
    listContactsWithScope: vi.fn().mockResolvedValue([]),
    listFiles: vi.fn().mockResolvedValue([]),
    getRGPDStats: vi.fn().mockResolvedValue(null),
    importVCFFile: (...a: unknown[]) => api.importVCFFile(...a),
  };
});
vi.mock('../../hooks', async () => {
  const reel = await vi.importActual<typeof import('../../hooks')>('../../hooks');
  return { ...reel, useDemoMask: () => ({ enabled: false, maskContact: (c: unknown) => c, maskText: (t: string) => t, populateMap: vi.fn() }) };
});

import { ImportVcardRefuse } from '../../services/api/memory';
import { MemoryPanel } from '../memory/MemoryPanel';
import { CRMPanel } from './CRMPanel';

const csv = new File(['nom;email\n'], 'prospects.csv', { type: 'text/csv' });

function deposer(ecran: 'crm' | 'contacts') {
  render(ecran === 'crm' ? <CRMPanel standalone /> : <MemoryPanel standalone />);
  const champ = document.querySelector<HTMLInputElement>('input[type="file"][accept=".vcf"]');
  if (!champ) throw new Error('champ de fichier introuvable');
  fireEvent.change(champ, { target: { files: [csv] } });
}

async function derniereErreur() {
  await waitFor(() => expect(useStatusStore.getState().notifications.some((n) => n.type === 'error')).toBe(true));
  return useStatusStore.getState().notifications.filter((n) => n.type === 'error').at(-1);
}

describe('B-1381 : un seul import vCard, qui dit pourquoi il refuse', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    useStatusStore.setState({ notifications: [] });
    useCRMStore.setState({ projects: [], activeTab: 'pipeline' });
    useContactsStore.setState({ contacts: [], loaded: true, loading: false, error: null, selectedContactId: null, truncated: false });
  });

  it.each(['crm', 'contacts'] as const)('%s : le refus du moteur est dit tel quel', async (ecran) => {
    api.importVCFFile.mockRejectedValue(new ImportVcardRefuse('Le fichier doit être au format .vcf'));
    deposer(ecran);

    const erreur = await derniereErreur();
    expect(api.importVCFFile).toHaveBeenCalledWith(csv);
    expect(erreur?.title).toBe('Import VCF');
    expect(erreur?.message).toBe('Le fichier doit être au format .vcf');
  });

  it.each(['crm', 'contacts'] as const)('%s : une panne technique ne montre pas le texte brut', async (ecran) => {
    api.importVCFFile.mockRejectedValue(new Error('TypeError: Failed to fetch'));
    deposer(ecran);

    const erreur = await derniereErreur();
    expect(erreur?.message).toBe('L’import a échoué. Vérifie le fichier et réessaie.');
  });
});
