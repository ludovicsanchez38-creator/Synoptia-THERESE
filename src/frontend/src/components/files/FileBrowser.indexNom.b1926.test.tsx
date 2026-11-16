/**
 * B-1926 : le bouton d'indexation n'a qu'un title. Le nom accessible doit
 * être un aria-label. Le masquage hors survol reste en place.
 */
import { render, screen } from '@testing-library/react';
import { beforeEach, expect, it, vi } from 'vitest';
import { FileBrowser } from './FileBrowser';

const mocks = vi.hoisted(() => ({
  getWorkingDirectory: vi.fn(),
  indexFile: vi.fn(),
  listFiles: vi.fn(),
  readDir: vi.fn(),
  stat: vi.fn(),
}));

vi.mock('../../services/api', () => ({
  getWorkingDirectory: mocks.getWorkingDirectory,
  indexFile: mocks.indexFile,
  listFiles: mocks.listFiles,
}));
vi.mock('@tauri-apps/plugin-fs', () => ({ readDir: mocks.readDir, stat: mocks.stat }));
vi.mock('@tauri-apps/api/path', () => ({
  homeDir: vi.fn().mockResolvedValue('/Users/ludo'),
  resolve: vi.fn(async (...parts: string[]) => parts.join('/')),
}));
vi.mock('@tauri-apps/plugin-dialog', () => ({ open: vi.fn() }));
vi.mock('../../lib/utils', async () => {
  const reel = await vi.importActual<typeof import('../../lib/utils')>('../../lib/utils');
  return { ...reel, isTauri: () => true };
});

const dossier = '/Volumes/Clients/Synoptia';

beforeEach(() => {
  vi.clearAllMocks();
  mocks.getWorkingDirectory.mockResolvedValue({ path: dossier, exists: true });
  mocks.stat.mockResolvedValue({ size: 42 });
  mocks.readDir.mockResolvedValue([{ name: 'brief.md', isDirectory: false }]);
  mocks.listFiles.mockResolvedValue([]);
});

it('B-1926 : Indexer ce fichier a un aria-label', async () => {
  render(<FileBrowser />);
  const bouton = await screen.findByRole('button', { name: 'Indexer ce fichier' });
  expect(bouton).toHaveAttribute('aria-label', 'Indexer ce fichier');
});

it('B-1926 : Réindexer ce fichier a un aria-label', async () => {
  mocks.listFiles.mockResolvedValue([{
    id: 'file-319',
    path: `${dossier}/brief.md`,
    name: 'brief.md',
    extension: '.md',
    size: 42,
    mime_type: 'text/markdown',
    chunk_count: 3,
    indexed_at: '2026-09-04T08:00:00Z',
    created_at: '2026-09-04T08:00:00Z',
  }]);
  render(<FileBrowser />);
  const bouton = await screen.findByRole('button', { name: 'Réindexer ce fichier' });
  expect(bouton).toHaveAttribute('aria-label', 'Réindexer ce fichier');
});
