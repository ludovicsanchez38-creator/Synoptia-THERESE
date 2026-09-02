/**
 * Repli d'une chaîne pour la recherche : casse ET diacritiques.
 *
 * B-211 (02/09/2026) : la palette ⌘K repliait la casse par `toLowerCase()` et
 * s'arrêtait là. Dans une application française, « tache » ne trouvait donc
 * pas « Tâches ». Le backend replie les deux depuis le catalogue documentaire
 * (memory_tools.py, legal_corpus.py, chat_actions.py) ; le frontend n'avait
 * aucun helper équivalent.
 *
 * NFD sépare la lettre de son signe, `\p{Mn}` retire les marques combinantes
 * ainsi dégagées. À appliquer des DEUX côtés de la comparaison : replier la
 * seule requête laisserait « tache » sans réponse face à « Tâches ».
 */
export function replierPourRecherche(texte: string): string {
  return texte.normalize('NFD').replace(/\p{Mn}/gu, '').toLowerCase();
}
