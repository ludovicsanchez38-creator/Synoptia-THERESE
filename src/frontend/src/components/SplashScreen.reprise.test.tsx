import { render, screen } from '@testing-library/react';
import { expect, it, vi } from 'vitest';
vi.mock('../services/api/core', () => ({
  getApiBase: () => 'http://127.0.0.1:1', initApiBase: vi.fn().mockResolvedValue(undefined),
  initializeAuth: vi.fn().mockResolvedValue(undefined), request: vi.fn().mockResolvedValue({ copies: [] }),
}));
vi.mock('@tauri-apps/api/event', () => ({ listen: vi.fn().mockResolvedValue(() => {}) }));
vi.mock('@tauri-apps/api/app', () => ({ getVersion: vi.fn().mockResolvedValue('0.82') }));
import { SplashScreen } from './SplashScreen';
it('une réponse recovery ouvre immédiatement la reprise sans appeler onReady', async () => {
  vi.mocked(fetch).mockResolvedValue({ ok: true, text: async () => JSON.stringify({ status: 'recovery', version: '0.82' }) } as Response);
  const pret = vi.fn();
  render(<SplashScreen onReady={pret} />);
  expect(await screen.findByRole('heading', { name: 'Récupérer tes données' })).toBeInTheDocument();
  expect(await screen.findByText(/Aucune copie automatique/)).toBeInTheDocument();
  expect(pret).not.toHaveBeenCalled();
});
