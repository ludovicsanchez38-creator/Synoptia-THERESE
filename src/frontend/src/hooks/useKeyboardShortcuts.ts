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

      // Don't trigger shortcuts when typing in inputs (except specific ones)
      const target = event.target as HTMLElement;
      const isInput =
        target.tagName === 'INPUT' ||
        target.tagName === 'TEXTAREA' ||
        target.isContentEditable;

      // Escape always works
      if (event.key === 'Escape') {
        handlers.onEscape?.();
        return;
      }

      // These shortcuts only work with modifier key
      if (!modKey) return;

      // Cmd+K - Command palette (works even in inputs)
      if (event.key === 'k') {
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

      // Cmd+N - New conversation
      if (event.key === 'n' && !event.shiftKey) {
        event.preventDefault();
        handlers.onNewConversation?.();
        return;
      }

      // Cmd+M - Toggle memory panel
      if (event.key === 'm') {
        event.preventDefault();
        handlers.onToggleMemoryPanel?.();
        return;
      }

      // Cmd+B - Toggle conversation sidebar
      if (event.key === 'b') {
        event.preventDefault();
        handlers.onToggleConversationSidebar?.();
        return;
      }

      // Cmd+D - Toggle board panel
      if (event.key === 'd' && !event.shiftKey) {
        event.preventDefault();
        handlers.onToggleBoardPanel?.();
        return;
      }

      // Cmd+E - Toggle email panel
      if (event.key === 'e' && !event.shiftKey) {
        event.preventDefault();
        handlers.onToggleEmailPanel?.();
        return;
      }

      // Cmd+T - Toggle tasks panel
      if (event.key === 't' && !event.shiftKey) {
        event.preventDefault();
        handlers.onToggleTasksPanel?.();
        return;
      }

      // Cmd+I - Toggle invoices panel
      if (event.key === 'i' && !event.shiftKey) {
        event.preventDefault();
        handlers.onToggleInvoicesPanel?.();
        return;
      }

      // Cmd+P - Toggle CRM pipeline
      if (event.key === 'p' && !event.shiftKey) {
        event.preventDefault();
        handlers.onToggleCRMPanel?.();
        return;
      }

      // Cmd+Shift+C - Calendar panel
      if (event.key === 'c' && event.shiftKey) {
        event.preventDefault();
        handlers.onToggleCalendarPanel?.();
        return;
      }

      // Cmd+Shift+P - New project
      if (event.key === 'p' && event.shiftKey) {
        event.preventDefault();
        handlers.onNewProject?.();
        return;
      }

      // Cmd+Shift+F - Search memory
      if (event.key === 'f' && event.shiftKey) {
        event.preventDefault();
        handlers.onSearch?.();
        return;
      }

      // Cmd+O - Open file
      if (event.key === 'o' && !event.shiftKey) {
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
