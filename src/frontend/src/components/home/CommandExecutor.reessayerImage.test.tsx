/**
 * B-585 (COCO, c4) : après une génération d'image échouée, « Réessayer » ne
 * relançait rien : la commande d'image était déjà refermée (mise à null au
 * lancement), et handleImageGenerate sortait à sa première garde.
 */
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import type { CommandDefinition } from '../../types/command';

const generateImage = vi.fn();

vi.mock('../../services/api', async () => {
  const reel = await vi.importActual<typeof import('../../services/api')>('../../services/api');
  return {
    ...reel,
    generateImage: (...args: unknown[]) => generateImage(...args),
  };
});

vi.mock('../../services/api/commands-v3', () => ({
  fetchCommandSchema: vi.fn(),
}));

import { CommandExecutor } from './CommandExecutor';

const commande: CommandDefinition = {
  id: 'image-illustration',
  name: 'Illustration',
  description: 'Génère une image',
  icon: 'image',
  category: 'produire',
  source: 'skill',
  action: 'image',
  prompt_template: '',
  skill_id: null,
  system_prompt: null,
  show_on_home: true,
  show_in_slash: true,
  sort_order: 0,
  image_config: { provider: 'gpt-image-2', default_size: '1024x1024', default_quality: 'medium' },
  navigate_target: null,
  is_editable: false,
} as unknown as CommandDefinition;

describe('B-585 : « Réessayer » relance la génération d’image', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    generateImage.mockRejectedValue(new Error('Panne simulée du fournisseur'));
  });

  it('après un échec, le clic sur Réessayer rappelle generateImage avec la même consigne', async () => {
    render(<CommandExecutor command={commande} onClose={vi.fn()} onPromptSelect={vi.fn()} onStartRFC={vi.fn()} />);

    const consigne = await screen.findByLabelText('Consigne');
    fireEvent.change(consigne, { target: { value: 'Un chat sur un toit' } });
    fireEvent.click(screen.getByRole('button', { name: /Générer/ }));

    await waitFor(() => expect(generateImage).toHaveBeenCalledTimes(1));
    const reessayer = await screen.findByRole('button', { name: /Réessayer/ });
    fireEvent.click(reessayer);

    await waitFor(() => expect(generateImage).toHaveBeenCalledTimes(2));
    const [premiere, seconde] = generateImage.mock.calls.map((c) => c[0] as { prompt: string });
    expect(seconde.prompt).toBe(premiere.prompt);
  });
});
