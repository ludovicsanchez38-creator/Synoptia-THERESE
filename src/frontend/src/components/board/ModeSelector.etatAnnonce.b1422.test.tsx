/**
 * B-1422 (tri de la couverture écran P-145, 25/09) : « Cloud » et « Souverain »
 * montraient le mode actif par une couleur seulement ; un lecteur d'écran ne
 * savait pas lequel était choisi.
 */
import { render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

import { ModeSelector } from './ModeSelector';

describe('B-1422 : le mode actif est annoncé', () => {
  it('Cloud actif', () => {
    render(<ModeSelector mode="cloud" onChange={vi.fn()} ollamaAvailable />);
    expect(screen.getByRole('button', { name: /Cloud/ })).toHaveAttribute('aria-pressed', 'true');
    expect(screen.getByRole('button', { name: /Souverain/ })).toHaveAttribute('aria-pressed', 'false');
  });

  it('Souverain actif', () => {
    render(<ModeSelector mode="sovereign" onChange={vi.fn()} ollamaAvailable />);
    expect(screen.getByRole('button', { name: /Souverain/ })).toHaveAttribute('aria-pressed', 'true');
    expect(screen.getByRole('button', { name: /Cloud/ })).toHaveAttribute('aria-pressed', 'false');
  });

  it('la vérification d’Ollama porte un nom accessible', () => {
    render(<ModeSelector mode="cloud" onChange={vi.fn()} ollamaAvailable={false} onRefreshOllama={vi.fn()} />);
    expect(screen.getByRole('button', { name: 'Vérifier Ollama' })).toBeInTheDocument();
  });
});
