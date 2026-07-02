import { fireEvent, render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { SmtpConfigStep } from './SmtpConfigStep';

const mockGetEmailProviders = vi.fn();
const mockSetupSmtpAccount = vi.fn();
const mockTestSmtpConnection = vi.fn();

vi.mock('../../../services/api', () => ({
  getEmailProviders: (...args: unknown[]) => mockGetEmailProviders(...args),
  setupSmtpAccount: (...args: unknown[]) => mockSetupSmtpAccount(...args),
  testSmtpConnection: (...args: unknown[]) => mockTestSmtpConnection(...args),
}));

describe('SmtpConfigStep', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockGetEmailProviders.mockResolvedValue([
      {
        name: 'Gmail',
        imap_host: 'imap.gmail.com',
        imap_port: 993,
        smtp_host: 'smtp.gmail.com',
        smtp_port: 587,
        smtp_use_tls: true,
      },
    ]);
  });

  it('BUG-112 : le mode manuel garde un bouton pour afficher et masquer le mot de passe', async () => {
    render(<SmtpConfigStep onBack={vi.fn()} onSuccess={vi.fn()} />);

    const toggle = await screen.findByRole('button', { name: 'Afficher le mot de passe' });
    const passwordInput = screen.getByLabelText('Mot de passe / App password *');

    expect(passwordInput).toHaveAttribute('type', 'password');
    fireEvent.click(toggle);
    expect(passwordInput).toHaveAttribute('type', 'text');
    expect(screen.getByRole('button', { name: 'Masquer le mot de passe' })).toBeInTheDocument();
  });

  it('BUG-112 : Enregistrer devient cliquable en fournisseur personnalisé quand tous les champs sont remplis', async () => {
    render(<SmtpConfigStep onBack={vi.fn()} onSuccess={vi.fn()} />);

    fireEvent.change(await screen.findByLabelText('Fournisseur email'), {
      target: { value: 'custom' },
    });
    fireEvent.change(screen.getByLabelText('Adresse email *'), {
      target: { value: 'test@synoptia.fr' },
    });
    fireEvent.change(screen.getByLabelText('Mot de passe / App password *'), {
      target: { value: 'motdepasse' },
    });
    fireEvent.change(screen.getByLabelText('Serveur IMAP *'), {
      target: { value: 'imap.exemple.fr' },
    });
    fireEvent.change(screen.getByLabelText('Serveur SMTP *'), {
      target: { value: 'smtp.exemple.fr' },
    });

    expect(screen.getByRole('button', { name: 'Enregistrer' })).toBeEnabled();
  });

  it('BUG-112 : un fournisseur prérempli ne peut pas être enregistré si un hôte est vidé', async () => {
    render(<SmtpConfigStep onBack={vi.fn()} onSuccess={vi.fn()} />);

    fireEvent.change(await screen.findByLabelText('Fournisseur email'), {
      target: { value: 'Gmail' },
    });
    fireEvent.change(screen.getByLabelText('Adresse email *'), {
      target: { value: 'test@synoptia.fr' },
    });
    fireEvent.change(screen.getByLabelText('Mot de passe / App password *'), {
      target: { value: 'motdepasse' },
    });
    fireEvent.change(screen.getByLabelText('Serveur IMAP *'), {
      target: { value: '' },
    });

    expect(screen.getByRole('button', { name: 'Enregistrer' })).toBeDisabled();
  });
});
