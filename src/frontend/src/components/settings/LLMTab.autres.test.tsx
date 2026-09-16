/**
 * P-085 (lot 0.74) : la grille des quatorze services noyait les six
 * fournisseurs secondaires (DeepSeek, GLM, Kimi, Qwen, MiniMax, Infomaniak)
 * parmi les principaux. Une carte « Autres » les regroupe, dépliée seulement
 * si l'un d'eux est courant ou muni d'une clé.
 */
import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

import { LLMTab } from './LLMTab';

vi.mock('../../lib/catalogueModeles', async (importOriginal) => ({
  ...(await importOriginal<object>()),
  chargerCatalogue: vi.fn(async () => null),
}));

type Props = Partial<React.ComponentProps<typeof LLMTab>>;
function rendre(props: Props = {}) {
  return render(
    <LLMTab
      selectedProvider="anthropic" selectedModel="claude-sonnet-4-6" apiKeys={{}} corruptedKeys={[]}
      apiKeyInput="" setApiKeyInput={vi.fn()} showApiKey={false} setShowApiKey={vi.fn()} ollamaStatus={null}
      ollamaModels={[]} systemResources={null} saving={false} saved={false} error={null} setError={vi.fn()}
      onSelectProvider={vi.fn()} onSelectModel={vi.fn()} onSaveApiKey={vi.fn()} {...props}
    />,
  );
}
const groupe = () => screen.getByRole('group', { name: 'Choix du service d’IA' });
const cartes = () => groupe().querySelectorAll('button[aria-pressed]');

describe('LLMTab - P-085, les fournisseurs secondaires derrière « Autres »', () => {
  it('au repos : huit cartes et une carte « Autres (+6) » repliée ; un clic déplie les quatorze', () => {
    rendre();
    expect(cartes()).toHaveLength(8);
    const autres = screen.getByRole('button', { name: /Autres \(\+6\)/ });
    expect(autres).toHaveAttribute('aria-expanded', 'false');
    expect(screen.queryByRole('button', { name: /^Kimi/ })).toBeNull();
    fireEvent.click(autres);
    expect(cartes()).toHaveLength(14);
    expect(screen.getByRole('button', { name: /^Kimi/ })).toBeInTheDocument();
  });

  it('un secondaire courant reste visible parmi les cartes, et « Réduire » ne peut pas le masquer (audit release)', () => {
    rendre({ selectedProvider: 'qwen', selectedModel: 'qwen-max' });
    expect(screen.getByRole('button', { name: /^Qwen/ })).toHaveAttribute('aria-pressed', 'true');
    expect(cartes()).toHaveLength(9);
    const bascule = screen.getByRole('button', { name: /Autres \(\+5\)/ });
    fireEvent.click(bascule);
    expect(cartes()).toHaveLength(14);
    fireEvent.click(screen.getByRole('button', { name: /Réduire les autres services/ }));
    expect(cartes()).toHaveLength(9);
    expect(screen.getByRole('button', { name: /^Qwen/ })).toBeInTheDocument();
  });

  it('la bascule est un seul bouton persistant : le focus ne tombe pas sur body (audit release)', () => {
    rendre();
    const bascule = screen.getByRole('button', { name: /Autres \(\+6\)/ });
    bascule.focus();
    fireEvent.click(bascule);
    expect(document.activeElement).toBe(bascule);
    expect(bascule).toHaveAttribute('aria-expanded', 'true');
    expect(bascule).toHaveAttribute('aria-controls');
    // H1 UX : cible de 36 px (min-h-9), plus un lien de 20 px.
    expect(bascule.className).toMatch(/min-h-9|h-9/);
    fireEvent.click(bascule);
    expect(document.activeElement).toBe(bascule);
    expect(bascule).toHaveAttribute('aria-expanded', 'false');
  });
});
