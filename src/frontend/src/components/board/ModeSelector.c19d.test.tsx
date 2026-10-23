import { render, screen } from '@testing-library/react';
import { expect, it, vi } from 'vitest';
import { ModeSelector } from './ModeSelector';
it('B-1049 : la vérification possède un nom explicite et un type', () => {
  render(<ModeSelector mode="cloud" onChange={vi.fn()} ollamaAvailable={false} onRefreshOllama={vi.fn()} />);
  const bouton = screen.getByRole('button', { name: 'Vérifier Ollama' });
  expect(bouton).toHaveAttribute('aria-label', 'Vérifier Ollama');
  expect(bouton).toHaveAttribute('type', 'button');
});
it('B-1050 : la raison du refus est visible et décrit le mode indisponible', () => {
  render(<ModeSelector mode="cloud" onChange={vi.fn()} ollamaAvailable={false} raisonIndisponible="Aucun modèle local installé" />);
  expect(screen.getByText('Aucun modèle local installé')).toBeVisible();
  expect(screen.getByRole('button', { name: 'Souverain' })).toHaveAccessibleDescription('Aucun modèle local installé');
});
