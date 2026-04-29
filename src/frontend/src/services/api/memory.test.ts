import { beforeEach, describe, expect, it, vi } from 'vitest';
import { downloadDir } from '@tauri-apps/api/path';
import { exists, writeFile } from '@tauri-apps/plugin-fs';

const mockApiFetch = vi.fn();

vi.mock('./core', async () => {
  const actual = await vi.importActual<typeof import('./core')>('./core');
  return {
    ...actual,
    API_BASE: 'http://127.0.0.1:17293',
    apiFetch: (...args: unknown[]) => mockApiFetch(...args),
  };
});

import { downloadVCFFile } from './memory';

describe('downloadVCFFile', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    delete (window as unknown as { __TAURI__?: boolean }).__TAURI__;
    vi.mocked(downloadDir).mockResolvedValue('/home/test/Downloads');
    vi.mocked(exists).mockResolvedValue(false);
    vi.mocked(writeFile).mockResolvedValue(undefined);
  });

  it('écrit le VCF dans Téléchargements en runtime Tauri', async () => {
    (window as unknown as { __TAURI__: boolean }).__TAURI__ = true;

    mockApiFetch.mockResolvedValueOnce({
      ok: true,
      headers: new Headers({ 'Content-Disposition': 'attachment; filename="therese-contacts.vcf"' }),
      blob: () => Promise.resolve({
        arrayBuffer: async () => new TextEncoder().encode('BEGIN:VCARD\nFN:Test').buffer,
      }),
    });

    await expect(downloadVCFFile()).resolves.toBe('desktop_saved');
    expect(writeFile).toHaveBeenCalledWith(
      '/home/test/Downloads/therese-contacts.vcf',
      expect.any(Uint8Array)
    );
  });

  it('évite d écraser un export existant dans Téléchargements', async () => {
    (window as unknown as { __TAURI__: boolean }).__TAURI__ = true;
    vi.mocked(exists)
      .mockResolvedValueOnce(true)
      .mockResolvedValueOnce(false);

    mockApiFetch.mockResolvedValueOnce({
      ok: true,
      headers: new Headers({ 'Content-Disposition': 'attachment; filename="therese-contacts.vcf"' }),
      blob: () => Promise.resolve({
        arrayBuffer: async () => new TextEncoder().encode('BEGIN:VCARD\nFN:Test').buffer,
      }),
    });

    await expect(downloadVCFFile()).resolves.toBe('desktop_saved');
    expect(writeFile).toHaveBeenCalledWith(
      '/home/test/Downloads/therese-contacts-2.vcf',
      expect.any(Uint8Array)
    );
  });

  it('propage une erreur visible si l écriture Tauri échoue sans fallback web', async () => {
    (window as unknown as { __TAURI__: boolean }).__TAURI__ = true;
    vi.mocked(writeFile).mockRejectedValueOnce(new Error('disk full'));
    const createObjectURLSpy = vi.spyOn(URL, 'createObjectURL');

    mockApiFetch.mockResolvedValueOnce({
      ok: true,
      headers: new Headers(),
      blob: () => Promise.resolve({
        arrayBuffer: async () => new TextEncoder().encode('BEGIN:VCARD').buffer,
      }),
    });

    await expect(downloadVCFFile()).rejects.toThrow('disk full');
    expect(createObjectURLSpy).not.toHaveBeenCalled();

    createObjectURLSpy.mockRestore();
  });

  it('démarre un téléchargement navigateur hors runtime Tauri', async () => {
    const blob = new Blob(['BEGIN:VCARD\nFN:Test'], { type: 'text/vcard' });
    const createObjectURLSpy = vi.spyOn(URL, 'createObjectURL').mockReturnValue('blob:vcf');
    const revokeObjectURLSpy = vi.spyOn(URL, 'revokeObjectURL').mockImplementation(() => undefined);
    const clickSpy = vi.spyOn(HTMLAnchorElement.prototype, 'click').mockImplementation(() => undefined);

    mockApiFetch.mockResolvedValueOnce({
      ok: true,
      headers: new Headers({ 'Content-Disposition': 'attachment; filename="therese-contacts.vcf"' }),
      blob: () => Promise.resolve(blob),
    });

    await expect(downloadVCFFile()).resolves.toBe('browser_download_started');
    expect(createObjectURLSpy).toHaveBeenCalledWith(blob);
    expect(clickSpy).toHaveBeenCalledTimes(1);
    expect(revokeObjectURLSpy).toHaveBeenCalledWith('blob:vcf');

    clickSpy.mockRestore();
    revokeObjectURLSpy.mockRestore();
    createObjectURLSpy.mockRestore();
  });

  it('remonte une ApiError quand l export backend échoue', async () => {
    mockApiFetch.mockResolvedValueOnce({
      ok: false,
      status: 500,
      statusText: 'Internal Server Error',
      json: () => Promise.resolve({ detail: 'backend cassé' }),
    });

    await expect(downloadVCFFile()).rejects.toEqual(
      expect.objectContaining({
        name: 'ApiError',
        message: 'backend cassé',
      })
    );
  });
});
