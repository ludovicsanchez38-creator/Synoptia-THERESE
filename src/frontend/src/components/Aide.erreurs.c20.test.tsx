import { fireEvent, render, screen } from '@testing-library/react';
import { beforeEach, expect, it, vi } from 'vitest';
import { open } from '@tauri-apps/plugin-shell';
import { Aide } from './Aide';

const pdf = vi.hoisted(() => ({ ouvrirGuide: vi.fn() }));
vi.mock('../lib/pdfLocaux', () => ({ ...pdf, GUIDE_VERSION: '0.83' }));

beforeEach(() => {
  vi.clearAllMocks();
  pdf.ouvrirGuide.mockResolvedValue(undefined);
  vi.mocked(open).mockResolvedValue(undefined);
});

it('B-2016 : un échec du PDF propose de vérifier le lecteur PDF uniquement', async () => {
  pdf.ouvrirGuide.mockRejectedValueOnce(new Error('Lecteur indisponible'));
  render(<Aide />);
  fireEvent.click(screen.getByRole('button', { name: 'Aide' }));
  fireEvent.click(screen.getByRole('button', { name: 'Ouvrir le guide (PDF)' }));

  const erreur = await screen.findByRole('alert');
  expect(erreur).toHaveTextContent('lecteur PDF');
  expect(erreur).not.toHaveTextContent('navigateur');
  expect(open).not.toHaveBeenCalled();

  fireEvent.click(screen.getByRole('button', { name: 'Ouvrir le guide (PDF)' }));
  expect(screen.queryByRole('alert')).not.toBeInTheDocument();
  expect(pdf.ouvrirGuide).toHaveBeenCalledTimes(2);
});

it('B-2016 : un échec de la page sécurité propose de vérifier le navigateur uniquement', async () => {
  vi.mocked(open).mockRejectedValueOnce(new Error('Navigateur indisponible'));
  render(<Aide />);
  fireEvent.click(screen.getByRole('button', { name: 'Aide' }));
  fireEvent.click(screen.getByRole('link', { name: 'Lire la page sécurité' }));

  const erreur = await screen.findByRole('alert');
  expect(erreur).toHaveTextContent('navigateur');
  expect(erreur).not.toHaveTextContent('PDF');
  expect(pdf.ouvrirGuide).not.toHaveBeenCalled();

  fireEvent.click(screen.getByRole('link', { name: 'Lire la page sécurité' }));
  expect(screen.queryByRole('alert')).not.toBeInTheDocument();
  expect(open).toHaveBeenCalledTimes(2);
});
