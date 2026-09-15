/**
 * B-815 (cycle 9) : le résultat de « Vérifier les mises à jour » n'était dans
 * aucune région live ; un lecteur d'écran ne l'entendait pas.
 */
import { fireEvent, render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

vi.mock('@tauri-apps/plugin-shell', () => ({ open: vi.fn() }));
vi.mock('../../services/api', () => ({ checkHealth: vi.fn().mockResolvedValue({ version: '0.73.0', status: 'healthy' }) }));
import { useBackendStore } from '../../hooks/useBackend';
import { AboutTab } from './AboutTab';

describe('AboutTab - B-815, le résultat de la vérification est annoncé', () => {
  beforeEach(() => {
    useBackendStore.setState({ version: '0.73.0' });
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: true, json: async () => [{ tag_name: 'v0.73.0-alpha', name: 'x', html_url: 'https://example.test', published_at: '2026-09-15T00:00:00Z', body: '', assets: [] }] }));
  });

  it('« à jour » vit dans une région status', async () => {
    render(<AboutTab />);
    fireEvent.click(screen.getByRole('button', { name: /Vérifier les mises à jour/ }));
    const statut = await screen.findByRole('status');
    expect(statut).toHaveTextContent(/THÉRÈSE est à jour/);
  });
});
