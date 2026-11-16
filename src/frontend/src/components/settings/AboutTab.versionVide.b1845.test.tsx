/**
 * B-1845 : tant que la version du store est vide, la vérification la remplace
 * par 0.0.0. Toute publication GitHub devient alors une mise à jour.
 */
import { fireEvent, render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

const checkHealth = vi.hoisted(() => vi.fn());
vi.mock('@tauri-apps/plugin-shell', () => ({ open: vi.fn() }));
vi.mock('../../services/api', () => ({ checkHealth }));

import { useBackendStore } from '../../hooks/useBackend';
import { AboutTab } from './AboutTab';

const publication = {
  tag_name: 'v0.9.0',
  name: 'v0.9.0',
  html_url: 'https://exemple.test/versions',
  published_at: '2026-11-01T00:00:00Z',
  body: '',
  assets: [],
};

describe('B-1845 : une version inconnue n’est pas 0.0.0', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    useBackendStore.setState({ version: null, status: 'disconnected', error: null, lastCheck: null });
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
      ok: true,
      json: async () => [publication],
    }));
  });

  it('n’annonce pas de mise à jour tant que la version installée est inconnue', async () => {
    checkHealth.mockImplementation(() => new Promise(() => {}));
    render(<AboutTab />);
    fireEvent.click(screen.getByRole('button', { name: /Vérifier les mises à jour/ }));
    expect(await screen.findByRole('alert')).toHaveTextContent(/version installée/);
    expect(screen.queryByText(/Nouvelle version disponible/)).toBeNull();
    expect(fetch).not.toHaveBeenCalled();
  });

  it('explique l’échec quand le moteur ne donne pas la version', async () => {
    checkHealth.mockRejectedValue(new Error('moteur injoignable'));
    render(<AboutTab />);
    expect(await screen.findByRole('alert')).toHaveTextContent(/version installée/);
    fireEvent.click(screen.getByRole('button', { name: /Vérifier les mises à jour/ }));
    expect(screen.queryByText(/Nouvelle version disponible/)).toBeNull();
    expect(fetch).not.toHaveBeenCalled();
  });
});
