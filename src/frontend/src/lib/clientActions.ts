/**
 * THÉRÈSE v2 - Actions déterministes côté client (tranche 1a, 10/07/2026).
 *
 * Le backend émet un événement `client_action` pour un message-action pur
 * ({action: ouvrir email}) : l'exécution passe par le registre d'actions
 * frontend (actionRegistry), JAMAIS par le LLM. Fonction pure et testable,
 * appelée par le consommateur du stream (ChatInput).
 */
import type { StreamChunk } from '../services/api/chat';
import { runAction } from './actionRegistry';

export function handleClientActionChunk(chunk: StreamChunk): boolean {
  const ca = chunk.client_action as
    | { action?: string; action_id?: string; target?: string }
    | undefined;
  if (!ca || ca.action !== 'navigate' || !ca.action_id) return false;
  return runAction(ca.action_id);
}
