/** B-614 (Karim, c4) : « EMAIL CONNECTÉ » écrit en dur face à « Aucun compte email connecté ». */
import { render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

import { EmailMessageCanvas } from './EmailConversationCard';

describe('EmailMessageCanvas : l’en-tête ne prétend pas qu’un compte est connecté', () => {
  it('en rédaction libre, l’en-tête dit « Nouveau message »', () => {
    render(
      <EmailMessageCanvas resource={null} nouvelleRedaction onRetry={vi.fn()} onGenerateDraft={vi.fn()} onSaveDraft={vi.fn()} onOpenClassic={vi.fn()} />,
    );
    expect(screen.getByText(/Nouveau message/)).toBeInTheDocument();
    expect(screen.queryByText(/Email connecté/i)).not.toBeInTheDocument();
  });
});
