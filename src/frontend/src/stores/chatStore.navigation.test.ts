import { describe, it, expect, beforeEach } from 'vitest';
import { useChatStore } from './chatStore';
import { useNavigationStore } from './navigationStore';

/**
 * BUG-107 (Capov, 0.21.0) : depuis la vue Accueil (introduite en 0.21), créer ou
 * sélectionner une conversation ne ramenait pas la zone centrale sur le chat.
 * Symptômes : Cmd+N « n'apparaît pas », clic sur l'historique « n'ouvre rien ».
 * Cause racine : aucun point central ne garantissait `activeView === 'chat'`
 * lors de l'activation d'une conversation. On verrouille ça au niveau du store.
 */
describe('chatStore — activer une conversation affiche le chat (BUG-107)', () => {
  beforeEach(() => {
    useNavigationStore.setState({ activeView: 'crm', history: [] });
    useChatStore.setState({ conversations: [], currentConversationId: null });
  });

  it('createConversation ramène la vue active sur le chat depuis une autre vue', () => {
    // 28/08 : « l'Accueil » n'est plus une vue embarquée mais l'écran de la
    // coque. Ce test vérifie le retour au chat DEPUIS ailleurs : n'importe
    // quelle vue réelle fait l'affaire.
    expect(useNavigationStore.getState().activeView).toBe('crm');
    useChatStore.getState().createConversation();
    expect(useNavigationStore.getState().activeView).toBe('chat');
  });

  it('loadConversation ramène la vue active sur le chat depuis une autre vue', () => {
    const id = useChatStore.getState().createConversation();
    // Re-simule une autre vue ouverte avant la sélection dans la sidebar.
    useNavigationStore.setState({ activeView: 'crm', history: [] });
    useChatStore.getState().loadConversation(id);
    expect(useNavigationStore.getState().activeView).toBe('chat');
  });
});
