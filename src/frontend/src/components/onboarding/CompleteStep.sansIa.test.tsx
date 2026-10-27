/**
 * Audit bêta du 27/10/2026 (A2-54) : sans service d'IA, la fin de la mise en
 * route annonçait « C'est parti ! THÉRÈSE est prête à t'accompagner », alors
 * qu'aucune réponse ne viendra au premier message. Le titre dit maintenant
 * qu'il reste une étape, et un bouton y mène.
 */
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import * as api from '../../services/api';
import { usePanelStore } from '../../stores/panelStore';
import { CompleteStep } from './CompleteStep';

vi.mock('../../services/api', () => ({
  getProfile: vi.fn().mockResolvedValue({ name: 'Gérard', display_name: 'Gérard' }),
  getLLMConfig: vi.fn(),
  getWorkingDirectory: vi.fn().mockResolvedValue(null),
  completeOnboarding: vi.fn().mockResolvedValue(undefined),
}));

const config = (available: boolean) => ({ provider: 'anthropic', model: 'claude-sonnet-5-5', available }) as unknown as api.LLMConfig;

describe('CompleteStep : sans IA, la fin ne promet pas une THÉRÈSE prête', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    usePanelStore.setState({ showSettings: false, requestedSettingsTab: null });
  });

  it.each([
    ['étape passée', { llmSkipped: true }, config(true)],
    ['aucune clé ni Ollama', { llmSkipped: false }, config(false)],
    ['configuration absente', { llmSkipped: false }, null],
  ])('%s : « Il reste une étape »', async (_cas, props, reponse) => {
    vi.mocked(api.getLLMConfig).mockResolvedValue(reponse as api.LLMConfig);
    render(<CompleteStep onComplete={vi.fn()} onBack={vi.fn()} {...props} />);

    expect(await screen.findByRole('heading', { name: 'Il reste une étape' })).toBeInTheDocument();
    expect(screen.queryByText(/est prête à t'accompagner/)).toBeNull();
  });

  it('avec une IA prête, le titre reste « C’est parti ! »', async () => {
    vi.mocked(api.getLLMConfig).mockResolvedValue(config(true));
    render(<CompleteStep onComplete={vi.fn()} onBack={vi.fn()} />);

    expect(await screen.findByRole('heading', { name: "C'est parti !" })).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: 'Choisir mon service d’IA' })).toBeNull();
  });

  it('le bouton termine la mise en route et ouvre le réglage du service d’IA', async () => {
    vi.mocked(api.getLLMConfig).mockResolvedValue(config(false));
    const onComplete = vi.fn();
    render(<CompleteStep onComplete={onComplete} onBack={vi.fn()} />);

    fireEvent.click(await screen.findByRole('button', { name: 'Choisir mon service d’IA' }));

    await waitFor(() => expect(onComplete).toHaveBeenCalledTimes(1));
    expect(api.completeOnboarding).toHaveBeenCalledTimes(1);
    expect(usePanelStore.getState().showSettings).toBe(true);
    expect(usePanelStore.getState().requestedSettingsTab).toBe('ai');
  });

  it('un récapitulatif illisible ne déclare pas d’étape manquante', async () => {
    vi.mocked(api.getLLMConfig).mockRejectedValue(new Error('moteur indisponible'));
    render(<CompleteStep onComplete={vi.fn()} onBack={vi.fn()} />);

    await screen.findByText(/Récapitulatif partiel/);
    expect(screen.queryByRole('heading', { name: 'Il reste une étape' })).toBeNull();
  });
});
