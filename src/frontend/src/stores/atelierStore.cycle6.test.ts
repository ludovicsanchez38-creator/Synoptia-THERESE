/**
 * Cycle 6, lecteur #220 (stores/atelierStore.ts) : `startAgentStream`
 * écrasait `currentStreamingId` sans clore le flux précédent ; deux
 * `agent_start` sans `agent_done` laissaient le premier message en
 * `isStreaming: true` pour toujours (le « curseur fantôme » du chat).
 */
import { beforeEach, describe, expect, it } from 'vitest';

import { useAtelierStore } from './atelierStore';

describe('#220 : un nouveau flux d’agent clôt le précédent', () => {
  beforeEach(() => {
    useAtelierStore.setState({ messages: [], isStreaming: false, currentStreamingId: null });
  });

  it('après deux agent_start, seul le second message est en cours', () => {
    const s = useAtelierStore.getState();
    const premier = s.startAgentStream('katia');
    const second = useAtelierStore.getState().startAgentStream('zezette');
    const messages = useAtelierStore.getState().messages;
    expect(messages.find((m) => m.id === premier)?.isStreaming).toBe(false);
    expect(messages.find((m) => m.id === second)?.isStreaming).toBe(true);
    expect(useAtelierStore.getState().currentStreamingId).toBe(second);
  });
});
