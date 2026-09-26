/**
 * B-1542 (RFC P-107 V4) : une image générée depuis l'Accueil partait chez le
 * fournisseur sans l'accord « images » que le canevas Images demande. B-096
 * n'avait retiré que la confirmation, pas l'accord. Le panneau dit désormais
 * où part la description, et le clic sur « Générer » enregistre l'accord.
 */
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import type { CommandDefinition } from '../../types/command';
import { hasCloudConsent } from '../../lib/consent';

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

async function saisir() {
  render(<CommandExecutor command={commande} onClose={vi.fn()} onPromptSelect={vi.fn()} onStartRFC={vi.fn()} />);
  fireEvent.change(await screen.findByLabelText('Consigne'), { target: { value: 'Un chat sur un toit' } });
}

describe('B-1542 : l’image de l’Accueil demande l’accord « images »', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    // Le localStorage de test/setup.ts est un simulacre muet : un vrai
    // stockage en mémoire, pour que l'accord enregistré se relise.
    const memoire = new Map<string, string>();
    vi.mocked(localStorage.getItem).mockImplementation((cle: string) => memoire.get(cle) ?? null);
    vi.mocked(localStorage.setItem).mockImplementation((cle: string, valeur: string) => { memoire.set(cle, valeur); });
    generateImage.mockResolvedValue({ id: 'img-1' });
  });

  it('dit où part la description, puis enregistre l’accord au clic', async () => {
    await saisir();
    expect(screen.getByText(/GPT Image 2/)).toBeInTheDocument();
    expect(screen.getByText(/tu donnes ton accord/)).toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: /Générer/ }));

    await waitFor(() => expect(generateImage).toHaveBeenCalledTimes(1));
    expect(hasCloudConsent('images', 'gpt-image-2')).toBe(true);
  });

  it('témoin : un accord déjà donné ne se redemande pas', async () => {
    const { grantCloudConsent } = await import('../../lib/consent');
    grantCloudConsent('images', 'gpt-image-2', ['description du visuel']);
    await saisir();
    expect(screen.queryByText(/tu donnes ton accord/)).toBeNull();
  });
});
