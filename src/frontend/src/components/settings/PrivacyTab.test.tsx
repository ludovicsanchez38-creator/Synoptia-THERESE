import { fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { grantCloudConsent, hasCloudConsent } from '../../lib/consent';
import { PrivacyTab } from './PrivacyTab';
import {
  createBackup,
  deleteAllData,
  downloadAllData,
  listBackups,
  restoreBackup,
} from '../../services/api/data';

vi.mock('./VoiceLocalSection', () => ({
  VoiceLocalSection: () => <div>Voix locale</div>,
}));

vi.mock('../../services/api/rgpd', () => ({
  getPurgeSettings: vi.fn().mockResolvedValue({ enabled: true, months: 36 }),
  updatePurgeSettings: vi.fn().mockResolvedValue(undefined),
}));

vi.mock('../../services/api/data', () => ({
  downloadAllData: vi.fn(),
  listBackups: vi.fn(),
  createBackup: vi.fn(),
  restoreBackup: vi.fn(),
  deleteBackup: vi.fn(),
  deleteAllData: vi.fn(),
}));

const backup = {
  backup_name: 'therese_backup_20260714_120000',
  created_at: '2026-07-14T12:00:00Z',
  size_bytes: 1_048_576,
};

describe('PrivacyTab - opérations globales', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(listBackups).mockResolvedValue([backup]);
    vi.mocked(downloadAllData).mockResolvedValue('desktop_saved');
    vi.mocked(createBackup).mockResolvedValue({
      success: true,
      backup_name: backup.backup_name,
      path: '/tmp/backup.tar.gz',
      created_at: backup.created_at,
      included: ['therese.db'],
    });
    vi.mocked(restoreBackup).mockResolvedValue({
      success: true,
      restored_from: backup.backup_name,
      restored_at: backup.created_at,
      safety_backup: 'pre_restore_20260714_120001',
      note: 'Redémarre l’application',
    });
    vi.mocked(deleteAllData).mockResolvedValue({
      deleted: true,
      message: 'Supprimé',
      note: 'Logs conservés',
    });
  });

  it('expose export, sauvegarde, restauration confirmée et effacement doublement confirmé', async () => {
    render(<PrivacyTab />);

    const exportButton = await screen.findByRole('button', { name: 'Exporter toutes mes données' });
    fireEvent.click(exportButton);
    await waitFor(() => expect(downloadAllData).toHaveBeenCalledOnce());

    // US-003 : la sauvegarde exige une passphrase de chiffrement.
    fireEvent.change(screen.getByLabelText('Passphrase de chiffrement de la sauvegarde'), { target: { value: 'ma-passphrase' } });
    fireEvent.click(screen.getByRole('button', { name: 'Créer une sauvegarde' }));
    await waitFor(() => expect(createBackup).toHaveBeenCalledWith('ma-passphrase'));

    fireEvent.click(screen.getByRole('button', { name: 'Restaurer' }));
    expect(screen.getByText(/remplace l’état courant/)).toBeInTheDocument();
    fireEvent.change(screen.getByLabelText('Passphrase de la sauvegarde à restaurer'), { target: { value: 'ma-passphrase' } });
    fireEvent.click(screen.getByRole('button', { name: 'Confirmer la restauration' }));
    await waitFor(() => expect(restoreBackup).toHaveBeenCalledWith(backup.backup_name, 'ma-passphrase'));

    fireEvent.click(screen.getByRole('button', { name: 'Préparer la suppression' }));
    const confirmation = screen.getByLabelText('Saisis SUPPRIMER pour confirmer');
    fireEvent.change(confirmation, { target: { value: 'SUPPRIMER' } });
    fireEvent.click(screen.getByRole('button', { name: 'Supprimer définitivement' }));
    await waitFor(() => expect(deleteAllData).toHaveBeenCalledOnce());
  });

  it('après effacement global, annonce honnêtement les sauvegardes conservées (revue 0.40)', async () => {
    vi.mocked(deleteAllData).mockResolvedValue({
      deleted: true,
      message: 'Toutes tes données ont été supprimées conformément au RGPD Art. 17',
      note: 'Les logs d’audit sont conservés. 2 sauvegarde(s) conservée(s) : supprime-les depuis la liste des sauvegardes si tu veux vraiment tout effacer.',
      backups_kept: 2,
    });
    render(<PrivacyTab />);

    fireEvent.click(await screen.findByRole('button', { name: 'Préparer la suppression' }));
    fireEvent.change(screen.getByLabelText('Saisis SUPPRIMER pour confirmer'), { target: { value: 'SUPPRIMER' } });
    fireEvent.click(screen.getByRole('button', { name: 'Supprimer définitivement' }));

    await waitFor(() => expect(deleteAllData).toHaveBeenCalledOnce());
    expect(await screen.findByText(/2 sauvegarde\(s\) conservée\(s\)/)).toBeInTheDocument();
  });
});

describe('PrivacyTab - consentements cloud (revue 0.40)', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(listBackups).mockResolvedValue([]);
    // Le setup global mocke localStorage sans persistance : on installe une
    // mémoire réelle pour que grant/revoke se relisent.
    const store: Record<string, string> = {};
    vi.stubGlobal('localStorage', {
      getItem: (k: string) => store[k] ?? null,
      setItem: (k: string, v: string) => {
        store[k] = v;
      },
      removeItem: (k: string) => {
        delete store[k];
      },
      clear: () => {
        for (const k of Object.keys(store)) delete store[k];
      },
    });
  });

  afterEach(() => vi.unstubAllGlobals());

  it('permet d’autoriser la dictée cloud Groq depuis les réglages (fin de l’impasse)', async () => {
    render(<PrivacyTab />);

    expect(await screen.findByText('Consentements cloud')).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: 'Autoriser la dictée cloud (Groq)' }));

    expect(hasCloudConsent('voice', 'Groq')).toBe(true);
    // Le consentement accordé apparaît dans la liste avec sa révocation.
    expect(await screen.findByText('Audio de la dictée')).toBeInTheDocument();
  });

  it('révoque un consentement sans toucher les autres', async () => {
    grantCloudConsent('voice', 'Groq', ['audio de la dictée']);
    grantCloudConsent('llm', 'openai', ['messages']);
    render(<PrivacyTab />);

    const row = (await screen.findByText('Audio de la dictée')).closest('li');
    expect(row).not.toBeNull();
    fireEvent.click(within(row as HTMLElement).getByRole('button', { name: 'Révoquer' }));

    expect(hasCloudConsent('voice', 'Groq')).toBe(false);
    expect(hasCloudConsent('llm', 'openai')).toBe(true);
  });
});
