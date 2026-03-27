/**
 * THERESE v2 - useMotionConfig Hook (US-012)
 *
 * Retourne des props framer-motion adaptes aux preferences
 * d'accessibilite (reduceMotion). Utilise le store + system preference.
 */

import { useMemo } from 'react';
import { useAccessibilityStore } from '../stores/accessibilityStore';
import type { Variants, Transition } from 'framer-motion';

interface MotionConfig {
  /** false si reduceMotion est actif, sinon les variants fournis */
  animate: false | string | Record<string, unknown>;
  /** Transition instantanee si reduceMotion */
  transition: Transition;
  /** true si les animations sont desactivees */
  isReduced: boolean;
}

/**
 * Hook qui adapte les animations framer-motion au setting reduceMotion.
 *
 * @example
 * const { isReduced, transition } = useMotionConfig();
 * <motion.div
 *   animate={isReduced ? false : { opacity: 1 }}
 *   transition={transition}
 * />
 */
export function useMotionConfig(): MotionConfig {
  const reduceMotion = useAccessibilityStore((s) => s.reduceMotion);

  // Combine user preference + system preference
  const systemReduced =
    typeof window !== 'undefined'
      ? window.matchMedia('(prefers-reduced-motion: reduce)').matches
      : false;

  const isReduced = reduceMotion || systemReduced;

  return useMemo(
    () => ({
      animate: isReduced ? false : 'animate',
      transition: isReduced ? { duration: 0 } : { duration: 0.2 },
      isReduced,
    }),
    [isReduced]
  );
}

/**
 * Helper pour obtenir des variants conditionnes par reduceMotion.
 *
 * @example
 * const variants = useMotionVariants(fadeInUp, noMotion);
 */
export function useMotionVariants<T extends Variants>(
  fullMotion: T,
  reducedMotion?: T
): T {
  const { isReduced } = useMotionConfig();
  return isReduced ? (reducedMotion || ({} as T)) : fullMotion;
}
