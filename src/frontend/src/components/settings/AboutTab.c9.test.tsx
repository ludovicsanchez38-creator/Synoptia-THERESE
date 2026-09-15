/**
 * B-763 (cycle 9) : « Voir toutes les versions sur GitHub » appelait open() du
 * greffon shell sans renvoyer sa promesse ; hors Tauri, le rejet n'atteignait
 * jamais le catch et le repli window.open ne tournait pas. Le bouton voisin
 * (téléchargement) faisait déjà le bon geste, et son commentaire l'explique.
 */
import { fireEvent, render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { open } from '@tauri-apps/plugin-shell';

vi.mock('@tauri-apps/plugin-shell', () => ({ open: vi.fn() }));
vi.mock('../../services/api', () => ({ checkHealth: vi.fn().mockResolvedValue({ version: '0.73.0', status: 'healthy' }) }));

import { useBackendStore } from '../../hooks/useBackend';
import { AboutTab } from './AboutTab';

const release = {
  tag_name: 'v9.9.9-alpha', name: 'THÉRÈSE v9.9.9-alpha',
  html_url: 'https://github.com/ludovicsanchez38-creator/Synoptia-THERESE/releases/tag/v9.9.9-alpha',
  published_at: '2026-09-15T00:00:00Z', body: '', assets: [],
};

describe('AboutTab - B-763, la page des versions s’ouvre aussi hors Tauri', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    useBackendStore.setState({ version: '0.73.0' });
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: true, json: async () => [release] }));
    vi.mocked(open).mockRejectedValue(new TypeError("Cannot read properties of undefined (reading 'invoke')"));
    window.open = vi.fn();
  });

  it('replie sur window.open quand le greffon shell rejette', async () => {
    render(<AboutTab />);
    fireEvent.click(screen.getByRole('button', { name: /Vérifier les mises à jour/ }));
    const lien = await screen.findByRole('button', { name: /Voir toutes les versions sur GitHub/ });

    fireEvent.click(lien);
    await vi.waitFor(() => {
      expect(window.open).toHaveBeenCalledWith(release.html_url, '_blank');
    });
  });
});
