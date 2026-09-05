/**
 * B-329 (05/09/2026) : avec des identifiants Google déjà détectés, choisir
 * Gmail saute à l'étape 4. Deux retours arrière tombaient sur l'étape 2, où
 * aucun contenu n'existe pour cet état : un panneau vide sans action.
 */
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

vi.mock('../../../services/api', async () => {
  const reel = await vi.importActual<typeof import('../../../services/api')>('../../../services/api');
  return {
    ...reel,
    getEmailSetupStatus: vi.fn().mockResolvedValue({
      google_credentials: { client_id: 'mcp-id', client_secret: 'mcp-secret' },
    }),
    getEmailAuthStatus: vi.fn().mockResolvedValue({ connected: false, accounts: [] }),
    initiateEmailOAuth: vi.fn().mockResolvedValue({
      auth_url: 'https://accounts.google.com/o/oauth2/auth?fake=1',
      redirect_uri: 'http://localhost/oauth/callback',
    }),
  };
});

import { EmailSetupWizard } from './EmailSetupWizard';

describe('EmailSetupWizard : retour arrière avec identifiants détectés (B-329)', () => {
  beforeEach(() => vi.clearAllMocks());

  it('deux retours depuis la vérification ramènent au choix du mode, jamais à un écran vide', async () => {
    render(<EmailSetupWizard onComplete={() => {}} onCancel={() => {}} />);
    await waitFor(() => expect(screen.getByText(/Credentials Google détectés/i)).toBeInTheDocument());

    fireEvent.click(screen.getByRole('button', { name: /Gmail OAuth/ }));
    await waitFor(() => expect(screen.getByText('Étape 4 sur 4')).toBeInTheDocument());

    fireEvent.click(await screen.findByRole('button', { name: /Annuler/i }));
    await screen.findByText('Entre tes identifiants', {}, { timeout: 3000 });

    fireEvent.click(screen.getByRole('button', { name: /^Retour$/i }));

    await waitFor(
      () => expect(screen.getByText(/Comment veux-tu connecter/i)).toBeInTheDocument(),
      { timeout: 5000 },
    );
    expect(screen.getByText('Étape 1 sur 4')).toBeInTheDocument();
  }, 15000);
});
