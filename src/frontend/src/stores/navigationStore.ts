/**
 * THÉRÈSE v2 - Navigation Store (Phase 1 revue produit)
 *
 * Modèle "content-swap par vues" : la zone principale rend la VUE active.
 * Les surfaces de productivité (CRM, Email, Agenda, Tâches, Factures, Mémoire)
 * deviennent des vues, au lieu de fenêtres Tauri séparées.
 */

import { create } from 'zustand';
import { usePersonalisationStore } from './personalisationStore';

/**
 * La liste des vues, en CONSTANTE plutôt qu'en union de types (0.44).
 *
 * Une union TypeScript disparaît à la compilation : aucun test ne peut vérifier
 * qu'une vue est décrite quelque part, ni qu'un catalogue la couvre. L'inventaire
 * du 13/08 a montré le prix de cette invisibilité — la même liste redéclarée à
 * sept endroits, et `files` oubliée dans la table du backend, ce qui rendait la
 * vue de l'indexation introuvable par `{action: ouvrir …}` comme par `/aide`.
 *
 * Le type est désormais DÉRIVÉ de la constante : ajouter une vue au type sans
 * l'ajouter ici devient impossible.
 */
export const APP_VIEWS = [
  'chat',
  'memory',
  'crm',
  'email',
  'calendar',
  'tasks',
  'invoices',
  'files', // Indexation de fichiers (sortie de la Mémoire, arbitrage A/B 2026-06-05)
  'projects', // Vue Projets dédiée (BUG-104 : surface perdue à la refonte 0.20)
  'documents', // Atelier documentaire : liste + création (D2), atelier de rédaction (D3)
] as const;

export type AppView = (typeof APP_VIEWS)[number];

interface NavigationStore {
  /**
   * La vue embarquée affichée, ou `null` quand il n'y en a AUCUNE — c'est
   * l'accueil conversationnel de la coque qui occupe alors l'écran.
   *
   * Ce `null` est le correctif du 27/08/2026. Le store démarrait sur `'home'`,
   * l'ancien tableau de bord embarqué, que plus rien n'affiche au lancement :
   * la coque a son propre accueil et un commentaire l'y rappelle déjà (« ne
   * pas appeler `initializeView`, qui poserait la vue 'home' et écraserait
   * l'accueil conversationnel natif »). La pile mentait donc DÈS L'OUVERTURE :
   * ouvrir une vue empilait `'home'`, et « Retour » ramenait sur un écran où
   * l'utilisateur n'était jamais allé — il fallait deux ou trois gestes pour
   * revenir vraiment. « Aucune vue » est un état réel : il lui fallait un nom.
   */
  activeView: AppView | null;
  /** Pile des vues précédentes (pour le retour / Échap). */
  history: AppView[];
  setView: (view: AppView) => void;
  /**
   * Revenir à l'accueil de la coque.
   *
   * Signalé par Ludo le 28/08 : aucun chemin nommé n'y ramenait. On ne pouvait
   * que FERMER ce qu'on avait ouvert, ce qui suppose de savoir ce qu'on a
   * ouvert — et l'action qui s'appelait « Accueil » menait à un second écran
   * d'accueil, celui qu'on cherche justement à retirer.
   *
   * L'accueil est la racine : la pile se vide, on ne « revient » pas d'un
   * accueil vers un écran précédent.
   */
  retourAccueil: () => void;
  goBack: () => void;
  resetToChat: () => void;
  /** Initialise la vue selon les préférences utilisateur */
  initializeView: () => void;
}

export const useNavigationStore = create<NavigationStore>((set) => ({
  activeView: null, // aucune vue embarquée : la coque montre son accueil
  history: [],

  setView: (view) =>
    set((state) => {
      if (view === state.activeView) return state; // no-op : pas de doublon
      return {
        activeView: view,
        // On n'empile que des vues RÉELLES. Venir de l'accueil n'empile rien :
        // sinon le retour ramènerait vers un écran jamais visité.
        history: state.activeView === null
          ? state.history
          : [...state.history, state.activeView],
      };
    }),


  retourAccueil: () => set({ activeView: null, history: [] }),
  goBack: () =>
    set((state) => {
      if (state.history.length === 0) {
        // Pile vide = on retourne à l'accueil, pas au chat. Ouvrir le chat
        // ici était le deuxième geste parasite du parcours de retour.
        return { activeView: null, history: [] };
      }
      const history = [...state.history];
      const previous = history.pop() as AppView;
      return { activeView: previous, history };
    }),

  resetToChat: () => set({ activeView: 'chat', history: [] }),

  initializeView: () => {
    const skipDashboard = usePersonalisationStore.getState().skipDashboard ?? false;
    // `null` et non `'home'` : voir le commentaire d'`activeView`. La coque
    // n'appelait plus cette fonction PARCE QU'elle posait la mauvaise vue.
    set({
      activeView: skipDashboard ? 'chat' : null,
      history: [],
    });
  },
}));
