/**
 * B-1941 : l’erreur de la boîte montre deux « Ouvrir Email », un dans
 * l’en-tête et un dans le bloc d’erreur. L’agenda n’a gardé que celui de
 * l’en-tête : deux contrôles au même nom ne disent pas lequel a été pressé.
 */
import { render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

import { EmailInboxCard } from './EmailConversationCard';

describe('B-1941 : l’erreur de la boîte n’a qu’un Ouvrir Email', () => {
  it('le bloc d’erreur garde Réessayer, l’en-tête garde l’ouverture', () => {
    render(
      <EmailInboxCard
        resource={{ status: 'error', data: null, error: 'Le fournisseur ne répond pas.' }}
        onRetry={vi.fn()}
        onOpenMessage={vi.fn()}
        onOpenClassic={vi.fn()}
      />,
    );

    expect(screen.getByTestId('email-inbox-error')).toBeInTheDocument();
    expect(screen.getAllByRole('button', { name: 'Ouvrir Email' })).toHaveLength(1);
    expect(screen.getByRole('button', { name: 'Réessayer' })).toBeInTheDocument();
  });
});
