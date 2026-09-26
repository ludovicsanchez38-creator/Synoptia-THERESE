/**
 * Les prestations : ce que Ludo vend à quelqu'un (tranche C du 29/08).
 *
 * Ce n'est pas un pipeline d'opportunités. Une négociation est une formation
 * pas encore signée, un client actif la même chose en cours : les séparer
 * aurait donné deux listes pour un seul métier.
 */
import { request } from './core';
import type { IdEtapeDePrestation } from '../../components/crm/pipelineEtapes';

/**
 * P-132 : la phase d'une prestation est une étape du pipeline
 * (`ETAPES_DE_PRESTATION`, pipelineEtapes.ts). Les mots affichés viennent de
 * cette seule liste ; l'ancien vocabulaire (Piste, Signée, En cours…) n'existe
 * plus.
 */
export type PhaseDePrestation = IdEtapeDePrestation;

export interface Prestation {
  id: string;
  contact_id: string;
  intitule: string;
  montant_ht: number | null;
  /** Lu tel que la base le porte : une valeur inconnue reste possible. */
  phase: string;
  created_at: string;
  updated_at: string;
}

export async function listerLesPrestations(contactId: string): Promise<Prestation[]> {
  return request<Prestation[]>(`/api/prestations?contact_id=${encodeURIComponent(contactId)}`);
}

export async function creerUnePrestation(corps: {
  contact_id: string;
  intitule: string;
  montant_ht?: number | null;
  phase?: PhaseDePrestation;
}): Promise<Prestation> {
  return request<Prestation>('/api/prestations', {
    method: 'POST',
    body: JSON.stringify(corps),
  });
}

export async function changerLaPhase(
  id: string,
  phase: PhaseDePrestation,
): Promise<Prestation> {
  return request<Prestation>(`/api/prestations/${id}`, {
    method: 'PATCH',
    body: JSON.stringify({ phase }),
  });
}

export async function supprimerUnePrestation(id: string): Promise<void> {
  await request(`/api/prestations/${id}`, { method: 'DELETE' });
}
