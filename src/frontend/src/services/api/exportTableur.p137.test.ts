/**
 * P-137 (persona Nathalie, cycle 13) : le moteur sait exporter les contacts
 * en tableur avec leurs étapes (`POST /api/crm/export/contacts`), aucune
 * surface ne l'appelait. L'export se range dans Téléchargements comme le vCard.
 */
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { downloadDir } from '@tauri-apps/api/path';
import { exists, writeFile } from '@tauri-apps/plugin-fs';

const mockApiFetch = vi.fn();
vi.mock('./core', async () => {
  const actual = await vi.importActual<typeof import('./core')>('./core');
  return { ...actual, API_BASE: 'http://127.0.0.1:17293', apiFetch: (...args: unknown[]) => mockApiFetch(...args) };
});

import { downloadContactsTableur } from './memory';

describe('P-137 : export des contacts en tableur', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    (window as unknown as { __TAURI__: boolean }).__TAURI__ = true;
    vi.mocked(downloadDir).mockResolvedValue('/home/test/Downloads');
    vi.mocked(exists).mockResolvedValue(false);
    vi.mocked(writeFile).mockResolvedValue(undefined);
  });

  it('demande un classeur Excel au moteur et le range dans Téléchargements', async () => {
    mockApiFetch.mockResolvedValueOnce({
      ok: true,
      headers: new Headers({ 'Content-Disposition': 'attachment; filename="contacts_20260925_1630.xlsx"' }),
      blob: () => Promise.resolve({ arrayBuffer: async () => new Uint8Array([80, 75]).buffer }),
    });
    await expect(downloadContactsTableur()).resolves.toBe('desktop_saved');
    expect(mockApiFetch).toHaveBeenCalledWith(
      'http://127.0.0.1:17293/api/crm/export/contacts?format=xlsx',
      expect.objectContaining({ method: 'POST' }),
    );
    expect(writeFile).toHaveBeenCalledWith('/home/test/Downloads/contacts_20260925_1630.xlsx', expect.any(Uint8Array));
  });

  it('un refus du moteur remonte en erreur', async () => {
    mockApiFetch.mockResolvedValueOnce({ ok: false, status: 500, statusText: 'x', json: async () => ({ detail: 'panne' }) });
    await expect(downloadContactsTableur()).rejects.toThrow();
    expect(writeFile).not.toHaveBeenCalled();
  });
});
