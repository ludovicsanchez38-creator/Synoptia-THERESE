/**
 * P-140 (persona Zoé, cycle 13) : dans « Travaux », les lignes étaient des
 * textes inertes, alors que c'était le seul endroit qui savait que la trame
 * tournait. Une ligne ouvre l'objet qu'elle nomme quand on le connaît ; sans
 * objet sûr, elle reste un texte (aucune destination inventée).
 *
 * Décision et Atelier ne vivent qu'en mémoire pendant leur exécution : une
 * fois terminés, rien ne permet de rouvrir celui-là précisément.
 */
import type { Traitement } from '../services/api';

export type DestinationDuTravail =
  | { kind: 'document'; id: string }
  | { kind: 'conversation'; id: string }
  | { kind: 'vue'; vue: 'projects' | 'files' }
  | { kind: 'scenario'; scenario: 'board' | 'atelier' }
  | { kind: 'action'; id: string };

/** Le panneau des travaux vit dans l'en-tête ; la coque écoute cet événement. */
export const EVENEMENT_OUVRIR_TRAVAIL = 'therese:ouvrir-travail';

export function destinationDuTravail(travail: Traitement): DestinationDuTravail | null {
  const enCours = travail.state === 'running' || travail.state === 'queued';
  switch (travail.type) {
    case 'document_outline':
      return travail.entity_id ? { kind: 'document', id: travail.entity_id } : null;
    case 'chat':
    case 'deep-research':
      return travail.conversation_id ? { kind: 'conversation', id: travail.conversation_id } : null;
    case 'project_sync':
      return { kind: 'vue', vue: 'projects' };
    case 'indexation':
      return { kind: 'vue', vue: 'files' };
    case 'board':
    case 'atelier':
      return enCours ? { kind: 'scenario', scenario: travail.type } : null;
    // B-1477 : le moteur relit une action par son identifiant (entity_id),
    // en cours comme terminée ; sa ligne rouvre le résultat.
    case 'action':
      return travail.entity_id ? { kind: 'action', id: travail.entity_id } : null;
    default:
      return null;
  }
}

export interface ActionsDOuverture {
  ouvrirVue: (vue: 'documents' | 'projects' | 'files') => void;
  ouvrirDocument: (id: string) => void;
  ouvrirConversation: (id: string) => void;
  ouvrirScenario: (scenario: 'board' | 'atelier') => void;
  ouvrirAction: (id: string) => void;
}

export function ouvrirLeTravail(cible: DestinationDuTravail, actions: ActionsDOuverture): void {
  if (cible.kind === 'document') {
    actions.ouvrirVue('documents');
    actions.ouvrirDocument(cible.id);
  } else if (cible.kind === 'conversation') {
    actions.ouvrirConversation(cible.id);
  } else if (cible.kind === 'vue') {
    actions.ouvrirVue(cible.vue);
  } else if (cible.kind === 'action') {
    actions.ouvrirAction(cible.id);
  } else {
    actions.ouvrirScenario(cible.scenario);
  }
}
