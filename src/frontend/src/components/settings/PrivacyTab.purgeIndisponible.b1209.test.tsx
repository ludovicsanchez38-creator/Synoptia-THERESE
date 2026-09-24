/**
 * B-1209 : quand les réglages de purge n'ont pas pu être lus, « Enregistrer »
 * envoyait les valeurs par défaut de l'écran (activée, 36 mois) et pouvait
 * réactiver une purge automatique que l'utilisateur avait coupée.
 */
import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

import { updatePurgeSettings } from '../../services/api/rgpd';
import { PrivacyTab } from './PrivacyTab';

vi.mock('./VoiceLocalSection', () => ({
  VoiceLocalSection: () => <div>Voix locale</div>,
}));
vi.mock('../../services/api/rgpd', () => ({
  getPurgeSettings: vi.fn().mockRejectedValue(new Error('moteur injoignable')),
  updatePurgeSettings: vi.fn().mockResolvedValue(undefined),
}));
vi.mock('../../services/api/data', () => ({
  downloadAllData: vi.fn(),
  listBackups: vi.fn().mockResolvedValue([]),
  createBackup: vi.fn(),
  restoreBackup: vi.fn(),
  deleteBackup: vi.fn(),
  deleteAllData: vi.fn(),
}));

describe('B-1209 : réglages de purge illisibles', () => {
  it('« Enregistrer » n’envoie pas des valeurs par défaut non lues', async () => {
    render(<PrivacyTab />);
    await screen.findByRole('button', { name: 'Réessayer le chargement' });
    const enregistrer = screen.getByRole('button', { name: 'Enregistrer' });

    fireEvent.click(enregistrer);

    expect({ desactive: (enregistrer as HTMLButtonElement).disabled, envois: vi.mocked(updatePurgeSettings).mock.calls.length })
      .toEqual({ desactive: true, envois: 0 });
  });

  it('B-1230 : les commandes de purge sont grisées et la raison est dite', async () => {
    render(<PrivacyTab />);
    await screen.findByRole('button', { name: 'Réessayer le chargement' });
    const interrupteur = screen.getByRole('switch');
    const curseur = screen.getByLabelText('Ancienneté des données à purger, en mois');
    expect({
      interrupteurInactif: (interrupteur as HTMLButtonElement).disabled,
      curseurInactif: (curseur as HTMLInputElement).disabled,
      raisonDite: screen.queryByText(/réglages n’ont pas pu être lus/i) !== null,
    }).toEqual({ interrupteurInactif: true, curseurInactif: true, raisonDite: true });
  });
});
