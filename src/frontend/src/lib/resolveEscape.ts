/**
 * THÉRÈSE v2 - Pile Échap/retour unifiée (L7, revue produit)
 *
 * UNE seule autorité pour la touche Échap, en remplacement des piles concurrentes
 * (panelStore.handleEscape + écouteurs par composant + rien pour les vues).
 *
 * Priorité (du plus en avant au plus en arrière) :
 *  1. Overlays modaux (z-order) : save command, contact, projet, board, ⌘K, raccourcis, réglages
 *  2. Panneaux latéraux : Atelier, Actions (Échap ne les fermait pas avant)
 *  3. Retour de vue : si on est sur une vue content-swap, revenir en arrière (coeur de L7)
 *  4. Dernier recours : fermer la sidebar Conversations
 */

import { usePanelStore } from '../stores/panelStore';
import { useAtelierStore } from '../stores/atelierStore';
import { useActionsStore } from '../stores/actionsStore';
import { useNavigationStore } from '../stores/navigationStore';

export function resolveEscape(): void {
  const ps = usePanelStore.getState();

  // 1. Overlays modaux, du plus en avant au moins en avant.
  if (ps.showSaveCommand) return ps.closeSaveCommand();
  if (ps.showContactModal) return ps.closeContactModal();
  if (ps.showProjectModal) return ps.closeProjectModal();
  if (ps.showBoardPanel) return ps.closeBoardPanel();
  if (ps.showCommandPalette) return ps.closeCommandPalette();
  if (ps.showShortcuts) return ps.closeShortcuts();
  if (ps.showSettings) return ps.closeSettings();

  // 2. Panneaux latéraux.
  if (useAtelierStore.getState().isOpen) return useAtelierStore.getState().closePanel();
  if (useActionsStore.getState().isPanelOpen) return useActionsStore.getState().closePanel();

  // 3. Retour de vue (le manque que L7 comble).
  if (useNavigationStore.getState().activeView !== 'chat') {
    return useNavigationStore.getState().goBack();
  }

  // 4. Dernier recours : sidebar Conversations.
  if (ps.showConversationSidebar) return ps.closeConversationSidebar();
}
