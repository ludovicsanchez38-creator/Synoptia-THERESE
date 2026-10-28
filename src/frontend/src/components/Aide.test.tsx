import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, expect, it, vi } from 'vitest';
const pdf = vi.hoisted(() => ({ ouvrirGuide: vi.fn().mockResolvedValue(undefined) }));
vi.mock('../lib/pdfLocaux', () => ({ ...pdf, GUIDE_VERSION: '0.82' }));
import { open } from '@tauri-apps/plugin-shell';
import { Aide } from './Aide';
import { LIEN_SECURITE } from './onboarding/SecurityStep';
beforeEach(() => vi.clearAllMocks());
it('ouvre le guide embarqué et la page sécurité depuis l’aide', async () => {
  render(<Aide />);
  fireEvent.click(screen.getByRole('button', { name: 'Aide' }));
  expect(screen.getByRole('dialog', { name: 'Aide' })).toHaveTextContent('0.82');
  fireEvent.click(screen.getByRole('button', { name: 'Ouvrir le guide (PDF)' }));
  await waitFor(() => expect(pdf.ouvrirGuide).toHaveBeenCalledTimes(1));
  fireEvent.click(screen.getByRole('link', { name: 'Lire la page sécurité' }));
  expect(open).toHaveBeenCalledWith(LIEN_SECURITE);
});
it('un lecteur absent laisse une erreur lisible et le bouton pour réessayer', async () => {
  pdf.ouvrirGuide.mockRejectedValueOnce(new Error('pas de lecteur'));
  render(<Aide />);
  fireEvent.click(screen.getByRole('button', { name: 'Aide' }));
  fireEvent.click(screen.getByRole('button', { name: 'Ouvrir le guide (PDF)' }));
  expect(await screen.findByRole('alert')).toHaveTextContent('lecteur PDF');
});
