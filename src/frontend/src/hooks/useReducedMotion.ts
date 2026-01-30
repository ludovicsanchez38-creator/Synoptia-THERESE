/**
 * THÉRÈSE v2 - Reduced Motion Hook
 *
 * Respects user's motion preferences for accessibility.
 */

import { useState, useEffect } from 'react';

/**
 * Hook to detect if user prefers reduced motion
 *
 * Returns true if the user has enabled reduced motion in their OS settings.
 * Use this to disable or simplify animations for accessibility.
 *
 * @example
 * const prefersReducedMotion = useReducedMotion();
 * const animation = prefersReducedMotion ? {} : fadeInUp;
 */
export function useReducedMotion(): boolean {
  const [prefersReducedMotion, setPrefersReducedMotion] = useState(false);

  useEffect(() => {
    // Check if matchMedia is available (SSR safety)
    if (typeof window === 'undefined' || !window.matchMedia) {
      return;
    }

    const mediaQuery = window.matchMedia('(prefers-reduced-motion: reduce)');

    // Set initial value
    setPrefersReducedMotion(mediaQuery.matches);

    // Listen for changes
    const handleChange = (event: MediaQueryListEvent) => {
      setPrefersReducedMotion(event.matches);
    };

    // Modern browsers
    if (mediaQuery.addEventListener) {
      mediaQuery.addEventListener('change', handleChange);
      return () => mediaQuery.removeEventListener('change', handleChange);
    }

    // Fallback for older browsers
    mediaQuery.addListener(handleChange);
    return () => mediaQuery.removeListener(handleChange);
  }, []);

  return prefersReducedMotion;
}

/**
 * Helper to get animation variants based on reduced motion preference
 *
 * @example
 * const variants = getMotionVariants(prefersReducedMotion, fadeInUp, fadeIn);
 */
export function getMotionVariants<T>(
  prefersReducedMotion: boolean,
  fullMotion: T,
  reducedMotion: T
): T {
  return prefersReducedMotion ? reducedMotion : fullMotion;
}
