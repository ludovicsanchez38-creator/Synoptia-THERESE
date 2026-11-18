import { render, screen } from '@testing-library/react';
import { expect, it, vi } from 'vitest';
import { useChatStore } from '../../stores/chatStore';
import { MessageBubble } from './MessageBubble';

vi.mock('../../services/api', async () => {
  const reel = await vi.importActual<typeof import('../../services/api')>('../../services/api');
  return { ...reel, downloadSkillFile: vi.fn(), fetchImageObjectUrl: vi.fn() };
});

it('le badge de la réponse affiche le fournisseur effectif après une bascule', () => {
  useChatStore.setState({ conversations: [], currentConversationId: null, fournisseurCourant: 'anthropic' });
  useChatStore.getState().createConversation();
  const id = useChatStore.getState().addMessage({ role: 'assistant', content: 'Réponse du repli' });
  useChatStore.getState().setMessageMetadata(id, {
    input_tokens: 10, output_tokens: 5, cost_eur: 0, provider: 'openai', model: 'modele-repli',
  });
  const message = useChatStore.getState().currentConversation()?.messages.find(element => element.id === id);
  expect(message).toBeDefined();
  render(<MessageBubble message={message!} />);

  expect(screen.getByText('Cloud')).toBeInTheDocument();
  expect(screen.getByTitle(/Réponse cloud \(openai\)/)).toBeInTheDocument();
  expect(screen.queryByTitle(/Réponse cloud \(anthropic\)/)).toBeNull();
});
