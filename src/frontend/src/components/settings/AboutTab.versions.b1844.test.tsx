/**
 * B-1844 : comparer 0.9.0-alpha.1, 0.9.0-alpha.2 et 0.9.0 comme égaux, ou
 * lire 1.2.4-rc.1 comme 1.2.0.1, annonce « à jour » ou une mise à jour à tort.
 */
import { fireEvent, render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

vi.mock('@tauri-apps/plugin-shell', () => ({ open: vi.fn() }));
vi.mock('../../services/api', () => ({ checkHealth: vi.fn().mockResolvedValue({ version: '0.83.0', status: 'healthy' }) }));

import { useBackendStore } from '../../hooks/useBackend';
import { AboutTab } from './AboutTab';

function release(tag: string) {
  return {
    tag_name: tag,
    name: tag,
    html_url: 'https://exemple.test/versions',
    published_at: '2026-11-01T00:00:00Z',
    body: '',
    assets: [],
  };
}

async function verifier(version: string, tag: string) {
  useBackendStore.setState({ version, status: 'connected', error: null, lastCheck: null });
  vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
    ok: true,
    json: async () => [release(tag)],
  }));
  render(<AboutTab />);
  fireEvent.click(screen.getByRole('button', { name: /Vérifier les mises à jour/ }));
}

describe('B-1844 : les préversions ne se confondent pas', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('0.9.0-alpha.2 est une mise à jour de 0.9.0-alpha.1', async () => {
    await verifier('0.9.0-alpha.1', 'v0.9.0-alpha.2');
    expect(await screen.findByText(/Nouvelle version disponible/)).toBeInTheDocument();
    expect(screen.queryByText(/THÉRÈSE est à jour/)).toBeNull();
  });

  it('une version finale dépasse la préversion du même numéro', async () => {
    await verifier('0.9.0-alpha.2', 'v0.9.0');
    expect(await screen.findByText(/Nouvelle version disponible/)).toBeInTheDocument();
  });

  it('1.2.4-rc.1 n’est pas en retard sur 1.2.1', async () => {
    await verifier('1.2.4-rc.1', 'v1.2.1');
    expect(await screen.findByText(/THÉRÈSE est à jour/)).toBeInTheDocument();
    expect(screen.queryByText(/Nouvelle version disponible/)).toBeNull();
  });

  it.each(['v0.85.0-beta', 'v0.85.0-beta.1'])('reconnaît le même numéro pour %s', async (tag) => {
    await verifier('0.85.0', tag);
    expect(await screen.findByText(/THÉRÈSE est à jour/)).toBeInTheDocument();
    expect(screen.queryByRole('alert')).toBeNull();
  });

  it('1.0.0 est proposée à une installation en 0.85.0', async () => {
    await verifier('0.85.0', 'v1.0.0');
    expect(await screen.findByText('Nouvelle version disponible : v1.0.0')).toBeInTheDocument();
  });

  it('la même livraison alpha, avec ou sans suffixe, reste à jour', async () => {
    await verifier('0.83.0', 'v0.83.0-alpha');
    expect(await screen.findByText(/THÉRÈSE est à jour/)).toBeInTheDocument();
  });
});
