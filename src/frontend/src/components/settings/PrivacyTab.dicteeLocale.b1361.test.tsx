/**
 * B-1361 (persona Claire, cycle 13) : la page de Confidentialité se
 * contredisait sur la dictée locale.
 *
 * « Dictée cloud (Groq) : non autorisée. La dictée reste possible en 100 %
 * local. » s'affichait sans condition, et plus bas la section voix locale
 * disait « La voix locale n'est pas embarquée dans cette version ». La phrase
 * ne promet plus une dictée locale qu'elle ne sait pas disponible : elle
 * renvoie à la section qui dit ce qu'il en est.
 */
import { render, screen } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { PrivacyTab } from './PrivacyTab';

vi.mock('./VoiceLocalSection', () => ({
  VoiceLocalSection: () => <div>Voix locale</div>,
}));
vi.mock('../../services/api/rgpd', () => ({
  getPurgeSettings: vi.fn().mockResolvedValue({ enabled: true, months: 36 }),
  updatePurgeSettings: vi.fn().mockResolvedValue(undefined),
}));
vi.mock('../../services/api/data', () => ({
  downloadAllData: vi.fn(),
  listBackups: vi.fn().mockResolvedValue([]),
  createBackup: vi.fn(),
  restoreBackup: vi.fn(),
  deleteBackup: vi.fn(),
  deleteAllData: vi.fn(),
}));

describe('B-1361 : la dictée locale n’est pas promise sans condition', () => {
  beforeEach(() => {
    const store: Record<string, string> = {};
    vi.stubGlobal('localStorage', {
      getItem: (k: string) => store[k] ?? null,
      setItem: (k: string, v: string) => { store[k] = v; },
      removeItem: (k: string) => { delete store[k]; },
      clear: () => { for (const k of Object.keys(store)) delete store[k]; },
    });
  });
  afterEach(() => vi.unstubAllGlobals());

  it('sans accord Groq, la phrase renvoie à la voix locale sans la promettre', async () => {
    render(<PrivacyTab />);
    const phrase = await screen.findByText(/Dictée cloud \(Groq\) : non autorisée/);
    expect(phrase.textContent).not.toMatch(/reste possible/);
    expect(phrase.textContent).toMatch(/voix locale/);
  });
});
