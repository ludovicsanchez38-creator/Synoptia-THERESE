/**
 * P-111 : Ollama détecté est choisi d'office à l'étape IA. Revenir sur cette
 * étape (Continuer, puis Retour) ne doit pas remplacer le service que
 * l'utilisateur vient de retenir par le choix d'office.
 */
import { act, fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

vi.mock('@tauri-apps/api/window', () => ({
  getCurrentWindow: () => ({ close: vi.fn(), minimize: vi.fn(), toggleMaximize: vi.fn() }),
}));
vi.mock('./WelcomeStep', () => ({
  WelcomeStep: ({ onNext }: { onNext: () => void }) => <button onClick={onNext}>Commencer</button>,
}));
vi.mock('./ProfileStep', () => ({
  ProfileStep: ({ onNext }: { onNext: () => void }) => <button onClick={onNext}>Profil suivant</button>,
}));
vi.mock('./SecurityStep', () => ({
  SecurityStep: ({ onBack }: { onBack: () => void }) => <button onClick={onBack}>Revenir au service</button>,
}));

const gib = 1024 ** 3;
const apiMocks = vi.hoisted(() => ({
  getApiKeysWithCorrupted: vi.fn(),
  getOllamaStatus: vi.fn(),
  getSystemResources: vi.fn(),
  setApiKey: vi.fn(),
  setLLMConfig: vi.fn(),
  clearLLMConfig: vi.fn(),
}));
vi.mock('../../services/api', () => apiMocks);
vi.mock('../../lib/catalogueModeles', async (importOriginal) => {
  const reel = await importOriginal<typeof import('../../lib/catalogueModeles')>();
  return { ...reel, chargerCatalogue: () => Promise.resolve(null) };
});

import { OnboardingWizard } from './OnboardingWizard';

describe('P-111 : un retour sur l’étape IA garde le service retenu', () => {
  it('Claude retenu, puis Retour : Claude reste choisi malgré Ollama', async () => {
    apiMocks.getApiKeysWithCorrupted.mockResolvedValue({ keys: { anthropic: true }, corrupted: [], sources: { anthropic: 'coffre' } });
    apiMocks.getOllamaStatus.mockResolvedValue({
      available: true, base_url: 'http://ollama.test', error: null,
      models: [{ name: 'qwen3:8b', size: 4.9 * gib, modified_at: null, digest: null, gere_les_outils: true, motif_indisponible: null }],
    });
    apiMocks.getSystemResources.mockResolvedValue({
      total_ram_bytes: 16 * gib, safe_local_model_ram_bytes: 8 * gib, ollama_context_margin_bytes: 2 * gib, detection_method: 'test',
    });
    apiMocks.setLLMConfig.mockResolvedValue({});
    render(<OnboardingWizard isOpen onComplete={vi.fn()} />);
    fireEvent.click(screen.getByRole('button', { name: 'Commencer' }));
    fireEvent.click(await screen.findByRole('button', { name: 'Profil suivant' }));
    const claude = await screen.findByRole('radio', { name: /Claude \(Anthropic\)/ });
    await act(async () => Promise.resolve());
    fireEvent.click(claude);
    await act(async () => {
      fireEvent.click(screen.getByTestId('onboarding-next-btn'));
      await Promise.resolve();
    });
    fireEvent.click(await screen.findByRole('button', { name: 'Revenir au service' }));
    const claudeDeRetour = await screen.findByRole('radio', { name: /Claude \(Anthropic\)/ });
    await act(async () => Promise.resolve());
    await act(async () => Promise.resolve());
    expect(claudeDeRetour).toHaveAttribute('aria-checked', 'true');
    expect(screen.getByRole('radio', { name: /Ollama \(Local\)/ })).toHaveAttribute('aria-checked', 'false');
  });
});
