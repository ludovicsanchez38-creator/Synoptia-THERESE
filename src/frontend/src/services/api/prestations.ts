/**
 * Les prestations : ce que Ludo vend à quelqu'un (tranche C du 29/08).
 *
 * Ce n'est pas un pipeline d'opportunités. Une négociation est une formation
 * pas encore signée, un client actif la même chose en cours : les séparer
 * aurait donné deux listes pour un seul métier.
 */
import { request } from './core';

export const PHASES_DE_PRESTATION = [
  'piste',
  'proposition',
  'gagne',
  'perdue',
  'en_cours',
  'terminee',
] as const;

export type PhaseDePrestation = (typeof PHASES_DE_PRESTATION)[number];

/** Les mots affichés. Le stockage reste en clé stable. */
export const LIBELLE_DE_PHASE: Record<PhaseDePrestation, string> = {
  piste: 'Piste',
  proposition: 'Proposition envoyée',
  gagne: 'Signée',
  perdue: 'Perdue',
  en_cours: 'En cours',
  terminee: 'Terminée',
};

export interface Prestation {
  id: string;
  contact_id: string;
  intitule: string;
  montant_ht: number | null;
  phase: PhaseDePrestation;
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
