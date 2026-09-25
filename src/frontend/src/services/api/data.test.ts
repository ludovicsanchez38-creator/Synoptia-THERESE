import { beforeEach, describe, expect, it, vi } from 'vitest';
import { save } from '@tauri-apps/plugin-dialog';
import { writeFile } from '@tauri-apps/plugin-fs';

const mockApiFetch = vi.fn();
const mockRequest = vi.fn();

vi.mock('./core', async () => {
  const actual = await vi.importActual<typeof import('./core')>('./core');
  return {
    ...actual,
    API_BASE: 'http://127.0.0.1:17293',
    apiFetch: (...args: unknown[]) => mockApiFetch(...args),
    request: (...args: unknown[]) => mockRequest(...args),
  };
});

import { deleteAllData, downloadAllData } from './data';

describe('data API', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    delete (window as unknown as { __TAURI__?: boolean }).__TAURI__;
  });

  it('enregistre l’export global choisi dans l’application desktop', async () => {
    (window as unknown as { __TAURI__: boolean }).__TAURI__ = true;
    vi.mocked(save).mockResolvedValue('/tmp/therese-export.json');
    vi.mocked(writeFile).mockResolvedValue(undefined);
    mockApiFetch.mockResolvedValue({
      ok: true,
      headers: new Headers({
        'Content-Disposition': 'attachment; filename="therese-export-20260714.json"',
      }),
      blob: () => Promise.resolve({
        arrayBuffer: async () => new TextEncoder().encode('{"contacts":[]}').buffer,
      }),
    });

    await expect(downloadAllData()).resolves.toBe('desktop_saved');
    // B-385 : l'export intégral n'est pas borné par le délai de 30 s d'apiFetch
    expect(mockApiFetch).toHaveBeenCalledWith('http://127.0.0.1:17293/api/data/export', { timeoutMs: null });
    expect(writeFile).toHaveBeenCalledWith('/tmp/therese-export.json', expect.any(Uint8Array));
  });

  it('déclenche un téléchargement standard dans le prototype navigateur', async () => {
    const blob = new Blob(['{}'], { type: 'application/json' });
    const createObjectURL = vi.spyOn(URL, 'createObjectURL').mockReturnValue('blob:data-export');
    const revokeObjectURL = vi.spyOn(URL, 'revokeObjectURL').mockImplementation(() => undefined);
    const click = vi.spyOn(HTMLAnchorElement.prototype, 'click').mockImplementation(() => undefined);
    mockApiFetch.mockResolvedValue({
      ok: true,
      headers: new Headers(),
      blob: () => Promise.resolve(blob),
    });

    await expect(downloadAllData()).resolves.toBe('browser_download_started');
    expect(createObjectURL).toHaveBeenCalledWith(blob);
    expect(click).toHaveBeenCalledOnce();
    expect(revokeObjectURL).toHaveBeenCalledWith('blob:data-export');

    createObjectURL.mockRestore();
    revokeObjectURL.mockRestore();
    click.mockRestore();
  });

  it('B-1250 : la purge totale n’abandonne pas au bout de 30 s', async () => {
    // Elle attend désormais l'indexation en vol (B-1249, jusqu'à ~19 s) avant
    // d'effacer : le délai client par défaut annonçait un échec pendant que
    // la purge aboutissait.
    mockRequest.mockResolvedValue({ deleted: true, message: 'ok', note: '' });
    await deleteAllData();
    const [chemin, options] = mockRequest.mock.calls[0] as [string, { timeoutMs?: number | null }];
    expect({ chemin, timeoutMs: options.timeoutMs }).toEqual({ chemin: '/api/data/all?confirm=true', timeoutMs: null });
  });
});
