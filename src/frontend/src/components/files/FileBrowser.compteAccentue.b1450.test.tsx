/** B-1450 (recette P-146, lot 3, KO-8) : le pied du navigateur de fichiers
 *  écrivait « 0 elements », sans accent ni accord. */
import { render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

vi.mock('../../services/api', () => ({
  getWorkingDirectory: vi.fn(), indexFile: vi.fn(), listFiles: vi.fn().mockResolvedValue([]),
}));
vi.mock('@tauri-apps/api/path', () => ({ homeDir: vi.fn(() => Promise.reject(new TypeError('invoke'))), resolve: vi.fn() }));
vi.mock('@tauri-apps/plugin-fs', () => ({ readDir: vi.fn(() => Promise.reject(new TypeError('invoke'))), stat: vi.fn() }));
vi.mock('@tauri-apps/plugin-dialog', () => ({ open: vi.fn(() => Promise.reject(new TypeError('invoke'))) }));
vi.mock('../../lib/utils', async () => {
  const actual = await vi.importActual<typeof import('../../lib/utils')>('../../lib/utils');
  return { ...actual, isTauri: () => false };
});

import { FileBrowser } from './FileBrowser';

describe('B-1450 : le compte des éléments est accentué et accordé', () => {
  it('dit « 0 élément »', async () => {
    render(<FileBrowser />);
    expect(await screen.findByText('0 élément')).toBeInTheDocument();
    expect(screen.queryByText(/elements/)).toBeNull();
  });
});
