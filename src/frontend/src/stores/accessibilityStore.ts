/**
 * THERESE v2 - Accessibility Store
 *
 * Store for managing accessibility preferences.
 * US-A11Y-04: Disable animations preference
 */

import { create } from 'zustand';
import { persist } from 'zustand/middleware';

interface AccessibilityState {
  // Animation preferences (US-A11Y-04)
  reduceMotion: boolean;
  setReduceMotion: (reduce: boolean) => void;

  // Font size preferences
  fontSize: 'small' | 'medium' | 'large';
  setFontSize: (size: 'small' | 'medium' | 'large') => void;

  // High contrast mode
  highContrast: boolean;
  setHighContrast: (enabled: boolean) => void;

  // Screen reader announcements
  announceMessages: boolean;
  setAnnounceMessages: (enabled: boolean) => void;

  // Keyboard navigation hints
  showKeyboardHints: boolean;
  setShowKeyboardHints: (show: boolean) => void;
}

export const useAccessibilityStore = create<AccessibilityState>()(
  persist(
    (set) => ({
      // Default to system preference for reduced motion
      reduceMotion:
        typeof window !== 'undefined'
          ? window.matchMedia('(prefers-reduced-motion: reduce)').matches
          : false,
      setReduceMotion: (reduce) => set({ reduceMotion: reduce }),

      fontSize: 'medium',
      setFontSize: (size) => set({ fontSize: size }),

      highContrast: false,
      setHighContrast: (enabled) => set({ highContrast: enabled }),

      announceMessages: true,
      setAnnounceMessages: (enabled) => set({ announceMessages: enabled }),

      showKeyboardHints: true,
      setShowKeyboardHints: (show) => set({ showKeyboardHints: show }),
    }),
    {
      name: 'therese-accessibility',
    }
  )
);

/**
 * Hook to check if animations should be reduced.
 * Combines user preference with system preference.
 */
export function useReducedMotion(): boolean {
  const userPreference = useAccessibilityStore((state) => state.reduceMotion);

  // Also check system preference
  if (typeof window !== 'undefined') {
    const systemPreference = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    return userPreference || systemPreference;
  }

  return userPreference;
}

/**
 * Get font size CSS value based on preference.
 */
export function useFontSize(): string {
  const fontSize = useAccessibilityStore((state) => state.fontSize);

  switch (fontSize) {
    case 'small':
      return '14px';
    case 'large':
      return '18px';
    default:
      return '16px';
  }
}
