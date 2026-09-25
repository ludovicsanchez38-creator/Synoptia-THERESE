/**
 * B-1435 (recette P-146, lot 1, A-5) : sans boîte branchée, « Enregistrer
 * comme brouillon » ouvrait la carte « Confirmer l'enregistrement chez le
 * fournisseur email » ; l'échec ne venait qu'au clic. Règle tranchée le
 * 25/09 (délégation de Ludo) : la rédaction dit AVANT la confirmation
 * qu'aucune boîte n'est branchée, et le texte reste dans le champ.
 */
import { act, fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

const api = vi.hoisted(() => ({
  getEmailAuthStatus: vi.fn().mockResolvedValue({ accounts: [] }),
}));
vi.mock('../../services/api/email', async (importOriginal) => ({
  ...(await importOriginal<object>()),
  ...api,
}));

import { EmailMessageCanvas } from './EmailConversationCard';

function remplir() {
  fireEvent.change(screen.getByLabelText(/destinataire du brouillon/i), { target: { value: 'julien@example.test' } });
  fireEvent.change(screen.getByLabelText(/objet du brouillon/i), { target: { value: 'Devis' } });
  const corps = screen.getAllByRole('textbox').find((c) => c.tagName === 'TEXTAREA');
  if (corps) fireEvent.change(corps, { target: { value: 'Bonjour Julien' } });
}

describe('B-1435 : rédaction sans boîte branchée', () => {
  it('le dit avant toute confirmation, et n’enregistre rien', () => {
    const onSaveDraft = vi.fn();
    render(
      <EmailMessageCanvas
        resource={null}
        nouvelleRedaction
        aucuneBoite
        onRetry={vi.fn()}
        onGenerateDraft={vi.fn()}
        onSaveDraft={onSaveDraft}
        onOpenClassic={vi.fn()}
      />,
    );
    expect(screen.getByText(/Aucune boîte n’est branchée/)).toBeInTheDocument();
    remplir();
    const enregistrer = screen.getByRole('button', { name: /Enregistrer comme brouillon/ });
    expect(enregistrer).toBeDisabled();
    fireEvent.click(enregistrer);
    expect(screen.queryByTestId('email-draft-confirmation')).toBeNull();
    expect(onSaveDraft).not.toHaveBeenCalled();
  });

  it('depuis l’établi, « Écrire » sans boîte le dit', async () => {
    const { useChatStore } = await import('../../stores/chatStore');
    const { useNavigationStore } = await import('../../stores/navigationStore');
    const { _clearEscapeHandlers } = await import('../../lib/escapeStack');
    const { ConversationCanvasPrototype } = await import('./ConversationCanvasPrototype');

    _clearEscapeHandlers();
    useChatStore.setState({ conversations: [], currentConversationId: null, isStreaming: false });
    useNavigationStore.setState({ activeView: null, history: [] } as never);
    window.history.replaceState({}, '', '/?interface=conversation-canvas');

    render(<ConversationCanvasPrototype />);
    await act(async () => { await Promise.resolve(); });
    await act(async () => {
      fireEvent.click(screen.getByRole('button', { name: /Écrire/ }));
    });
    expect(await screen.findByText(/Aucune boîte n’est branchée/)).toBeInTheDocument();
  });
});
