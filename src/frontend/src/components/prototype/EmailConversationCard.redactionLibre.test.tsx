/**
 * B-596 (Karim, c4) : en rédaction libre, « Générer une proposition » restait
 * actif alors que generateDraft sortait sans rien faire faute de message source.
 */
import { render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

import { EmailMessageCanvas } from './EmailConversationCard';

describe('EmailMessageCanvas : la proposition suppose un message source', () => {
  it('en rédaction libre, aucun bouton muet, une explication à la place', () => {
    render(
      <EmailMessageCanvas
        resource={null}
        nouvelleRedaction
        onRetry={vi.fn()}
        onGenerateDraft={vi.fn()}
        onSaveDraft={vi.fn()}
        onOpenClassic={vi.fn()}
      />,
    );
    expect(screen.queryByRole('button', { name: /Générer une proposition/ })).not.toBeInTheDocument();
    expect(screen.getByText(/aucune proposition à générer sans message source/i)).toBeInTheDocument();
  });
});
