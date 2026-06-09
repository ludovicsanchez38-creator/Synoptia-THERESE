/**
 * THÉRÈSE v2 - Registre d'actions (L8, revue produit)
 *
 * Source de vérité UNIQUE de « ce que l'app sait faire ». Trois portes d'entrée :
 *  1. ⌘K (la palette de commandes lit ce registre, au lieu de props codées en dur)
 *  2. Test / appel bas niveau : runAction('memory.open') déclenche la fonction + son UI
 *     sans passer par une conversation (suggestion Dr_logic).
 *  3. (futur) Thérèse scripte une séquence d'actions.
 *
 * Le registre est volontairement SANS JSX (pas d'icônes ici) pour rester invocable
 * hors React. La palette mappe id -> icône de son côté.
 */

import { useNavigationStore } from '../stores/navigationStore';
import { usePanelStore } from '../stores/panelStore';
import { useChatStore } from '../stores/chatStore';
import { useActionsStore } from '../stores/actionsStore';

export type ActionGroup = 'Chat' | 'Mémoire' | 'Navigation' | 'Réglages' | 'Actions';

export interface AppAction {
  id: string;
  label: string;
  description?: string;
  group: ActionGroup;
  /** Suffixe de raccourci (le mod ⌘/Ctrl est ajouté par l'UI). */
  shortcut?: string;
  /** Mots-clés supplémentaires pour la recherche dans la palette. */
  keywords?: string[];
  run: () => void;
}

/** Insère un prompt de départ dans le chat (correctif KO Syn 2.1 « Produire un document »). */
function insertChatPrompt(text: string): void {
  if (typeof window !== 'undefined') {
    window.dispatchEvent(new CustomEvent('therese:insert-prompt', { detail: text }));
  }
}

const nav = () => useNavigationStore.getState();
const panel = () => usePanelStore.getState();
const chat = () => useChatStore.getState();

export const APP_ACTIONS: AppAction[] = [
  // -- Chat --
  { id: 'chat.new', label: 'Nouvelle conversation', description: 'Démarrer une nouvelle conversation', group: 'Chat', shortcut: 'N', run: () => chat().createConversation() },
  { id: 'chat.clear', label: 'Effacer la conversation', description: 'Supprimer tous les messages', group: 'Chat', keywords: ['vider', 'reset'], run: () => chat().clearCurrentConversation() },
  { id: 'conversations.toggle', label: 'Conversations', description: 'Ouvrir la liste des conversations', group: 'Chat', shortcut: 'B', run: () => panel().toggleConversationSidebar() },
  { id: 'guided.open', label: 'Produire un document', description: 'Générer DOCX, PPTX ou XLSX (Skills Office)', group: 'Chat', keywords: ['docx', 'pptx', 'xlsx', 'office'], run: () => { nav().setView('chat'); insertChatPrompt('Aide-moi à produire un document (DOCX, PPTX ou XLSX) : '); } },
  { id: 'prompt-library.open', label: 'Bibliothèque de prompts', description: 'Modèles de prompts prêts à l\'emploi', group: 'Chat', keywords: ['modèles', 'templates'], run: () => panel().openPromptLibrary() },

  // -- Mémoire --
  { id: 'memory.open', label: 'Ouvrir la Mémoire', description: 'Contacts', group: 'Mémoire', shortcut: 'M', keywords: ['contacts'], run: () => nav().setView('memory') },
  { id: 'memory.search', label: 'Rechercher en mémoire', description: 'Chercher dans les contacts', group: 'Mémoire', shortcut: '⇧F', keywords: ['recherche', 'find'], run: () => nav().setView('memory') },
  { id: 'contact.new', label: 'Ajouter un contact', description: 'Créer un nouveau contact', group: 'Mémoire', keywords: ['nouveau contact'], run: () => panel().openNewContact() },
  { id: 'project.new', label: 'Ajouter un projet', description: 'Créer un nouveau projet', group: 'Mémoire', keywords: ['nouveau projet'], run: () => panel().openNewProject() },

  // -- Navigation (vues content-swap) --
  { id: 'home.open', label: 'Accueil', description: "Revenir à la page d'accueil", group: 'Navigation', shortcut: 'H', keywords: ['accueil', 'home', 'journée'], run: () => nav().setView('home') },
  { id: 'crm.open', label: 'Ouvrir le CRM', description: 'Pipeline commercial', group: 'Navigation', shortcut: 'P', keywords: ['pipeline', 'prospects'], run: () => nav().setView('crm') },
  { id: 'email.open', label: 'Ouvrir l\'Email', description: 'Boîte email', group: 'Navigation', shortcut: 'E', run: () => nav().setView('email') },
  { id: 'calendar.open', label: 'Ouvrir le Calendrier', description: 'Agenda', group: 'Navigation', shortcut: '⇧C', keywords: ['agenda', 'rdv'], run: () => nav().setView('calendar') },
  { id: 'tasks.open', label: 'Ouvrir les Tâches', description: 'Tâches et todos', group: 'Navigation', shortcut: 'T', keywords: ['todo'], run: () => nav().setView('tasks') },
  { id: 'invoices.open', label: 'Ouvrir les Factures', description: 'Factures et devis', group: 'Navigation', shortcut: 'I', keywords: ['devis'], run: () => nav().setView('invoices') },
  { id: 'projects.open', label: 'Ouvrir les Projets', description: 'Vos projets et leur avancement (kanban par statut)', group: 'Navigation', keywords: ['projets', 'kanban', 'avancement'], run: () => nav().setView('projects') },
  { id: 'files.open', label: 'Indexation des fichiers', description: 'Parcourir et indexer des fichiers locaux', group: 'Navigation', keywords: ['fichiers', 'indexation', 'documents'], run: () => nav().setView('files') },
  { id: 'board.open', label: 'Board de décision', description: 'Convoquer le board de conseillers IA', group: 'Navigation', shortcut: 'D', run: () => panel().toggleBoardPanel() },
  { id: 'actions.open', label: 'Actions', description: 'Lancer un agent actionnable (rapport, relance, audit...)', group: 'Actions', run: () => useActionsStore.getState().openPanel() },

  // -- Réglages --
  { id: 'data.export', label: 'Exporter les données', description: 'Sauvegarder ta mémoire (via Réglages)', group: 'Réglages', keywords: ['backup', 'sauvegarde'], run: () => panel().openSettings() },
  { id: 'settings.open', label: 'Paramètres', description: 'Configurer THÉRÈSE', group: 'Réglages', shortcut: ',', run: () => panel().openSettings() },
  { id: 'shortcuts.open', label: 'Raccourcis clavier', description: 'Voir tous les raccourcis', group: 'Réglages', shortcut: '/', run: () => panel().openShortcuts() },
];

/** Liste des actions disponibles (pour la palette ⌘K). */
export function getActions(): AppAction[] {
  return APP_ACTIONS;
}

/** Déclenche une action par son id. Retourne false si l'id est inconnu (sans planter). */
export function runAction(id: string): boolean {
  const action = APP_ACTIONS.find((a) => a.id === id);
  if (!action) return false;
  action.run();
  return true;
}
