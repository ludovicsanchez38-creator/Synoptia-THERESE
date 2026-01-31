import { useEffect, useCallback } from 'react';

interface ShortcutHandlers {
  onCommandPalette?: () => void;
  onNewConversation?: () => void;
  onShowShortcuts?: () => void;
  onToggleMemoryPanel?: () => void;
  onToggleConversationSidebar?: () => void;
  onToggleBoardPanel?: () => void;
  onToggleEmailPanel?: () => void;
  onToggleCalendarPanel?: () => void;
  onToggleTasksPanel?: () => void;
  onToggleInvoicesPanel?: () => void;
  onToggleCRMPanel?: () => void;
  onNewContact?: () => void;
  onNewProject?: () => void;
  onOpenSettings?: () => void;
  onSearch?: () => void;
  onOpenFile?: () => void;
  onEscape?: () => void;
}

/**
 * Hook for handling global keyboard shortcuts.
 *
 * Uses Cmd (Mac) / Ctrl (Windows/Linux) as modifier.
 */
export function useKeyboardShortcuts(handlers: ShortcutHandlers) {
  const handleKeyDown = useCallback(
    (event: KeyboardEvent) => {
      // Determine the correct modifier key
      const isMac = navigator.platform.toUpperCase().indexOf('MAC') >= 0;
      const modKey = isMac ? event.metaKey : event.ctrlKey;
      const key = event.key.toLowerCase();

      // Don't trigger shortcuts when typing in inputs (except specific ones)
      const target = event.target as HTMLElement;
      const isInput =
        target.tagName === 'INPUT' ||
        target.tagName === 'TEXTAREA' ||
        target.isContentEditable;

      // Escape always works
      if (key === 'escape') {
        handlers.onEscape?.();
        return;
      }

      // These shortcuts only work with modifier key
      if (!modKey) return;

      // Cmd+K - Command palette (works even in inputs)
      if (key === 'k') {
        event.preventDefault();
        handlers.onCommandPalette?.();
        return;
      }

      // Cmd+/ - Show shortcuts (works even in inputs)
      if (event.key === '/') {
        event.preventDefault();
        handlers.onShowShortcuts?.();
        return;
      }

      // Skip other shortcuts when in inputs
      if (isInput) return;

      // --- Shift combos first (before non-shift) ---

      // Cmd+Shift+C - Calendar panel
      if (key === 'c' && event.shiftKey) {
        event.preventDefault();
        handlers.onToggleCalendarPanel?.();
        return;
      }

      // Cmd+Shift+F - Search memory
      if (key === 'f' && event.shiftKey) {
        event.preventDefault();
        handlers.onSearch?.();
        return;
      }

      // --- Non-shift combos ---

      // Cmd+N - New conversation
      if (key === 'n' && !event.shiftKey) {
        event.preventDefault();
        handlers.onNewConversation?.();
        return;
      }

      // Cmd+M - Toggle memory panel
      if (key === 'm') {
        event.preventDefault();
        handlers.onToggleMemoryPanel?.();
        return;
      }

      // Cmd+B - Toggle conversation sidebar
      if (key === 'b') {
        event.preventDefault();
        handlers.onToggleConversationSidebar?.();
        return;
      }

      // Cmd+D - Toggle board panel
      if (key === 'd' && !event.shiftKey) {
        event.preventDefault();
        handlers.onToggleBoardPanel?.();
        return;
      }

      // Cmd+E - Toggle email panel
      if (key === 'e' && !event.shiftKey) {
        event.preventDefault();
        handlers.onToggleEmailPanel?.();
        return;
      }

      // Cmd+T - Toggle tasks panel
      if (key === 't' && !event.shiftKey) {
        event.preventDefault();
        handlers.onToggleTasksPanel?.();
        return;
      }

      // Cmd+I - Toggle invoices panel
      if (key === 'i' && !event.shiftKey) {
        event.preventDefault();
        handlers.onToggleInvoicesPanel?.();
        return;
      }

      // Cmd+P - Toggle CRM pipeline
      if (key === 'p' && !event.shiftKey) {
        event.preventDefault();
        handlers.onToggleCRMPanel?.();
        return;
      }

      // Cmd+, - Settings
      if (event.key === ',') {
        event.preventDefault();
        handlers.onOpenSettings?.();
        return;
      }

      // Cmd+O - Open file
      if (key === 'o' && !event.shiftKey) {
        event.preventDefault();
        handlers.onOpenFile?.();
        return;
      }
    },
    [handlers]
  );

  useEffect(() => {
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [handleKeyDown]);
}
