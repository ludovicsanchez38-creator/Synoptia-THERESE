import { describe, expect, it } from 'vitest';
import { texteContexteTransmis } from './contexteTransmis';

describe('texteContexteTransmis (P-159)', () => {
  it('dit combien de messages passés ont été relus', () => {
    expect(texteContexteTransmis({ messages_relus: 12, messages_transmis: 12 }))
      .toBe('Contexte : 12 messages relus');
  });

  it('accorde le singulier et le zéro', () => {
    expect(texteContexteTransmis({ messages_relus: 1, messages_transmis: 1 }))
      .toBe('Contexte : 1 message relu');
    expect(texteContexteTransmis({ messages_relus: 0, messages_transmis: 0 }))
      .toBe('Contexte : aucun message relu');
  });

  it('dit quand la coupe du modèle en a retiré, et combien', () => {
    expect(texteContexteTransmis({ messages_relus: 50, messages_transmis: 30 }))
      .toBe('Contexte raccourci : 30 messages sur 50');
    expect(texteContexteTransmis({ messages_relus: 12, messages_transmis: 1 }))
      .toBe('Contexte raccourci : 1 message sur 12');
    expect(texteContexteTransmis({ messages_relus: 50, messages_transmis: 0 }))
      .toBe('Contexte raccourci : aucun message sur 50');
  });
});
