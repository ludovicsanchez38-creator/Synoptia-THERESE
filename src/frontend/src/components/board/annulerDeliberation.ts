/**
 * 0.47 - Annulation canonique d'une délibération du Board.
 *
 * Un abort() local ne coupe que le transport : le backend continuait de
 * consulter les conseillers (défaut relevé au plan 0.42). Le contrat :
 * demander l'arrêt au traitement durable (identifiant reçu en premier
 * événement SSE du flux), PUIS fermer le transport. Si l'appel échoue ou
 * qu'aucun identifiant n'est connu (suivi en panne), le transport se coupe
 * quand même - le backend constate la déconnexion et pose cancelled.
 */
import { annulerTraitement } from '../../services/api/processingTasks';

export async function annulerDeliberation(
  taskId: string | null,
  couperLeTransport: () => void,
): Promise<void> {
  if (taskId) {
    try {
      await annulerTraitement(taskId);
    } catch {
      // Le transport coupé suffit : le backend posera cancelled.
    }
  }
  couperLeTransport();
}


/**
 * Revue jalon (F8) : capturer le controller À L'INSTANT du clic.
 *
 * Les handlers nettoient `abortRef.current` tout de suite (un nouveau run
 * peut démarrer) ; le repli asynchrone d'`annulerDeliberation` lisait alors
 * `null` et ne coupait jamais l'ancien transport.
 */
export function couperTransport(
  ref: { current: AbortController | null },
): () => void {
  const controller = ref.current;
  ref.current = null;
  return () => controller?.abort();
}
