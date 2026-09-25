/**
 * P-142 (persona Zoé, cycle 13) : après un rechargement, l'application
 * revenait toujours à l'Accueil. L'écran quitté est gardé pour la session :
 * `sessionStorage` survit au rechargement de la fenêtre, pas à la fermeture
 * de l'application (un nouveau lancement repart de l'Accueil).
 *
 * Commodité par fenêtre : toute lecture ou écriture peut échouer (stockage
 * bloqué) sans rien casser.
 */
import { APP_VIEWS, type AppView } from '../stores/navigationStore';

const CLE_VUE = 'therese:vue-quittee';

// Le chat n'est pas un écran à rouvrir : il suit la conversation courante.
const RESTAURABLES = new Set<AppView>(APP_VIEWS.filter((vue) => vue !== 'chat'));

export function lireLaVueQuittee(): AppView | null {
  try {
    const vue = sessionStorage.getItem(CLE_VUE) as AppView | null;
    return vue && RESTAURABLES.has(vue) ? vue : null;
  } catch {
    return null;
  }
}

export function memoriserLaVue(vue: AppView | null): void {
  try {
    if (vue && RESTAURABLES.has(vue)) sessionStorage.setItem(CLE_VUE, vue);
    else sessionStorage.removeItem(CLE_VUE);
  } catch {
    /* stockage indisponible : l'écran ne sera simplement pas repris */
  }
}

/** Un lien profond dit où aller : il l'emporte sur l'écran quitté. */
export function lienProfondPresent(search: string): boolean {
  const parametres = new URLSearchParams(search);
  return ['view', 'panel', 'action', 'scenario', 'settings_tab', 'prompt'].some((cle) => parametres.has(cle));
}

const CLE_DOCUMENT = 'therese:document-quitte';

/** P-142 : le document ouvert dans l'atelier, même règle que la vue. */
export function lireLeDocumentQuitte(): string | null {
  try {
    return sessionStorage.getItem(CLE_DOCUMENT) || null;
  } catch {
    return null;
  }
}

export function memoriserLeDocument(id: string | null): void {
  try {
    if (id) sessionStorage.setItem(CLE_DOCUMENT, id);
    else sessionStorage.removeItem(CLE_DOCUMENT);
  } catch {
    /* stockage indisponible */
  }
}
