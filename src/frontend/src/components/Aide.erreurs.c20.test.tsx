import { fireEvent, render, screen } from '@testing-library/react';
import { beforeEach, expect, it, vi } from 'vitest';
import { open } from '@tauri-apps/plugin-shell';
import { Aide } from './Aide';

beforeEach(() => {
  vi.clearAllMocks();
  vi.mocked(open).mockResolvedValue(undefined);
});

it('B-2016 : un lien externe en échec laisse le guide 0.85 ouvert et le lien réessayable', async () => {
  vi.mocked(open).mockRejectedValueOnce(new Error('Navigateur indisponible'));
  render(<Aide />);
  fireEvent.click(screen.getByRole('button', { name: 'Aide' }));
  fireEvent.click(screen.getByRole('button', { name: 'Ouvrir le guide' }));
  const politique = screen.getByRole('link', { name: 'Politique de confidentialité de Synthetic' });
  fireEvent.click(politique);

  expect(await screen.findByRole('alert')).toHaveTextContent('navigateur');
  expect(screen.getByRole('article', { name: 'Guide des testeurs' })).toBeVisible();

  fireEvent.click(politique);
  expect(screen.queryByRole('alert')).not.toBeInTheDocument();
  expect(open).toHaveBeenCalledTimes(2);
});

it('B-2016 : un échec de la page sécurité propose de vérifier le navigateur uniquement', async () => {
  vi.mocked(open).mockRejectedValueOnce(new Error('Navigateur indisponible'));
  render(<Aide />);
  fireEvent.click(screen.getByRole('button', { name: 'Aide' }));
  fireEvent.click(screen.getByRole('link', { name: 'Lire la page sécurité' }));

  const erreur = await screen.findByRole('alert');
  expect(erreur).toHaveTextContent('navigateur');
  expect(erreur).not.toHaveTextContent('PDF');
  expect(open).toHaveBeenCalledTimes(1);

  fireEvent.click(screen.getByRole('link', { name: 'Lire la page sécurité' }));
  expect(screen.queryByRole('alert')).not.toBeInTheDocument();
  expect(open).toHaveBeenCalledTimes(2);
});
