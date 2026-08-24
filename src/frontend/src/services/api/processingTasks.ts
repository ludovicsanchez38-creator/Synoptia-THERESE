/**
 * Traitements longs (0.46) - « tâches » est pris par les todos métier.
 */
import { request } from './core';

export interface Traitement {
  id: string;
  type: string;
  label: string;
  state:
    | 'queued'
    | 'running'
    | 'cancel_requested'
    | 'cancelled'
    | 'interrupted'
    | 'done'
    | 'failed';
  step: string | null;
  progress: number | null;
  project_id: string | null;
  conversation_id: string | null;
  error: string | null;
  created_at: string | null;
  started_at: string | null;
  finished_at: string | null;
  can_cancel: boolean;
}

export async function listerTraitements(
  options: { actives?: boolean; limit?: number } = {},
): Promise<Traitement[]> {
  const params = new URLSearchParams();
  if (options.actives !== undefined) params.set('actives', String(options.actives));
  if (options.limit !== undefined) params.set('limit', String(options.limit));
  const suffixe = params.toString() ? `?${params.toString()}` : '';
  const corps = await request<{ traitements: Traitement[] }>(
    `/api/processing-tasks${suffixe}`,
  );
  return corps.traitements;
}

export async function annulerTraitement(
  id: string,
): Promise<{ state: string; resultat: string; transmise: boolean }> {
  return request(`/api/processing-tasks/${id}/cancel`, { method: 'POST' });
}
