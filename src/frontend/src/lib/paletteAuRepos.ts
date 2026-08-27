/**
 * Ce que la palette propose quand personne n'a encore tapé.
 *
 * Elle rendait une liste vide : il fallait deviner le mot exact pour
 * découvrir qu'« Ouvrir les Projets » ou « Exporter les données » existent.
 *
 * La curation compte autant que l'affichage. Les parcours de l'établi et les
 * capacités fréquentes sont déjà listés au-dessus dans la même palette : y
 * répéter leurs destinations ferait douter qu'il s'agisse des mêmes, et
 * recréerait le mur que le chantier de simplification a voulu abattre.
 */
export interface ActionProposable {
  id: string;
  label: string;
}

/* Générique : l'appelant récupère ses actions ENTIÈRES, avec leur description
   et leur raccourci. Un type de retour plus étroit les raboterait, et la
   palette perdrait ce qu'elle affiche. */

/**
 * Au repos, la palette suggère, elle ne déverse pas.
 *
 * Huit et non six : après curation, « Ouvrir les Projets » et « Ouvrir les
 * Fichiers » tombent aux septième et huitième rangs de l'ordre de
 * déclaration. Six les auraient coupées, alors que ce sont deux destinations
 * majeures — et que le raccourci des Fichiers vient d'être câblé. Huit reste
 * une suggestion, pas le mur que la simplification a voulu abattre.
 */
const PLAFOND_AU_REPOS = 8;

/**
 * Ce que le rail et l'établi portent déjà, ou ce qui n'est pas une
 * destination à découvrir.
 *
 * La relecture l'a montré sur le registre RÉEL : sans cette liste, l'ordre de
 * déclaration remplissait les six places avec « Nouvelle conversation »,
 * « Effacer la conversation » et « Conversations » — deux boutons du rail et
 * une action destructrice — pendant que « Ouvrir les Projets » et « Ouvrir
 * les Fichiers » tombaient au onzième rang. Mes exemples de test, eux,
 * plaçaient les bonnes réponses en tête : un test qui invente ses données
 * valide son invention.
 */
const DEJA_PORTEES = new Set([
  'chat.new', // le + du rail
  'conversations.toggle', // le bouton Conversations du rail
  'chat.clear', // détruit, ne mène nulle part : rien à découvrir ici
]);

/**
 * Les actions qu'aucune autre section de la palette n'annonce déjà.
 *
 * `parcours` : les identifiants de l'établi (« email », « invoice »…).
 * `capacites` : les identifiants des capacités déjà affichées.
 */
export function actionsAuRepos<T extends ActionProposable>(
  actions: readonly T[],
  parcours: readonly string[],
  capacites: readonly string[],
): T[] {
  const deja = new Set<string>([
    ...parcours,
    ...capacites,
    // L'accueil : on y est déjà quand la palette s'ouvre depuis la coque.
    'home',
  ]);
  return actions
    .filter((action) => !DEJA_PORTEES.has(action.id))
    .filter((action) => {
      const domaine = action.id.split('.')[0];
      // `invoices.open` mène au parcours « invoice » : on compare sur la
      // racine du domaine, singulier ou pluriel.
      const racine = domaine.replace(/s$/, '');
      return !deja.has(domaine) && !deja.has(racine);
    })
    .slice(0, PLAFOND_AU_REPOS);
}
