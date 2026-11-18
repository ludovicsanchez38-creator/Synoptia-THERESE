/**
 * B-1940 : en rédaction libre, l’en-tête dit « Nouveau message » mais la
 * section reste celle d’une réponse, le champ propose encore de générer,
 * et le ton et la longueur restent alors qu’il n’y a rien à générer.
 */
import { render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

import { EmailMessageCanvas } from './EmailConversationCard';

describe('B-1940 : la rédaction libre ne parle pas d’une réponse à générer', () => {
  it('la section, le champ et les réglages de génération s’effacent', () => {
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

    expect(screen.getByRole('heading', { name: 'Ton message' })).toBeInTheDocument();
    expect(screen.queryByRole('heading', { name: 'Brouillon de réponse' })).not.toBeInTheDocument();
    expect(screen.getByLabelText('Corps du brouillon')).toHaveAttribute('placeholder', 'Écris ton message…');
    expect(screen.queryByLabelText('Ton du brouillon')).not.toBeInTheDocument();
    expect(screen.queryByLabelText('Longueur du brouillon')).not.toBeInTheDocument();
  });
});
