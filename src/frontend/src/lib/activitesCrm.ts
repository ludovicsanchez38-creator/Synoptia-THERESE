/**
 * Présentation d'une activité CRM à l'écran.
 *
 * B-1353 (persona Claire, cycle 13) : l'historique affichait les codes que le
 * moteur écrit pour lui-même : le type (`score_change`, `note`), le titre
 * « Score: 50 → 85 » et le motif « Raison: initial_creation ». Les activités
 * déjà enregistrées gardent ces textes en base ; la traduction se fait donc à
 * l'affichage, pour les anciennes comme pour les nouvelles.
 */
import type { ActivityResponse } from '../services/api';
import { libelleDEtape } from '../components/crm/pipelineEtapes';

const LIBELLES_DE_TYPE: Record<string, string> = {
  email: 'E-mail',
  call: 'Appel',
  meeting: 'Rendez-vous',
  note: 'Note',
  stage_change: 'Changement d’étape',
  score_change: 'Score',
};

export function libelleTypeActivite(type: string): string {
  return LIBELLES_DE_TYPE[type] ?? 'Activité';
}

const MOTIFS: Record<string, string> = {
  initial_creation: 'création de la fiche',
  manual_recalculation: 'recalcul demandé',
  batch_recalculation: 'recalcul général',
  recalculation: 'recalcul',
};

/** Le motif d'un recalcul de score, écrit par `update_contact_score`. */
export function motifLisible(motif: string): string {
  const code = motif.trim();
  if (MOTIFS[code]) return MOTIFS[code];
  if (code.startsWith('update_')) return 'fiche modifiée';
  if (code.startsWith('interaction_')) return 'nouvelle interaction';
  if (code.startsWith('stage_change_')) return 'changement d’étape';
  // Un code inconnu reste un code : il ne s'affiche pas. Un texte libre
  // (espaces, accents) est déjà une phrase.
  if (/^[a-z0-9_,]+$/.test(code)) return 'recalcul';
  return code;
}

/** B-1385 : « Stage: contact -> discovery » devient « Étape : Contact → Découverte ». */
function presenterChangementDEtape(activity: ActivityResponse): { titre: string; description: string } {
  let ancienne: unknown;
  let nouvelle: unknown;
  try {
    ({ old_stage: ancienne, new_stage: nouvelle } = JSON.parse(activity.extra_data ?? '') as {
      old_stage?: unknown; new_stage?: unknown;
    });
  } catch {
    const lu = /^Stage\s*:\s*(\S+)\s*-?>\s*(\S+)/.exec(activity.title);
    if (lu) [, ancienne, nouvelle] = lu;
  }
  const titre = typeof ancienne === 'string' && typeof nouvelle === 'string'
    ? `Étape : ${libelleDEtape(ancienne)} → ${libelleDEtape(nouvelle)}`
    : 'Changement d’étape';
  return { titre, description: 'Changement d’étape dans le pipeline' };
}

export function presenterActivite(activity: ActivityResponse): { titre: string; description: string | null } {
  if (activity.type === 'stage_change') return presenterChangementDEtape(activity);
  if (activity.type !== 'score_change') {
    return { titre: activity.title, description: activity.description ?? null };
  }
  let ancien: unknown;
  let nouveau: unknown;
  let motif: unknown;
  try {
    ({ old_score: ancien, new_score: nouveau, reason: motif } = JSON.parse(activity.extra_data ?? '') as {
      old_score?: unknown; new_score?: unknown; reason?: unknown;
    });
  } catch {
    // Données illisibles : on retombe sur le titre et la description.
  }
  const titre = typeof ancien === 'number' && typeof nouveau === 'number'
    ? `Score recalculé : ${ancien} → ${nouveau}`
    : activity.title.replace(/^Score\s*:\s*/, 'Score recalculé : ');
  const motifBrut = typeof motif === 'string'
    ? motif
    : (activity.description ?? '').replace(/^Raison\s*:\s*/, '');
  return { titre, description: motifBrut ? `Motif : ${motifLisible(motifBrut)}` : null };
}
