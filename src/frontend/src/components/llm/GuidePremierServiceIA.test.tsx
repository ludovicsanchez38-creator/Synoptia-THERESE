import { fireEvent, render, screen } from '@testing-library/react';
import { beforeEach, expect, it, vi } from 'vitest';
import { open } from '@tauri-apps/plugin-shell';
import { GuidePremierServiceIA } from './GuidePremierServiceIA';
beforeEach(() => { vi.mocked(open).mockResolvedValue(undefined); });
it('explique compte, crédits, plafond et clé, avec les liens directs et sans montant', () => {
  const { container } = render(<GuidePremierServiceIA provider="anthropic" />);
  expect(container.textContent).toMatch(/code personnel/);
  expect(container.textContent).toMatch(/plafond/);
  expect(container.textContent).not.toMatch(/[€$]/);
  expect(screen.getByRole('link', { name: 'Créer une clé Claude' })).toHaveAttribute('href', 'https://platform.claude.com/settings/keys');
  fireEvent.click(screen.getByRole('link', { name: 'Voir les tarifs de Claude' }));
  expect(open).toHaveBeenCalledWith('https://claude.com/pricing#api');
});
it('rend l’installation locale accessible même avant la détection d’Ollama', () => {
  const retester = vi.fn();
  render(<GuidePremierServiceIA provider="anthropic" onRetest={retester} />);
  fireEvent.click(screen.getByText('Sur ton ordinateur : installer Ollama gratuitement'));
  expect(screen.getByRole('link', { name: 'Télécharger Ollama' })).toHaveAttribute('href', 'https://ollama.com/download');
  expect(screen.getByText('ollama run qwen3.5:4b')).toBeVisible();
  expect(screen.getByText(/3,3 Go/)).toBeVisible();
  fireEvent.click(screen.getByRole('button', { name: 'Vérifier Ollama après l’installation' }));
  expect(retester).toHaveBeenCalledTimes(1);
});
