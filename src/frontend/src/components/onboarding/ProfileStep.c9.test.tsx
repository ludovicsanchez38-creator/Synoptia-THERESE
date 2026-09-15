/**
 * B-773 (cycle 9) : l'échec du pont natif à l'import de THÉRÈSE.md affichait le
 * message brut de l'exception (« Cannot read properties of undefined (reading
 * 'invoke') »), là où WorkingDirStep traduit le même échec en français (B-235).
 */
import { fireEvent, render, screen } from '@testing-library/react';
import { open } from '@tauri-apps/plugin-dialog';
import { beforeEach, describe, expect, it, vi } from 'vitest';

const apiMocks = vi.hoisted(() => ({ getProfile: vi.fn(), setProfile: vi.fn(), importClaudeMd: vi.fn(), getWorkingDirectory: vi.fn() }));
vi.mock('../../services/api', () => apiMocks);

import { ProfileStep } from './ProfileStep';

const JARGON = /undefined|invoke|TypeError|Error:/i;

describe('ProfileStep - B-773, une panne du sélecteur se dit en français', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    apiMocks.getProfile.mockResolvedValue(null);
  });

  it('ne relaie pas l’exception du pont natif et propose de réessayer', async () => {
    vi.mocked(open).mockRejectedValueOnce(new TypeError("Cannot read properties of undefined (reading 'invoke')"));
    render(<ProfileStep onNext={vi.fn()} onBack={vi.fn()} />);
    fireEvent.click(await screen.findByRole('button', { name: /Importer THÉRÈSE\.md/ }));

    const alerte = await screen.findByRole('alert');
    expect(alerte.textContent).not.toMatch(JARGON);
    expect(alerte.textContent).toMatch(/fenêtre de choix du fichier|Redémarre THÉRÈSE/);
  });
});
