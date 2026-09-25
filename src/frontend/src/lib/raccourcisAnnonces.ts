/**
 * Raccourcis clavier annoncés à l'utilisateur : une seule table pour la
 * fenêtre des raccourcis (⌘/) et la liste de Paramètres > Accessibilité.
 *
 * B-1376 (persona Hugo, cycle 13) : les deux listes divergeaient (⌘M
 * « Mémoire » d'un côté, « Contacts » de l'autre et à l'écran) et aucune ne
 * disait que la plupart des raccourcis sont ignorés dans un champ de saisie.
 */

export interface Raccourci {
  keys: string;
  description: string;
  /** B-1376 : actif aussi quand le curseur est dans un champ de saisie. Le
   *  gestionnaire ignore les autres dans un champ (une frappe ne doit pas
   *  changer d'écran) ; la fenêtre et Paramètres le disent. */
  pendantLaSaisie?: true;
}

export interface ShortcutGroup {
  title: string;
  shortcuts: Raccourci[];
}

/** Exporté pour que le test de véracité puisse confronter chaque raccourci
 *  annoncé au gestionnaire de clavier. Une fiche d'aide qui ment est pire que
 *  pas de fiche : l'utilisateur essaie, rien ne se passe, il conclut que
 *  l'application est cassée. */
export const SHORTCUT_GROUPS: ShortcutGroup[] = [
  {
    title: 'Chat',
    shortcuts: [
      { keys: '↵', description: 'Envoyer le message' },
      { keys: '⇧ + ↵', description: 'Nouvelle ligne' },
      { keys: '⌘ + N', description: 'Nouvelle conversation', pendantLaSaisie: true },
    ],
  },
  {
    title: 'Navigation',
    shortcuts: [
      { keys: '⌘ + K', description: 'Palette de commandes', pendantLaSaisie: true },
      { keys: '⌘ + /', description: 'Raccourcis clavier', pendantLaSaisie: true },
      { keys: '⌘ + B', description: 'Liste des conversations' },
      { keys: '⌘ + M', description: 'Contacts' },
      { keys: '⌘ + ,', description: 'Paramètres', pendantLaSaisie: true },
      { keys: 'Échap', description: 'Fermer le panneau actif' },
    ],
  },
  {
    title: 'Fonctions principales',
    shortcuts: [
      { keys: '⌘ + D', description: 'Décision' },
      { keys: '⌘ + E', description: 'Email (Gmail)' },
      { keys: '⌘ + T', description: 'Tâches (Kanban)' },
      { keys: '⌘ + I', description: 'Devis et factures' },
      { keys: '⌘ + P', description: 'Pipeline' },
    ],
  },
  {
    title: 'Outils',
    shortcuts: [
      { keys: '⌘ + ⇧ + A', description: 'Améliorer THÉRÈSE' },
      // P-095 : nommer par ce que fait le raccourci, pas par le prénom interne de l'agent.
      { keys: '⌘ + ⇧ + K', description: 'Écrire à l’agent de l’Atelier', pendantLaSaisie: true },
      { keys: '⌘ + ⇧ + C', description: 'Agenda' },
      { keys: '⌘ + ⇧ + F', description: 'Rechercher dans les Contacts' },
      { keys: '⌘ + ⇧ + D', description: 'Mode démonstration' },
    ],
  },
  {
    title: 'Fichiers',
    shortcuts: [
      // Entrée 6 : ce groupe était déclaré VIDE, et le raccourci qu'il aurait
      // dû annoncer n'était branché nulle part. Les deux se répondaient.
      { keys: '⌘ + O', description: 'Ouvrir les Fichiers' },
    ],
  },
];

const tousLesRaccourcis = SHORTCUT_GROUPS.flatMap((g) => g.shortcuts);

/** Les raccourcis qui marchent aussi pendant la saisie, dans l'ordre de la fiche. */
export const RACCOURCIS_PENDANT_LA_SAISIE: string[] = tousLesRaccourcis
  .filter((s) => s.pendantLaSaisie)
  .map((s) => s.keys);

/** Le nom d'un raccourci tel que la fiche l'annonce. */
export function descriptionDuRaccourci(keys: string): string {
  const trouve = tousLesRaccourcis.find((s) => s.keys === keys);
  if (!trouve) throw new Error(`Raccourci non annoncé : ${keys}`);
  return trouve.description;
}
