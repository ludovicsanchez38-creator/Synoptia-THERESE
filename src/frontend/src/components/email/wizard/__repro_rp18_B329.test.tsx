/**
 * RP18 - reproduction B-329 : impasse dans l'assistant Gmail quand des
 * identifiants MCP existent. Choix Gmail -> saut direct à l'étape 4
 * (VerifyStep). Retour arrière -> étape 3 (CredentialsStep, rendue même si
 * useMcpCredentials=true). Nouveau retour arrière -> étape 2, où AUCUNE
 * condition ne correspond (GuideStep exige !useMcpCredentials) : écran vide.
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

describe('B-329 : impasse assistant Gmail avec identifiants MCP', () => {
  beforeEach(() => vi.clearAllMocks());

  it('deux retours arrière depuis VerifyStep mènent à un écran vide (étape 2 sans contenu)', async () => {
    render(<EmailSetupWizard onComplete={() => {}} onCancel={() => {}} />);

    // Les credentials MCP sont chargés au montage (useEffect loadSetupStatus)
    await waitFor(() => expect(screen.getByText(/Credentials Google détectés/i)).toBeInTheDocument());

    // Choix Gmail -> mcpCredentials existe -> setStep(4), saute Guide (2) et Credentials (3)
    fireEvent.click(screen.getByRole('button', { name: /Gmail OAuth/ }));

    // On doit atterrir directement à l'étape 4 (VerifyStep)
    await waitFor(() => expect(screen.getByText('Étape 4 sur 4')).toBeInTheDocument());

    // VerifyStep affiche un bouton "Annuler" (onBack=prevStep) une fois l'état 'waiting' atteint
    const annulerBtn = await screen.findByRole('button', { name: /Annuler/i });
    fireEvent.click(annulerBtn);

    // prevStep() : step 4 -> 3. La condition ne teste PAS useMcpCredentials :
    // CredentialsStep se réaffiche même si l'utilisateur a des identifiants MCP.
    // (attendre le VRAI contenu de CredentialsStep, pas seulement le texte d'en-tête
    // qui change de façon synchrone alors qu'AnimatePresence mode="wait" retarde le swap DOM)
    const titreCredentials = await screen.findByText('Entre tes identifiants', {}, { timeout: 3000 });
    expect(titreCredentials).toBeInTheDocument();
    expect(screen.getByText('Étape 3 sur 4')).toBeInTheDocument();

    const retourCredentials = screen.getByRole('button', { name: /^Retour$/i });
    fireEvent.click(retourCredentials);

    // prevStep() : step 3 -> 2. GuideStep exige !wizardState.useMcpCredentials ;
    // useMcpCredentials est resté à true depuis l'auto-remplissage MCP -> RIEN ne s'affiche.
    await waitFor(() => expect(screen.getByText('Étape 2 sur 4')).toBeInTheDocument());
    // Laisser le temps à un éventuel swap AnimatePresence de se stabiliser
    await new Promise((r) => setTimeout(r, 400));

    // Preuve de l'impasse : aucun contenu de step (ni Guide, ni Credentials, ni Verify)
    expect(screen.queryByText(/Comment veux-tu connecter/i)).toBeNull(); // ChoiceStep (étape 1)
    expect(screen.queryByLabelText(/Client ID/i)).toBeNull(); // CredentialsStep (étape 3)
    expect(screen.queryByText(/As-tu déjà un projet/i)).toBeNull(); // GuideStep (étape 2)
    expect(screen.queryByText(/Connexion à Google/i)).toBeNull(); // VerifyStep (étape 4)

    // Le conteneur de contenu (AnimatePresence) est bien vide
    const contentDiv = document.querySelector('.p-6');
    expect(contentDiv?.textContent?.trim()).toBe('');
  });
});
