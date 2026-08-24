/**
 * project.sync (0.45) - synchroniser un dossier local avec l'index d'un projet.
 *
 * Timeouts adaptés (challenge V2.1) : le plan hashe TOUT le dossier, le
 * défaut apiFetch de 30 s le tuerait sur un gros répertoire. L'apply répond
 * 202 immédiatement et se suit par l'état.
 */
import { request } from './core';

const DELAI_PLAN_MS = 10 * 60 * 1000; // hash systématique : proportionnel au dossier

export interface SyncRacine {
  racine: string;
  generation: number;
}

export interface SyncOperation {
  id: string;
  type: 'indexer' | 'reindexer' | 'retirer' | 'conflit';
  chemin: string;
  etat: 'a_faire' | 'fait' | 'echec' | 'obsolete';
  erreur: string | null;
  attempt_count: number;
  last_attempt_at: string | null;
}

export interface SyncPlan {
  id: string;
  etat: 'propose' | 'en_cours' | 'applique' | 'applique_partiel' | 'caduc';
  generation_racine: number;
  nb_indexer: number;
  nb_reindexer: number;
  nb_retirer: number;
  nb_conflits: number;
  nb_inchanges: number;
  created_at: string;
  operations?: SyncOperation[];
}

export interface SyncEtat {
  racine: string | null;
  generation: number | null;
  dernier_plan: SyncPlan | null;
  run: { etat: string; progression: number | null } | null;
}

export async function definirRacineSync(
  projectId: string, chemin: string
): Promise<SyncRacine> {
  return request<SyncRacine>(`/api/projects/${projectId}/sync/racine`, {
    method: 'PUT',
    body: JSON.stringify({ chemin }),
  });
}

export async function retirerRacineSync(projectId: string): Promise<void> {
  await request(`/api/projects/${projectId}/sync/racine`, { method: 'DELETE' });
}

export async function preparerPlanSync(projectId: string): Promise<SyncPlan> {
  return request<SyncPlan>(`/api/projects/${projectId}/sync/plan`, {
    method: 'POST',
    timeoutMs: DELAI_PLAN_MS,
  });
}

export async function appliquerPlanSync(
  projectId: string, planId: string
): Promise<void> {
  await request(`/api/projects/${projectId}/sync/apply`, {
    method: 'POST',
    body: JSON.stringify({ plan_id: planId }),
  });
}

export async function etatSync(projectId: string): Promise<SyncEtat> {
  return request<SyncEtat>(`/api/projects/${projectId}/sync`);
}

export async function journalSync(
  projectId: string, page = 0
): Promise<{ operations: SyncOperation[]; total?: number }> {
  return request(`/api/projects/${projectId}/sync/journal?page=${page}`);
}
