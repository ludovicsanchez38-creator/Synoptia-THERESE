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
