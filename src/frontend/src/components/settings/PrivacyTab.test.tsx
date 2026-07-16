import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
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
});
