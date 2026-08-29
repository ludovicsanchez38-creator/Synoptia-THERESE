/**
 * Entrée 10 du plan du 28/08 : « Écrire » ouvre un brouillon.
 *
 * Le verbe le plus simple de l'établi était le plus long à atteindre : Écrire
 * menait à « Messages à consulter », puis il fallait « Email complet », puis
 * « Nouveau ». Trois clics, quand ses sœurs ont leur bouton de création sur la
 * carte — « Préparer un devis » ouvre un devis d'un geste.
 *
 * Tranché avec la relecture : brouillon SANS envoi. Monter le composeur
 * complet ajouterait l'expédition dans une surface qui promet « brouillon
 * confirmé, aucun envoi » — elle perdrait la garantie qu'elle affiche. C'est
 * le pendant exact de `selectedInvoiceId === 'new-devis'`.
 */
import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

import { EmailMessageCanvas } from './EmailConversationCard';

function rendre(nouvelleRedaction: boolean, onOpenClassic = vi.fn()) {
  return render(
    <EmailMessageCanvas
      // Aucun message source : c'est tout le sujet de cette entrée.
      resource={null}
      nouvelleRedaction={nouvelleRedaction}
      onRetry={vi.fn()}
      onGenerateDraft={vi.fn()}
      onSaveDraft={vi.fn()}
      onOpenClassic={onOpenClassic}
    />,
  );
}

describe('Entrée 10 : « Écrire » mène à une rédaction', () => {
  it('propose destinataire, objet et corps', () => {
    rendre(true);

    expect(screen.getByLabelText(/destinataire du brouillon/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/objet du brouillon/i)).toBeInTheDocument();
  });

  it('ne peut pas envoyer : la surface promet un brouillon', () => {
    rendre(true);

    // Aucun contrôle dont le nom annonce un envoi. La garantie affichée par
    // ce canevas serait fausse le jour où l'un d'eux apparaîtrait.
    expect(screen.queryByRole('button', { name: /envoyer/i })).toBeNull();
  });

  it('offre la sortie qui, elle, sait envoyer', () => {
    const onOpenClassic = vi.fn();
    rendre(true, onOpenClassic);

    fireEvent.click(screen.getByRole('button', { name: 'Ouvrir Email' }));
    expect(onOpenClassic).toHaveBeenCalled();
  });

  it('sans cible de rédaction, le canevas reste ce qu’il était', () => {
    rendre(false);

    // Sans cible de rédaction, on retombe sur l'attente d'un message.
    expect(screen.queryByLabelText(/destinataire du brouillon/i)).toBeNull();
  });
});

// Le composant peut savoir rédiger sans que le verbe y mène : c'est le
// parcours qui compte, et le sabotage du branchement doit casser un test.
describe('Entrée 10 : le verbe « Écrire » y conduit vraiment', () => {
  it('depuis l’établi, Écrire ouvre la rédaction', async () => {
    const { act } = await import('@testing-library/react');
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

    // Une rédaction, pas « Messages à consulter ».
    expect(await screen.findByLabelText(/destinataire du brouillon/i)).toBeInTheDocument();
  });
});
