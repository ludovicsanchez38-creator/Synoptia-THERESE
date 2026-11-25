/**
 * B-235 — une panne du sélecteur de dossier se dit en français, et s'annonce.
 *
 * L'étape réaffichait `err.message` verbatim : sur un poste où le pont Tauri
 * n'est pas joignable, l'écran montrait « Cannot read properties of undefined
 * (reading 'invoke') », dans un `<span>` nu — ni `role="alert"`, ni `aria-live`,
 * aucun rôle nulle part dans l'étape. Deux fautes d'un coup : la frontière
 * d'erreurs de la 0.48 (le message du fournisseur ne traverse pas jusqu'à
 * l'écran) et le bandeau muet.
 *
 * Le refus du serveur passait par le même chemin : `Path does not exist`,
 * écrit pour un journal, pas pour une personne.
 */
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { open } from '@tauri-apps/plugin-dialog';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import { ApiError } from '../../services/api/core';
import { WorkingDirStep } from './WorkingDirStep';

const apiMocks = vi.hoisted(() => ({
  getWorkingDirectory: vi.fn(),
  setWorkingDirectory: vi.fn(),
}));

vi.mock('../../services/api', () => apiMocks);

/** Ce qu'un message écrit pour une personne ne contient jamais. */
const JARGON = /undefined|invoke|Path does not exist|TypeError/i;

async function ouvrirLEtape() {
  apiMocks.getWorkingDirectory.mockResolvedValue({ path: null, exists: false });
  render(<WorkingDirStep onNext={vi.fn()} onBack={vi.fn()} />);
  return screen.findByText('Sélectionner un dossier');
}

describe('WorkingDirStep — une panne de sélection est dite et annoncée', () => {
  beforeEach(() => vi.clearAllMocks());

  it('ne relaie pas l’exception du pont natif, et l’annonce', async () => {
    const bouton = await ouvrirLEtape();
    vi.mocked(open).mockRejectedValueOnce(
      new TypeError("Cannot read properties of undefined (reading 'invoke')"),
    );

    fireEvent.click(bouton);

    const alerte = await screen.findByRole('alert');
    expect(alerte.textContent?.trim()).toBeTruthy();
    expect(alerte.textContent ?? '').not.toMatch(JARGON);
    expect(document.body.textContent ?? '').not.toMatch(JARGON);
  });

  it('ne relaie pas non plus le refus du serveur', async () => {
    const bouton = await ouvrirLEtape();
    vi.mocked(open).mockResolvedValueOnce('/Users/camille/Documents' as never);
    apiMocks.setWorkingDirectory.mockRejectedValueOnce(new Error('Path does not exist'));

    fireEvent.click(bouton);

    const alerte = await screen.findByRole('alert');
    await waitFor(() => expect(alerte.textContent?.trim()).toBeTruthy());
    expect(alerte.textContent ?? '').not.toMatch(JARGON);
    expect(document.body.textContent ?? '').not.toMatch(JARGON);
  });
});


it('R1-8 : explique le refus du dossier personnel entier', async () => {
  const bouton = await ouvrirLEtape();
  vi.mocked(open).mockResolvedValueOnce('/Users/camille');
  const raison = 'Choisis un dossier de travail dédié : ton dossier personnel entier est refusé.';
  apiMocks.setWorkingDirectory.mockRejectedValueOnce(new ApiError(400, 'Bad Request', raison));
  fireEvent.click(bouton);
  expect((await screen.findByText(raison)).closest('[role=alert]')).not.toBeNull();
});

it('B-2062 : avertit au choix du dossier et retire le message après un autre choix', async () => {
  const bouton = await ouvrirLEtape();
  vi.mocked(open).mockResolvedValueOnce('/Volumes/Externe/Facturation');
  apiMocks.setWorkingDirectory.mockResolvedValueOnce({
    path: '/Volumes/Externe/Facturation',
    exists: true,
    avertissement_facturation: 'THÉRÈSE n’a pas pu créer de lien physique dans ce dossier. Les PDF de devis et de factures peuvent échouer. Choisis un dossier dédié sur le disque interne, par exemple dans Documents.',
  });
  fireEvent.click(bouton);

  const alerte = await screen.findByText(/Les PDF de devis et de factures peuvent échouer/);
  expect(alerte.closest('[role=alert]')).not.toBeNull();
  expect(alerte).toHaveTextContent('disque interne');

  vi.mocked(open).mockResolvedValueOnce('/Users/camille/Documents/THÉRÈSE');
  apiMocks.setWorkingDirectory.mockResolvedValueOnce({ path: '/Users/camille/Documents/THÉRÈSE', exists: true });
  fireEvent.click(screen.getByRole('button', { name: 'Changer de dossier' }));
  await screen.findByText('/Users/camille/Documents/THÉRÈSE');
  expect(alerte).not.toBeInTheDocument();
});
