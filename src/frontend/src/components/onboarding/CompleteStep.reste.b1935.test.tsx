/**
 * B-1935 : quand l’IA manque, le titre dit « Il reste une étape » mais
 * l’illustration reste le cotillon. Le dossier de travail ne garde que les
 * deux derniers segments, et le survol répète cette version courte.
 */
import { render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import * as api from '../../services/api';
import { CompleteStep } from './CompleteStep';

vi.mock('../../services/api', () => ({
  getProfile: vi.fn().mockResolvedValue({ name: 'Gérard', display_name: 'Gérard' }),
  getLLMConfig: vi.fn(),
  getWorkingDirectory: vi.fn().mockResolvedValue({ path: null, exists: false }),
  completeOnboarding: vi.fn().mockResolvedValue(undefined),
}));

const config = (available: boolean) => ({ provider: 'ollama', model: 'qwen3:8b', available }) as api.LLMConfig;
const chemin = '/Users/ada/clients/atelier/dossier';

describe('récapitulatif : étape restante et chemin entier (B-1935)', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(api.getWorkingDirectory).mockResolvedValue({ path: null, exists: false });
  });

  it('sans IA, l’illustration n’est plus un cotillon de fête', async () => {
    vi.mocked(api.getLLMConfig).mockResolvedValue(config(false));
    const { container } = render(<CompleteStep onComplete={vi.fn()} onBack={vi.fn()} />);
    expect(await screen.findByRole('heading', { name: 'Il reste une étape' })).toBeInTheDocument();
    expect(container.querySelector('.lucide-party-popper')).toBeNull();
  });

  it('avec une IA prête, le cotillon reste', async () => {
    vi.mocked(api.getLLMConfig).mockResolvedValue(config(true));
    const { container } = render(<CompleteStep onComplete={vi.fn()} onBack={vi.fn()} />);
    expect(await screen.findByRole('heading', { name: "C'est parti !" })).toBeInTheDocument();
    expect(container.querySelector('.lucide-party-popper')).toBeTruthy();
  });

  it('le dossier de travail s’affiche en entier, et le survol aussi', async () => {
    vi.mocked(api.getLLMConfig).mockResolvedValue(config(true));
    vi.mocked(api.getWorkingDirectory).mockResolvedValue({ path: chemin, exists: true });
    render(<CompleteStep onComplete={vi.fn()} onBack={vi.fn()} />);
    const ligne = await screen.findByText(chemin);
    expect(ligne).toHaveAttribute('title', chemin);
    expect(screen.queryByText('atelier/dossier')).not.toBeInTheDocument();
  });
});
