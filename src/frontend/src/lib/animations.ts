/**
 * THÉRÈSE v2 - Animation Library
 *
 * Framer Motion variants and utilities for consistent animations.
 */

import type { Variants, Transition } from 'framer-motion';

// ============================================================
// Transitions
// ============================================================

export const springTransition: Transition = {
  type: 'spring',
  stiffness: 400,
  damping: 30,
};

export const easeTransition: Transition = {
  type: 'tween',
  ease: [0.4, 0, 0.2, 1],
  duration: 0.2,
};

export const smoothTransition: Transition = {
  type: 'tween',
  ease: [0.4, 0, 0.2, 1],
  duration: 0.3,
};

// ============================================================
// Fade Variants
// ============================================================

export const fadeIn: Variants = {
  initial: { opacity: 0 },
  animate: { opacity: 1 },
  exit: { opacity: 0 },
};

export const fadeInUp: Variants = {
  initial: { opacity: 0, y: 10 },
  animate: { opacity: 1, y: 0 },
  exit: { opacity: 0, y: 10 },
};

export const fadeInDown: Variants = {
  initial: { opacity: 0, y: -10 },
  animate: { opacity: 1, y: 0 },
  exit: { opacity: 0, y: -10 },
};

export const fadeInLeft: Variants = {
  initial: { opacity: 0, x: -10 },
  animate: { opacity: 1, x: 0 },
  exit: { opacity: 0, x: -10 },
};

export const fadeInRight: Variants = {
  initial: { opacity: 0, x: 10 },
  animate: { opacity: 1, x: 0 },
  exit: { opacity: 0, x: 10 },
};

// ============================================================
// Scale Variants
// ============================================================

export const scaleIn: Variants = {
  initial: { opacity: 0, scale: 0.95 },
  animate: { opacity: 1, scale: 1 },
  exit: { opacity: 0, scale: 0.95 },
};

export const scaleInBounce: Variants = {
  initial: { opacity: 0, scale: 0.8 },
  animate: {
    opacity: 1,
    scale: 1,
    transition: springTransition,
  },
  exit: { opacity: 0, scale: 0.8 },
};

export const popIn: Variants = {
  initial: { opacity: 0, scale: 0.5 },
  animate: {
    opacity: 1,
    scale: 1,
    transition: {
      type: 'spring',
      stiffness: 500,
      damping: 25,
    },
  },
  exit: { opacity: 0, scale: 0.5 },
};

// ============================================================
// Slide Variants
// ============================================================

export const slideInFromRight: Variants = {
  initial: { x: '100%', opacity: 0 },
  animate: { x: 0, opacity: 1 },
  exit: { x: '100%', opacity: 0 },
};

export const slideInFromLeft: Variants = {
  initial: { x: '-100%', opacity: 0 },
  animate: { x: 0, opacity: 1 },
  exit: { x: '-100%', opacity: 0 },
};

export const slideInFromTop: Variants = {
  initial: { y: '-100%', opacity: 0 },
  animate: { y: 0, opacity: 1 },
  exit: { y: '-100%', opacity: 0 },
};

export const slideInFromBottom: Variants = {
  initial: { y: '100%', opacity: 0 },
  animate: { y: 0, opacity: 1 },
  exit: { y: '100%', opacity: 0 },
};

// ============================================================
// List/Stagger Variants
// ============================================================

export const staggerContainer: Variants = {
  initial: {},
  animate: {
    transition: {
      staggerChildren: 0.05,
    },
  },
  exit: {
    transition: {
      staggerChildren: 0.02,
      staggerDirection: -1,
    },
  },
};

export const staggerItem: Variants = {
  initial: { opacity: 0, y: 10 },
  animate: {
    opacity: 1,
    y: 0,
    transition: easeTransition,
  },
  exit: {
    opacity: 0,
    y: 10,
    transition: { duration: 0.15 },
  },
};

// ============================================================
// Modal/Overlay Variants
// ============================================================

export const overlayVariants: Variants = {
  initial: { opacity: 0 },
  animate: { opacity: 1 },
  exit: { opacity: 0 },
};

export const modalVariants: Variants = {
  initial: { opacity: 0, scale: 0.95, y: 20 },
  animate: {
    opacity: 1,
    scale: 1,
    y: 0,
    transition: {
      type: 'spring',
      stiffness: 400,
      damping: 30,
    },
  },
  exit: {
    opacity: 0,
    scale: 0.95,
    y: 20,
    transition: { duration: 0.15 },
  },
};

export const sidebarVariants: Variants = {
  initial: { x: '100%' },
  animate: {
    x: 0,
    transition: smoothTransition,
  },
  exit: {
    x: '100%',
    transition: { duration: 0.2 },
  },
};

export const sidebarLeftVariants: Variants = {
  initial: { x: '-100%' },
  animate: {
    x: 0,
    transition: smoothTransition,
  },
  exit: {
    x: '-100%',
    transition: { duration: 0.2 },
  },
};

// ============================================================
// Message/Chat Variants
// ============================================================

export const messageVariants: Variants = {
  initial: { opacity: 0, y: 20, scale: 0.95 },
  animate: {
    opacity: 1,
    y: 0,
    scale: 1,
    transition: {
      type: 'spring',
      stiffness: 500,
      damping: 30,
    },
  },
  exit: { opacity: 0 },
};

export const typingIndicatorVariants: Variants = {
  initial: { opacity: 0, scale: 0.8 },
  animate: {
    opacity: 1,
    scale: 1,
    transition: springTransition,
  },
  exit: {
    opacity: 0,
    scale: 0.8,
    transition: { duration: 0.1 },
  },
};

// ============================================================
// Button/Interactive Variants
// ============================================================

export const buttonHover = {
  scale: 1.02,
  transition: { duration: 0.15 },
};

export const buttonTap = {
  scale: 0.98,
  transition: { duration: 0.1 },
};

export const pulseAnimation = {
  scale: [1, 1.05, 1],
  opacity: [1, 0.8, 1],
  transition: {
    duration: 2,
    repeat: Infinity,
    ease: 'easeInOut',
  },
};

// ============================================================
// Skeleton/Loading Variants
// ============================================================

export const shimmer: Variants = {
  initial: { x: '-100%' },
  animate: {
    x: '100%',
    transition: {
      duration: 1.5,
      repeat: Infinity,
      ease: 'linear',
    },
  },
};

// ============================================================
// Utility Functions
// ============================================================

/**
 * Create stagger variants with custom delay
 */
export function createStaggerVariants(delay: number = 0.05): {
  container: Variants;
  item: Variants;
} {
  return {
    container: {
      initial: {},
      animate: {
        transition: {
          staggerChildren: delay,
        },
      },
    },
    item: staggerItem,
  };
}

/**
 * Create slide variants with custom offset
 */
export function createSlideVariants(
  direction: 'left' | 'right' | 'up' | 'down',
  offset: number | string = '100%'
): Variants {
  const axis = direction === 'left' || direction === 'right' ? 'x' : 'y';
  const sign = direction === 'left' || direction === 'up' ? -1 : 1;
  const value = typeof offset === 'number' ? sign * offset : `${sign > 0 ? '' : '-'}${offset}`;

  return {
    initial: { [axis]: value, opacity: 0 },
    animate: { [axis]: 0, opacity: 1 },
    exit: { [axis]: value, opacity: 0 },
  };
}
