/**
 * P-148, lot 4 : ce que la suppression d'un projet emporte, dit avant de
 * confirmer. Les totaux viennent de la route d'ensemble, qui lit les mêmes
 * clauses que la suppression (`projet_ensemble.py`) : le compte annoncé est
 * le compte exécuté.
 *
 * Une famille à zéro est omise. Une famille illisible (`null`) fait renoncer
 * à toute la phrase : mieux vaut la mise en garde générale qu'un « 0 tâche »
 * inventé, ou qu'une liste qui tairait ce qu'elle n'a pas pu lire.
 */
import type { EnsembleDuProjet } from '../services/api';

function compte(n: number, singulier: string, pluriel: string): string {
  return `${n} ${n > 1 ? pluriel : singulier}`;
}

function enumerer(parties: string[]): string {
  if (parties.length <= 1) return parties.join('');
  return `${parties.slice(0, -1).join(', ')} et ${parties[parties.length - 1]}`;
}

/** Les phrases qui disent les conséquences, ou `null` si une famille manque. */
export function consequencesDeLaSuppression(ensemble: EnsembleDuProjet): string[] | null {
  const {
    taches, livrables, fichiers, dossier_synchronise, planning, conversations, documents, rendez_vous, contacts,
    sous_dossiers,
  } = ensemble;
  if (
    !taches || !livrables || !fichiers || !dossier_synchronise || !planning || !conversations || !documents
    || !rendez_vous || !contacts || !sous_dossiers
  ) {
    return null;
  }
  const phrases: string[] = [];

  const emportes = [
    taches.total > 0 ? compte(taches.total, 'tâche', 'tâches') : '',
    livrables.total > 0 ? compte(livrables.total, 'livrable', 'livrables') : '',
    // Revue P-148, constat 3 : seul le dépôt de THÉRÈSE part du disque.
    fichiers.deposes > 0 ? compte(fichiers.deposes, 'fichier déposé dans THÉRÈSE', 'fichiers déposés dans THÉRÈSE') : '',
    // Revue P-148, constat 6 : les ressources déclarées sont des données
    // saisies, pas un calcul ; elles se nomment à part.
    planning.ressources > 0
      ? compte(planning.ressources, 'ressource de planning déclarée', 'ressources de planning déclarées')
      : '',
    planning.calculs > 0 ? 'son planning calculé' : '',
  ].filter(Boolean);
  if (emportes.length > 0) phrases.push(`La suppression emporte ${enumerer(emportes)}.`);

  // Les fichiers indexés depuis le dossier synchronisé quittent l'index de
  // THÉRÈSE, mais la suppression ne touche pas à leur disque
  // (`_purger_le_depot_du_dossier`).
  if (fichiers.indexes_sur_place > 0) {
    phrases.push(fichiers.indexes_sur_place > 1
      ? `${fichiers.indexes_sur_place} fichiers indexés depuis ton disque sortent de l’index ; ils restent sur ton disque.`
      : '1 fichier indexé depuis ton disque sort de l’index ; il reste sur ton disque.');
  }
  if (dossier_synchronise.rattache) {
    phrases.push('Le dossier synchronisé est détaché du projet ; il reste sur ton disque.');
  }

  const detaches = [
    conversations.total > 0 ? compte(conversations.total, 'conversation', 'conversations') : '',
    documents.total > 0 ? compte(documents.total, 'document', 'documents') : '',
    rendez_vous.total > 0 ? compte(rendez_vous.total, 'rendez-vous', 'rendez-vous') : '',
  ].filter(Boolean);
  const nombreDetaches = conversations.total + documents.total + rendez_vous.total;
  if (detaches.length > 0) {
    phrases.push(`${enumerer(detaches)} ${nombreDetaches > 1 ? 'restent' : 'reste'}, sans lien avec le projet.`);
  }
  if (conversations.total > 0) {
    // memory.py : la conversation détachée repasse en périmètre « global ».
    phrases.push(conversations.total > 1
      ? 'Ces conversations ne liront plus que les documents généraux.'
      : 'Cette conversation ne lira plus que les documents généraux.');
  }

  const ranges = [
    contacts.ranges > 0 ? compte(contacts.ranges, 'contact', 'contacts') : '',
    sous_dossiers.total > 0 ? compte(sous_dossiers.total, 'sous-projet', 'sous-projets') : '',
  ].filter(Boolean);
  const nombreRanges = contacts.ranges + sous_dossiers.total;
  if (ranges.length > 0) {
    // B-1503 : ils repassent au périmètre général (« Global » dans Contacts).
    phrases.push(nombreRanges > 1
      ? `${enumerer(ranges)} rangés dans ce projet passent en Global, visibles dans toutes les conversations.`
      : `${enumerer(ranges)} rangé dans ce projet passe en Global, visible dans toutes les conversations.`);
  }
  return phrases;
}
