import { fireEvent, render, screen } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

vi.mock('../../services/api', () => ({
  checkHealth: vi.fn().mockResolvedValue({ version: '0.83.0', status: 'healthy' }),
}));
import { useBackendStore } from '../../hooks/useBackend';
import { checkHealth } from '../../services/api';
import { AboutTab } from './AboutTab';

describe('R1-1 : numéro sans identification de livraison', () => {
  beforeEach(() => {
    useBackendStore.getState().reset();
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
      ok: true,
      json: async () => [{ tag_name: 'v0.83.0-alpha.2', assets: [] }],
    }));
  });
  afterEach(() => vi.unstubAllGlobals());

  it.each([
    ['0.83.0', 'v0.83.0-alpha.2'],
    ['0.83.0', 'v0.83.0'],
    ['0.83.0+build.9', 'v0.83.0+autre'],
  ])('reconnaît le même numéro pour %s et %s', async (version, tag) => {
    vi.mocked(checkHealth).mockResolvedValueOnce({ version, status: 'healthy' });
    vi.mocked(fetch).mockResolvedValue({
      ok: true,
      json: async () => [{ tag_name: tag, assets: [] }],
    } as Response);
    render(<AboutTab />);
    await screen.findByText(version);
    fireEvent.click(screen.getByRole('button', { name: 'Vérifier les mises à jour' }));
    expect(await screen.findByText(/THÉRÈSE est à jour/)).toBeInTheDocument();
    expect(screen.queryByText(/Nouvelle version disponible/)).not.toBeInTheDocument();
    expect(screen.queryByRole('alert')).not.toBeInTheDocument();
  });
});
