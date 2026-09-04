import { fireEvent, render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

vi.mock('../../../services/api', async () => {
  const actual = await vi.importActual<typeof import('../../../services/api')>('../../../services/api');
  return {
    ...actual,
    getEmailSetupStatus: vi.fn().mockResolvedValue({ google_credentials: null }),
  };
});

import { EmailSetupWizard } from './EmailSetupWizard';

describe('B-323 : progression de la configuration Email', () => {
  beforeEach(() => vi.clearAllMocks());

  it('n’annonce aucun total avant de connaître le parcours', () => {
    render(<EmailSetupWizard onComplete={() => {}} onCancel={() => {}} />);

    expect(screen.getByText('Choix du mode de connexion')).toBeInTheDocument();
    expect(screen.queryByText(/Étape 1 sur 4/)).toBeNull();
    expect(screen.getByRole('progressbar')).toHaveAttribute('aria-valuenow', '0');
  });

  it('annonce deux étapes seulement après le choix SMTP', () => {
    render(<EmailSetupWizard onComplete={() => {}} onCancel={() => {}} />);

    fireEvent.click(screen.getByRole('button', { name: /SMTP \/ IMAP classique/ }));

    expect(screen.getByText('Étape 2 sur 2')).toBeInTheDocument();
    expect(screen.getByRole('progressbar')).toHaveAttribute('aria-valuemax', '2');
    expect(screen.queryByText(/sur 4/)).toBeNull();
  });

  it('annonce quatre étapes après le choix Gmail', () => {
    render(<EmailSetupWizard onComplete={() => {}} onCancel={() => {}} />);

    fireEvent.click(screen.getByRole('button', { name: /Gmail OAuth/ }));

    expect(screen.getByText('Étape 2 sur 4')).toBeInTheDocument();
    expect(screen.getByRole('progressbar')).toHaveAttribute('aria-valuemax', '4');
  });
});
