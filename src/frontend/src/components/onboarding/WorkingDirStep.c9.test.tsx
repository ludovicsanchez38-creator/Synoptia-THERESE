/**
 * B-771 (cycle 9) : après « Dossier configuré mais introuvable », choisir un
 * nouveau dossier enregistrait le chemin sans lever l'avertissement.
 */
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { open } from '@tauri-apps/plugin-dialog';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import { WorkingDirStep } from './WorkingDirStep';

const apiMocks = vi.hoisted(() => ({ getWorkingDirectory: vi.fn(), setWorkingDirectory: vi.fn() }));
vi.mock('../../services/api', () => apiMocks);

describe('WorkingDirStep - B-771, un nouveau dossier lève l’avertissement « introuvable »', () => {
  beforeEach(() => vi.clearAllMocks());

  it('retire l’avertissement une fois un dossier existant enregistré', async () => {
    apiMocks.getWorkingDirectory.mockResolvedValue({ path: '/Users/ludo/Ancien', exists: false });
    apiMocks.setWorkingDirectory.mockResolvedValue({ path: '/Users/ludo/Nouveau', exists: true });
    vi.mocked(open).mockResolvedValue('/Users/ludo/Nouveau');

    render(<WorkingDirStep onNext={vi.fn()} onBack={vi.fn()} />);
    expect(await screen.findByText(/introuvable/)).toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: /Changer|Sélectionner|Choisir/ }));
    await waitFor(() => expect(apiMocks.setWorkingDirectory).toHaveBeenCalledWith('/Users/ludo/Nouveau'));

    await waitFor(() => expect(screen.queryByText(/introuvable/)).toBeNull());
    expect(screen.getByText(/Nouveau/)).toBeInTheDocument();
  });
});

describe('P-005 : une seule action pour avancer depuis le dossier de travail', () => {
  it.each([
    [null, 'Continuer sans dossier'],
    ['/tmp/travail-fictif', 'Continuer'],
  ])('affiche le bon libellé pour le dossier %s', async (path, libelle) => {
    apiMocks.setWorkingDirectory.mockClear();
    apiMocks.getWorkingDirectory.mockResolvedValue({ path, exists: Boolean(path) });
    const onNext = vi.fn();
    render(<WorkingDirStep onNext={onNext} onBack={vi.fn()} />);

    const continuer = await screen.findByRole('button', { name: libelle });
    expect(screen.getAllByRole('button', { name: /^(Continuer|Passer)/ })).toEqual([continuer]);
    expect(continuer).toBeEnabled();
    fireEvent.click(continuer);
    expect(onNext).toHaveBeenCalledTimes(1);
    expect(apiMocks.setWorkingDirectory).not.toHaveBeenCalled();
  });
});
