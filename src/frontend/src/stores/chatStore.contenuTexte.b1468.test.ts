/**
 * B-1468 (recette P-146, lot 5, KO-2) : un message dont le contenu n'était
 * pas du texte (résultat brut d'un connecteur) faisait planter la bulle
 * (`texte.replace is not a function`), puis, persisté, le tiroir des
 * conversations à chaque ouverture. Le store garantit un contenu textuel, à
 * l'ajout comme à la restauration du cache.
 */
import { describe, expect, it } from 'vitest';

import { useChatStore } from './chatStore';

describe('B-1468 : le contenu d’un message est toujours du texte', () => {
  it('à l’ajout', () => {
    useChatStore.setState({ conversations: [], currentConversationId: null });
    useChatStore.getState().addMessage({
      role: 'assistant',
      content: { content: [{ type: 'text', text: 'Il est 22:41.' }] } as unknown as string,
    });
    const conversation = useChatStore.getState().conversations[0];
    expect(typeof conversation.messages[0].content).toBe('string');
    expect(conversation.messages[0].content).toContain('22:41');
  });

  it('à la restauration d’un cache empoisonné', () => {
    const lu = { conversations: [{
      id: 'conv-1', title: 'Heure', createdAt: new Date(), updatedAt: new Date(),
      messages: [{ id: 'm-1', role: 'assistant', content: { heure: '22:41' }, timestamp: new Date() }],
    }] };
    const fusion = useChatStore.persist.getOptions().merge;
    expect(fusion).toBeDefined();
    const etat = fusion!(lu, useChatStore.getState());
    expect(typeof etat.conversations[0].messages[0].content).toBe('string');
  });
});
