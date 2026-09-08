/** P-048 (revue COCO) : le retard d'un livrable se juge par jour civil, pas
 * à l'instant : une échéance « aujourd'hui » (stockée à minuit) n'est pas en
 * retard toute la journée. */
import { localDateKey } from './civilDate';

export const STATUTS_LIVRABLE = ['a_faire', 'en_cours', 'en_revision', 'valide'] as const;
export type StatutLivrable = (typeof STATUTS_LIVRABLE)[number];

export function estEnRetard(
  livrable: { due_date: string | null; status: string },
  maintenant: Date = new Date(),
): boolean {
  if (!livrable.due_date || livrable.status === 'valide') return false;
  const echeance = new Date(livrable.due_date);
  if (!Number.isFinite(echeance.getTime())) return false;
  return localDateKey(echeance) < localDateKey(maintenant);
}
