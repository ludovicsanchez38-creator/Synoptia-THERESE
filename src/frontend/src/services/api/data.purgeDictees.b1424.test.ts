/**
 * B-1424, second volet : « Effacer toutes mes données » laissait les
 * enregistrements de dictée du greffon micro
 * (`app_data_dir/tauri-plugin-mic-recorder/`), hors du dossier de THÉRÈSE que
 * purge le moteur.
 */
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

const { remove, request } = vi.hoisted(() => ({ remove: vi.fn(), request: vi.fn() }));

vi.mock('@tauri-apps/plugin-fs', () => ({ remove, BaseDirectory: { AppData: 14 } }));
vi.mock('./core', async () => {
  const reel = await vi.importActual<Record<string, unknown>>('./core');
  return { ...reel, request };
});

import { deleteAllData } from './data';

describe('B-1424 : la purge totale efface les dictées conservées', () => {
  beforeEach(() => {
    (window as unknown as Record<string, unknown>).__TAURI_INTERNALS__ = {};
    remove.mockReset().mockResolvedValue(undefined);
    request.mockReset();
  });
  afterEach(() => {
    delete (window as unknown as Record<string, unknown>).__TAURI_INTERNALS__;
  });

  it('après une purge réussie, le dossier du greffon part', async () => {
    request.mockResolvedValue({ deleted: true, message: 'ok', note: '' });
    await deleteAllData();
    expect(remove).toHaveBeenCalledWith('tauri-plugin-mic-recorder', { baseDir: 14, recursive: true });
  });

  it('une purge refusée ne touche à rien', async () => {
    request.mockRejectedValue(new Error('refus'));
    await expect(deleteAllData()).rejects.toThrow('refus');
    expect(remove).not.toHaveBeenCalled();
  });

  it('un dossier absent ne fait pas échouer la purge', async () => {
    request.mockResolvedValue({ deleted: true, message: 'ok', note: '' });
    remove.mockRejectedValue(new Error('No such file or directory'));
    await expect(deleteAllData()).resolves.toMatchObject({ deleted: true });
  });

  it('hors application de bureau, rien n’est tenté', async () => {
    delete (window as unknown as Record<string, unknown>).__TAURI_INTERNALS__;
    request.mockResolvedValue({ deleted: true, message: 'ok', note: '' });
    await deleteAllData();
    expect(remove).not.toHaveBeenCalled();
  });
});
