/**
 * Manifeste de capacités — accès typé au fichier canonique (0.44).
 *
 * Le manifeste ne remplace AUCUN registre. Il les relie : chaque `binding`
 * référence un identifiant qui existe déjà ailleurs (`actionRegistry`,
 * `AppView`, le registre de commandes du backend). C'est cette référence typée
 * qui rend les vérifications mécaniques possibles — et qui aurait empêché les
 * quatre raccourcis annoncés sans exister, comme la vue « Fichiers » absente de
 * la table du backend.
 *
 * La source est un JSON neutre partagé avec le sidecar Python
 * (`src/backend/app/data/capacites.json`), et non un fichier généré depuis ce
 * module : dans le pipeline de release, le sidecar est construit AVANT que le
 * frontend ne le soit, et ne verrait jamais un fichier produit ici.
 */
import type { AppView } from '../../stores/navigationStore';

import donnees from '../../../../backend/app/data/capacites.json';

export type CapabilityId = string;
export type EntrypointId = string;
export type RequirementId = string;

export type Famille = 'quotidien' | 'developper' | 'documents';

export interface TextesLocalises {
  'fr-FR': { nom: string; quoi: string };
}

export type Binding =
  | { registre: 'action'; actionId: string }
  | { registre: 'vue'; view: AppView }
  | { registre: 'commande'; commandId: string }
  | { registre: 'raccourci'; actionId: string }
  | { registre: 'scenario'; scenarioId: string }
  | { registre: 'lien_profond'; parametre: string }
  | { registre: 'ui'; composant: string; testid: string }
  | { registre: 'externe'; note: string }
  | { registre: 'tiroir'; carte: string };

export interface Capacite {
  id: CapabilityId;
  famille: Famille;
  textes: TextesLocalises;
  maturite: 'complete' | 'partielle';
  audience: 'tous' | 'contributeur';
  entrees: EntrypointId[];
  exigences: RequirementId[];
  limites?: string[];
  cycle: { introduite: string; remplacee_par?: CapabilityId };
}

export interface PointEntree {
  id: EntrypointId;
  capacites: CapabilityId[];
  type:
    | 'vue' | 'action' | 'commande' | 'raccourci'
    | 'scenario' | 'lien_profond' | 'ui_contextuelle' | 'outil' | 'api'
    | 'tiroir';
  binding: Binding;
  /** Déclaré, jamais déduit de l'ordre du tableau : l'ordre serait un contrat caché. */
  principal?: boolean;
  touches?: string;
}

interface Manifeste {
  schema: number;
  capacites: Capacite[];
  points_entree: PointEntree[];
  identifiants_reserves: CapabilityId[];
}

const manifeste = donnees as unknown as Manifeste;

export const SCHEMA_MANIFESTE = manifeste.schema;
export const CAPACITES: readonly Capacite[] = manifeste.capacites;
export const POINTS_ENTREE: readonly PointEntree[] = manifeste.points_entree;
export const IDENTIFIANTS_RESERVES: readonly CapabilityId[] =
  manifeste.identifiants_reserves;

export function capacite(id: CapabilityId): Capacite | undefined {
  return CAPACITES.find((c) => c.id === id);
}

export function pointEntree(id: EntrypointId): PointEntree | undefined {
  return POINTS_ENTREE.find((p) => p.id === id);
}

/** Le chemin à montrer quand il faut n'en montrer qu'un (aide, catalogue). */
export function accesPrincipal(id: CapabilityId): PointEntree | undefined {
  const cible = capacite(id);
  if (!cible) return undefined;
  return POINTS_ENTREE.find((p) => cible.entrees.includes(p.id) && p.principal);
}

/** Tous les chemins d'une capacité, dans l'ordre déclaré. */
export function accesDe(id: CapabilityId): PointEntree[] {
  const cible = capacite(id);
  if (!cible) return [];
  return cible.entrees
    .map((entree) => pointEntree(entree))
    .filter((p): p is PointEntree => p !== undefined);
}

/** Les capacités qu'une vue rend disponibles. */
export function capacitesDeLaVue(view: AppView): Capacite[] {
  const entrees = POINTS_ENTREE.filter(
    (p) => p.binding.registre === 'vue' && p.binding.view === view,
  ).map((p) => p.id);

  return CAPACITES.filter((c) => c.entrees.some((e) => entrees.includes(e)));
}

/** Les limites connues d'une capacité, à afficher plutôt qu'à taire. */
export function limitesDe(id: CapabilityId): string[] {
  return capacite(id)?.limites ?? [];
}
