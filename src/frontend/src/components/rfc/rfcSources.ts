/**
 * Références serveur du mini-chat RFC (tour 7 du lot confidentialité).
 *
 * Seules les réponses terminées avec un identifiant serveur sont reprises ;
 * une réponse refusée, interrompue ou coupée reste affichée sans être reprise.
 */

export interface RFCMessage {
  sourceId?: string;
  /** Réponse sans identifiant serveur (refus, arrêt, coupe) : jamais reprise. */
  horsSuite?: boolean;
  id: string;
  role: 'user' | 'assistant';
  content: string;
}

/** Identifiants serveur des réponses vérifiées, sans doublon, dans l'ordre. */
export function sourcesVerifiees(messages: RFCMessage[], initiales: string[] = []): string[] {
  return [...new Set([...initiales, ...messages.flatMap(m => (m.role === 'assistant' && m.sourceId ? [m.sourceId] : []))])];
}

/** Tour 8 : une réponse supprimée côté moteur n'est plus reprise ni bloquante. */
export function retirerSources(messages: RFCMessage[], absentes: string[]): RFCMessage[] {
  if (!absentes.length) return messages;
  const retirees = new Set(absentes);
  return messages.map(m => (m.sourceId && retirees.has(m.sourceId) ? { ...m, sourceId: undefined, horsSuite: true } : m));
}
