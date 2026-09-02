import { beforeEach, describe, expect, it, vi } from 'vitest';
import { act, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { PrototypeConversationDrawer } from './PrototypeConversationDrawer';
import { _clearEscapeHandlers, runTopEscapeHandler } from '../../lib/escapeStack';
import { useChatStore } from '../../stores/chatStore';

vi.mock('../../hooks/useConversationSync', () => ({
  useConversationSync: vi.fn(() => ({ syncConversations: vi.fn(), loadConversationMessages: vi.fn() })),
}));

const { renameRemote, deleteRemote, exportRemote } = vi.hoisted(() => ({
  renameRemote: vi.fn(),
  deleteRemote: vi.fn(),
  exportRemote: vi.fn(),
}));

vi.mock('../../services/api/chat', () => ({
  renameConversation: renameRemote,
  deleteConversation: deleteRemote,
  exportConversation: exportRemote,
}));

describe('PrototypeConversationDrawer', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    _clearEscapeHandlers();
    renameRemote.mockResolvedValue({});
    deleteRemote.mockResolvedValue(undefined);
    exportRemote.mockResolvedValue(undefined);
    useChatStore.setState({
      conversations: [{
        id: 'conversation-1',
        title: 'Préparation rendez-vous réel',
        messages: [],
        messageCount: 3,
        createdAt: new Date(),
        updatedAt: new Date(),
        synced: true,
      }],
      currentConversationId: null,
    });
  });

  it('affiche uniquement les conversations du store et ouvre la sélection', () => {
    const onClose = vi.fn();
    const onOpenChat = vi.fn();
    render(<PrototypeConversationDrawer onClose={onClose} onOpenChat={onOpenChat} />);

    expect(screen.getByText('Préparation rendez-vous réel')).toBeInTheDocument();
    expect(screen.queryByText(/PROPULSER|Programme parrainage|12 conversations/)).not.toBeInTheDocument();

    fireEvent.click(screen.getByText('Préparation rendez-vous réel'));

    expect(useChatStore.getState().currentConversationId).toBe('conversation-1');
    expect(onClose).toHaveBeenCalledTimes(1);
    expect(onOpenChat).toHaveBeenCalledTimes(1);
  });

  it('recherche et crée une vraie conversation locale', () => {
    const onClose = vi.fn();
    const onOpenChat = vi.fn();
    render(<PrototypeConversationDrawer onClose={onClose} onOpenChat={onOpenChat} />);

    fireEvent.change(screen.getByLabelText('Rechercher une conversation'), { target: { value: 'absente' } });
    expect(screen.getByText('Aucune conversation trouvée')).toBeInTheDocument();

    fireEvent.change(screen.getByLabelText('Rechercher une conversation'), { target: { value: '' } });
    fireEvent.click(screen.getByRole('button', { name: 'Nouvelle conversation' }));

    expect(useChatStore.getState().conversations[0].title).toBe('Nouvelle conversation');
    expect(onOpenChat).toHaveBeenCalledTimes(1);
  });

  it('expose les trois surfaces du tiroir sans panneau concurrent', () => {
    const { rerender } = render(
      <PrototypeConversationDrawer
        surface="new"
        onClose={vi.fn()}
        onOpenChat={vi.fn()}
      />,
    );

    expect(screen.getByRole('button', { name: 'Nouvelle conversation' })).toHaveFocus();

    rerender(
      <PrototypeConversationDrawer
        surface="search"
        onClose={vi.fn()}
        onOpenChat={vi.fn()}
      />,
    );
    expect(screen.getByLabelText('Rechercher une conversation')).toHaveFocus();

    fireEvent.change(screen.getByLabelText('Rechercher une conversation'), {
      target: { value: 'rendez-vous' },
    });
    rerender(
      <PrototypeConversationDrawer
        surface="history"
        onClose={vi.fn()}
        onOpenChat={vi.fn()}
      />,
    );

    expect(screen.getByLabelText('Historique des conversations')).toHaveFocus();
    expect(screen.getByLabelText('Rechercher une conversation')).toHaveValue('');
  });

  it('persiste le renommage dans le backend', async () => {
    render(<PrototypeConversationDrawer onClose={vi.fn()} onOpenChat={vi.fn()} />);

    fireEvent.click(screen.getByRole('button', { name: 'Actions pour Préparation rendez-vous réel' }));
    fireEvent.click(screen.getByRole('menuitem', { name: 'Renommer' }));
    fireEvent.change(screen.getByLabelText('Nouveau titre'), { target: { value: 'Rendez-vous Camille' } });
    fireEvent.click(screen.getByRole('button', { name: 'Enregistrer' }));

    await waitFor(() => expect(renameRemote).toHaveBeenCalledWith('conversation-1', 'Rendez-vous Camille'));
    expect(useChatStore.getState().conversations[0].title).toBe('Rendez-vous Camille');
  });

  it('demande une confirmation avant la suppression backend', async () => {
    render(<PrototypeConversationDrawer onClose={vi.fn()} onOpenChat={vi.fn()} />);

    fireEvent.click(screen.getByRole('button', { name: 'Actions pour Préparation rendez-vous réel' }));
    fireEvent.click(screen.getByRole('menuitem', { name: 'Supprimer' }));

    expect(screen.getByTestId('conversation-delete-confirmation')).toBeInTheDocument();
    expect(deleteRemote).not.toHaveBeenCalled();

    fireEvent.click(screen.getByRole('button', { name: 'Confirmer la suppression' }));
    await waitFor(() => expect(deleteRemote).toHaveBeenCalledWith('conversation-1'));
    expect(useChatStore.getState().conversations).toHaveLength(0);
  });

  it('conserve la conversation courante pendant une réponse en cours', () => {
    const onClose = vi.fn();
    const onOpenChat = vi.fn();
    render(
      <PrototypeConversationDrawer
        navigationLocked
        onClose={onClose}
        onOpenChat={onOpenChat}
      />,
    );

    fireEvent.click(screen.getByText('Préparation rendez-vous réel'));

    expect(screen.getByRole('alert')).toHaveTextContent(
      'Arrête la réponse en cours avant de changer de conversation.',
    );
    expect(useChatStore.getState().currentConversationId).toBeNull();
    expect(onClose).not.toHaveBeenCalled();
    expect(onOpenChat).not.toHaveBeenCalled();
  });

  it('ferme le menu avant le tiroir avec Échap et expose le pattern menu', () => {
    // B-204 : un panneau latéral ne pilote pas le clavier, sa cascade Échap
    // ne passe donc plus par le piège de focus. Les overlays INTERNES du
    // tiroir (menu, renommage, suppression) passent par la pile d'Échap de
    // l'application ; la fermeture du tiroir, elle, revient à la coque, APRÈS
    // les modales - sinon le tiroir volerait Échap aux Réglages ouverts
    // par-dessus. Le contrat mesuré est le même : le menu d'abord, et rien
    // d'interne à fermer ensuite. Que la coque ferme alors le tiroir sur une
    // vraie frappe est mesuré dans PanneauxNonModaux.test.tsx (« Échap le
    // ferme toujours, par le vrai chemin clavier de la coque »).
    const onClose = vi.fn();
    render(<PrototypeConversationDrawer onClose={onClose} onOpenChat={vi.fn()} />);

    const trigger = screen.getByRole('button', { name: 'Actions pour Préparation rendez-vous réel' });
    fireEvent.click(trigger);
    expect(trigger).toHaveAttribute('aria-expanded', 'true');
    expect(screen.getByRole('menuitem', { name: 'Renommer' })).toHaveFocus();

    act(() => { expect(runTopEscapeHandler()).toBe(true); });
    expect(screen.queryByRole('menu')).not.toBeInTheDocument();
    expect(onClose).not.toHaveBeenCalled();
    expect(trigger).toHaveFocus();

    // Plus aucun overlay interne : la pile rend la main, et personne n'a
    // fermé le tiroir dans le dos de la coque.
    act(() => { expect(runTopEscapeHandler()).toBe(false); });
    expect(onClose).not.toHaveBeenCalled();
  });
});
