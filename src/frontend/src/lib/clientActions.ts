/**
 * THÉRÈSE v2 - Actions déterministes côté client (tranche 1a, 10/07/2026).
 *
 * Le backend émet un événement `client_action` pour un message-action pur
 * ({action: ouvrir email}) : l'exécution passe par le registre d'actions
 * frontend (actionRegistry), JAMAIS par le LLM. Fonction pure et testable,
 * appelée par le consommateur du stream (ChatInput).
 *
 * BUG-139 (harmonisation 17/07) : dans la coque 0.40, le registre classique
 * pilote le navigationStore que la coque n'écoute pas - « J'ouvre le CRM »
 * répondait sans naviguer. On émet d'abord un événement REVENDICABLE : si la
 * coque est montée, elle le prend (preventDefault) et ouvre la vue embarquée ;
 * sinon, repli sur le registre de l'interface classique.
 */
import type { StreamChunk } from '../services/api/chat';
import { runAction } from './actionRegistry';

export const CLIENT_ACTION_EVENT = 'therese:client-action';

/**
 * Exécute une navigation déterministe côté client : événement revendicable
 * (la coque 0.40 le prend si elle est montée), sinon registre classique.
 * Utilisé par le stream (client_action backend) ET par la sélection directe
 * d'une commande / de navigation (BUG-139 suite : dictée, zéro aller-retour).
 */
export function runNavigationAction(actionId: string): boolean {
  if (typeof window !== 'undefined') {
    const event = new CustomEvent(CLIENT_ACTION_EVENT, {
      detail: { actionId },
      cancelable: true,
    });
    const notPrevented = window.dispatchEvent(event);
    if (!notPrevented) return true; // revendiqué par la coque
  }
  return runAction(actionId);
}

export function handleClientActionChunk(chunk: StreamChunk): boolean {
  const ca = chunk.client_action as
    | { action?: string; action_id?: string; target?: string }
    | undefined;
  if (!ca || ca.action !== 'navigate' || !ca.action_id) return false;
  return runNavigationAction(ca.action_id);
}
