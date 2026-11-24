const phases = {
  alpha: { libelle: 'Alpha', suffixe: '-alpha' },
  beta: { libelle: 'Bêta', suffixe: '-beta' },
  stable: { libelle: 'Stable', suffixe: '' },
} as const;

export const PHASE_APPLICATION = phases.beta;
export const PAGE_TELECHARGEMENT = 'https://synoptia.fr/therese/beta/';
