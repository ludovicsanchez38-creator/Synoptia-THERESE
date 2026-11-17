/**
 * THERESE v2 - Z-Index Layer System
 *
 * Hierarchie standardisee pour eviter les conflits z-index.
 * Utiliser ces constantes au lieu de valeurs en dur.
 */
export const Z_LAYER = {
  /** Elements internes : badges, indicateurs, overlays relatifs */
  INTERNAL: 'z-10',
  /** Menus contextuels, dropdowns, tooltips */
  DROPDOWN: 'z-20',
  /** Sidebars et panels coulissants */
  SIDEBAR: 'z-30',
  /** Backdrops des modaux (overlay sombre) */
  BACKDROP: 'z-40',
  /** Modaux principaux (DialogShell, Settings, Email, Calendar, Board, CRM) */
  MODAL: 'z-50',
  /** Modaux secondaires (modale dans modale) */
  MODAL_NESTED: 'z-[60]',
  /** Setup wizards, notifications actionables */
  WIZARD: 'z-[70]',
  /** Command palette */
  COMMAND_PALETTE: 'z-[80]',
  /** Toasts / notifications passives */
  TOAST: 'z-[90]',
  /** Onboarding uniquement */
  ONBOARDING: 'z-[100]',
  /** Onboarding header */
  ONBOARDING_TOP: 'z-[101]',
} as const;

export type ZLayer = typeof Z_LAYER[keyof typeof Z_LAYER];
