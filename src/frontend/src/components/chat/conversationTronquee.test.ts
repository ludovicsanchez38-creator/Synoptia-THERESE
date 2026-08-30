import { describe, expect, it } from 'vitest';
import { conversationEstTronquee } from './conversationTronquee';

describe('conversationEstTronquee', () => {
  it('est vraie quand le listing annonce plus que la fenêtre chargée', () => {
    expect(
      conversationEstTronquee({ messageCount: 110, messages: { length: 100 } }),
    ).toBe(true);
  });

  it('est fausse quand tout le fil est à l’écran', () => {
    expect(
      conversationEstTronquee({ messageCount: 12, messages: { length: 12 } }),
    ).toBe(false);
  });

  it('est fausse sans conversation', () => {
    expect(conversationEstTronquee(null)).toBe(false);
  });
});
