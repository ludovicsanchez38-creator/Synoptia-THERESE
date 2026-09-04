import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import { FileBrowser } from './FileBrowser';

const mocks = vi.hoisted(() => ({
  getWorkingDirectory: vi.fn(),
  indexFile: vi.fn(),
  listFiles: vi.fn(),
  open: vi.fn(),
  readDir: vi.fn(),
  stat: vi.fn(),
}));

vi.mock('../../services/api', () => ({
  getWorkingDirectory: mocks.getWorkingDirectory,
  indexFile: mocks.indexFile,
  listFiles: mocks.listFiles,
}));

vi.mock('@tauri-apps/plugin-fs', () => ({
  readDir: mocks.readDir,
  stat: mocks.stat,
}));

vi.mock('@tauri-apps/api/path', () => ({
  homeDir: vi.fn().mockResolvedValue('/Users/ludo'),
  resolve: vi.fn(async (...parts: string[]) => parts.join('/')),
}));

vi.mock('@tauri-apps/plugin-dialog', () => ({ open: mocks.open }));

vi.mock('../../lib/utils', async () => {
  const actual = await vi.importActual<typeof import('../../lib/utils')>('../../lib/utils');
  return { ...actual, isTauri: () => true };
});

const dossierConfigure = '/Volumes/Clients/Synoptia';

const metadata = {
  id: 'file-319',
  path: `${dossierConfigure}/brief.md`,
  name: 'brief.md',
  extension: '.md',
  size: 42,
  mime_type: 'text/markdown',
  chunk_count: 3,
  indexed_at: '2026-09-04T08:00:00Z',
  created_at: '2026-09-04T08:00:00Z',
};

beforeEach(() => {
  vi.clearAllMocks();
  mocks.getWorkingDirectory.mockResolvedValue({ path: dossierConfigure, exists: true });
  mocks.listFiles.mockResolvedValue([]);
  mocks.stat.mockResolvedValue({ size: 42 });
});

describe('B-318 : dossier configuré hors du home', () => {
  it('ne revient pas silencieusement au home et propose de renouveler l’autorisation', async () => {
    mocks.readDir.mockRejectedValueOnce(new Error('forbidden path'));

    render(<FileBrowser />);

    expect(await screen.findByRole('alert')).toHaveTextContent(dossierConfigure);
    expect(screen.getByRole('button', { name: 'Autoriser ce dossier' })).toBeInTheDocument();
    expect(mocks.readDir).toHaveBeenCalledTimes(1);
    expect(mocks.readDir).not.toHaveBeenCalledWith('/Users/ludo');
  });

  it('relit le dossier après sa sélection explicite', async () => {
    mocks.readDir
      .mockRejectedValueOnce(new Error('scope lost'))
      .mockResolvedValueOnce([{ name: 'brief.md', isDirectory: false }]);
    mocks.open.mockResolvedValue(dossierConfigure);

    render(<FileBrowser />);

    fireEvent.click(await screen.findByRole('button', { name: 'Autoriser ce dossier' }));

    expect(await screen.findByText('brief.md')).toBeInTheDocument();
    expect(mocks.open).toHaveBeenCalledWith(expect.objectContaining({
      directory: true,
      defaultPath: dossierConfigure,
    }));
    expect(mocks.readDir).toHaveBeenLastCalledWith(dossierConfigure);
  });
});

describe('B-319 : retour visible de l’indexation', () => {
  beforeEach(() => {
    mocks.readDir.mockResolvedValue([{ name: 'brief.md', isDirectory: false }]);
  });

  it('affiche l’état persistant déjà connu du serveur', async () => {
    mocks.listFiles.mockResolvedValue([metadata]);

    render(<FileBrowser />);

    expect(await screen.findByText('Indexé · 3 fragments')).toBeInTheDocument();
  });

  it('confirme l’indexation et conserve le nombre de fragments dans la ligne', async () => {
    mocks.indexFile.mockResolvedValue({ ...metadata, chunk_count: 4 });

    render(<FileBrowser />);

    fireEvent.click(await screen.findByTitle('Indexer ce fichier'));

    await waitFor(() => {
      expect(screen.getByRole('status')).toHaveTextContent('brief.md');
      expect(screen.getByRole('status')).toHaveTextContent('4 fragments');
    });
    expect(screen.getByText('Indexé · 4 fragments')).toBeInTheDocument();
    expect(screen.getByTitle('Réindexer ce fichier')).toBeInTheDocument();
  });
});
