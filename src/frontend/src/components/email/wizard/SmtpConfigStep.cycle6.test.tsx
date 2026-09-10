/**
 * Cycle 6, lecteur D79 (SmtpConfigStep.tsx) : les listes de ports proposaient
 * « Autre : <port> » dont la sélection était ignorée ; aucun champ ne
 * permettait de saisir un port hors 25/465/587 ou 143/993.
 */
import { fireEvent, render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { SmtpConfigStep } from './SmtpConfigStep';

vi.mock('../../../services/api', () => ({
  getEmailProviders: vi.fn().mockResolvedValue([]),
  setupSmtpAccount: vi.fn(),
  testSmtpConnection: vi.fn(),
}));

describe('D79 : « Autre » ouvre la saisie d’un port', () => {
  beforeEach(() => { vi.clearAllMocks(); });

  it('choisir Autre sur le port SMTP affiche un champ numérique qui garde la valeur tapée', async () => {
    render(<SmtpConfigStep onBack={vi.fn()} onSuccess={vi.fn()} />);
    const selecteur = await screen.findByLabelText('Port SMTP');
    fireEvent.change(selecteur, { target: { value: 'custom' } });
    const champ = screen.getByLabelText('Port SMTP personnalisé') as HTMLInputElement;
    fireEvent.change(champ, { target: { value: '2525' } });
    expect(champ.value).toBe('2525');
    expect((screen.getByLabelText('Port SMTP') as HTMLSelectElement).value).toBe('custom');
  });
});
