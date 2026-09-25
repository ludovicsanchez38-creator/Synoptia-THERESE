/**
 * Le texte affiché dans la bulle de Thérèse quand sa réponse échoue.
 *
 * B-1395 (persona Zoé, cycle 13) : recharger la page pendant une réponse
 * laissait « network error », l'exception brute du navigateur, comme réponse
 * de Thérèse. Une coupure du flux (rechargement, moteur arrêté, réseau) se dit
 * en français, avec le geste à faire ; la question reste dans le champ.
 */
import { ApiError } from '../services/api/core';

const REPONSE_INTERROMPUE =
  'Réponse interrompue : la connexion au moteur de THÉRÈSE a été coupée avant la fin. '
  + 'Ta question est restée dans le champ, renvoie-la.';

export function messageDErreurDuFlux(error: unknown): string {
  if (error instanceof ApiError) {
    // Le client code 0 une requête qui n'a jamais obtenu de réponse.
    if (error.status === 0) return REPONSE_INTERROMPUE;
    return `Erreur serveur (${error.status}): ${error.message}`;
  }
  // `fetch` et la lecture d'un flux lèvent un TypeError sur coupure réseau
  // (« network error », « Failed to fetch », « Load failed »…).
  if (error instanceof TypeError) return REPONSE_INTERROMPUE;
  if (error instanceof Error) return error.message;
  return "Désolée, une erreur s'est produite. Réessaie.";
}
