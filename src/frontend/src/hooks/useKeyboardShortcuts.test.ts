/**
 * THERESE v2 - Keyboard Shortcuts Hook Tests
 *
 * Tests for US-CHAT-10: Keyboard navigation.
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { useKeyboardShortcuts } from './useKeyboardShortcuts';

describe('useKeyboardShortcuts', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  // Dans jsdom, navigator.platform n'est pas "MacIntel", donc le hook
  // utilise ctrlKey comme modificateur. On envoie les deux pour être sûr.
  const createKeyEvent = (
    key: string,
    modifiers: { meta?: boolean; ctrl?: boolean; shift?: boolean; alt?: boolean } = {}
  ): KeyboardEvent => {
    const useMod = modifiers.meta || modifiers.ctrl;
    return new KeyboardEvent('keydown', {
      key,
      metaKey: modifiers.meta ?? false,
      ctrlKey: useMod ?? false,
      shiftKey: modifiers.shift ?? false,
      altKey: modifiers.alt ?? false,
      bubbles: true,
    });
  };

  describe('Escape key', () => {
    it('should call onEscape when Escape pressed', () => {
      const onEscape = vi.fn();

      renderHook(() =>
        useKeyboardShortcuts({
          onEscape,
        })
      );

      // Dispatch event directly on document
      act(() => {
        window.dispatchEvent(createKeyEvent('Escape'));
      });

      expect(onEscape).toHaveBeenCalled();
    });
  });

  describe('Cmd+K - Command palette', () => {
    it('should call onCommandPalette when Cmd+K pressed', () => {
      const onCommandPalette = vi.fn();

      renderHook(() =>
        useKeyboardShortcuts({
          onCommandPalette,
        })
      );

      act(() => {
        window.dispatchEvent(createKeyEvent('k', { meta: true }));
      });

      expect(onCommandPalette).toHaveBeenCalled();
    });
  });

  describe('Cmd+N - New conversation', () => {
    it('should call onNewConversation when Cmd+N pressed', () => {
      const onNewConversation = vi.fn();

      renderHook(() =>
        useKeyboardShortcuts({
          onNewConversation,
        })
      );

      act(() => {
        window.dispatchEvent(createKeyEvent('n', { meta: true }));
      });

      expect(onNewConversation).toHaveBeenCalled();
    });
  });

  describe('Cmd+B - Toggle conversation sidebar', () => {
    it('should call onToggleConversationSidebar when Cmd+B pressed', () => {
      const onToggleConversationSidebar = vi.fn();

      renderHook(() =>
        useKeyboardShortcuts({
          onToggleConversationSidebar,
        })
      );

      act(() => {
        window.dispatchEvent(createKeyEvent('b', { meta: true }));
      });

      expect(onToggleConversationSidebar).toHaveBeenCalled();
    });
  });

  describe('Cmd+M - Toggle memory panel', () => {
    it('should call onToggleMemoryPanel when Cmd+M pressed', () => {
      const onToggleMemoryPanel = vi.fn();

      renderHook(() =>
        useKeyboardShortcuts({
          onToggleMemoryPanel,
        })
      );

      act(() => {
        window.dispatchEvent(createKeyEvent('m', { meta: true }));
      });

      expect(onToggleMemoryPanel).toHaveBeenCalled();
    });
  });

  describe('Cmd+D - Toggle board panel', () => {
    it('should call onToggleBoardPanel when Cmd+D pressed', () => {
      const onToggleBoardPanel = vi.fn();

      renderHook(() =>
        useKeyboardShortcuts({
          onToggleBoardPanel,
        })
      );

      act(() => {
        window.dispatchEvent(createKeyEvent('d', { meta: true }));
      });

      expect(onToggleBoardPanel).toHaveBeenCalled();
    });
  });

  describe('Cmd+/ - Show shortcuts', () => {
    it('should call onShowShortcuts when Cmd+/ pressed', () => {
      const onShowShortcuts = vi.fn();

      renderHook(() =>
        useKeyboardShortcuts({
          onShowShortcuts,
        })
      );

      act(() => {
        window.dispatchEvent(createKeyEvent('/', { meta: true }));
      });

      expect(onShowShortcuts).toHaveBeenCalled();
    });
  });

  describe('Event cleanup', () => {
    it('should remove event listeners on unmount', () => {
      const removeEventListenerSpy = vi.spyOn(window, 'removeEventListener');

      const { unmount } = renderHook(() =>
        useKeyboardShortcuts({
          onEscape: vi.fn(),
        })
      );

      unmount();

      expect(removeEventListenerSpy).toHaveBeenCalledWith(
        'keydown',
        expect.any(Function)
      );
    });
  });

  describe('Input focus handling', () => {
    it('should not trigger shortcuts when typing in input', () => {
      const onNewConversation = vi.fn();

      renderHook(() =>
        useKeyboardShortcuts({
          onNewConversation,
        })
      );

      // Create an input element and focus it
      const input = document.createElement('input');
      document.body.appendChild(input);
      input.focus();

      // Create event with input as target
      const event = new KeyboardEvent('keydown', {
        key: 'n',
        metaKey: true,
        bubbles: true,
      });
      Object.defineProperty(event, 'target', { value: input });

      act(() => {
        input.dispatchEvent(event);
      });

      // Should not be called because we're in an input
      expect(onNewConversation).not.toHaveBeenCalled();

      document.body.removeChild(input);
    });
  });
});
