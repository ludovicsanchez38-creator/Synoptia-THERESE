import { fireEvent, render, screen, within } from '@testing-library/react';
import { beforeEach, expect, it, vi } from 'vitest';
import { open } from '@tauri-apps/plugin-shell';
import { Aide } from './Aide';
import { LIEN_SECURITE } from './onboarding/SecurityStep';

beforeEach(() => vi.clearAllMocks());

it('ouvre le guide embarqué 0.85 et la page sécurité depuis l’aide', () => {
  render(<Aide />);
  fireEvent.click(screen.getByRole('button', { name: 'Aide' }));
  fireEvent.click(screen.getByRole('button', { name: 'Ouvrir le guide' }));

  const guide = screen.getByRole('article', { name: 'Guide des testeurs' });
  expect(within(guide).getByRole('heading', { name: 'Guide des testeurs de THÉRÈSE 0.85' })).toBeVisible();
  expect(within(guide).getByText(/les PDF de devis et de factures peuvent échouer/)).toBeVisible();
  expect(within(guide).getByText(/est masquée dans le composeur/)).toBeVisible();
  expect(within(guide).getByRole('link', { name: 'Politique de confidentialité de Synthetic' }))
    .toHaveAttribute('href', 'https://synthetic.new/policies/privacy');
  expect(within(guide).getAllByRole('img')).toHaveLength(4);
  expect(open).not.toHaveBeenCalled();

  fireEvent.click(screen.getByRole('link', { name: 'Lire la page sécurité' }));
  expect(open).toHaveBeenCalledWith(LIEN_SECURITE);
});

it('ferme et rouvre le guide sans dépendre d’un lecteur externe', () => {
  render(<Aide />);
  fireEvent.click(screen.getByRole('button', { name: 'Aide' }));
  fireEvent.click(screen.getByRole('button', { name: 'Ouvrir le guide' }));
  fireEvent.click(screen.getByRole('button', { name: 'Masquer le guide' }));
  expect(screen.queryByRole('article', { name: 'Guide des testeurs' })).not.toBeInTheDocument();
  fireEvent.click(screen.getByRole('button', { name: 'Ouvrir le guide' }));
  expect(screen.getByRole('article', { name: 'Guide des testeurs' })).toBeVisible();
  expect(open).not.toHaveBeenCalled();
});
