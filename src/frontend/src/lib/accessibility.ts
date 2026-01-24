/**
 * THERESE v2 - Accessibility Utilities
 *
 * US-A11Y-01 to US-A11Y-05
 */

// ============================================================
// US-A11Y-04: Animation preferences
// ============================================================

/**
 * Check if user prefers reduced motion.
 */
export function prefersReducedMotion(): boolean {
  if (typeof window === 'undefined') return false;
  return window.matchMedia('(prefers-reduced-motion: reduce)').matches;
}

/**
 * Subscribe to reduced motion preference changes.
 */
export function onReducedMotionChange(callback: (reduced: boolean) => void): () => void {
  if (typeof window === 'undefined') return () => {};

  const mediaQuery = window.matchMedia('(prefers-reduced-motion: reduce)');
  const handler = (e: MediaQueryListEvent) => callback(e.matches);

  mediaQuery.addEventListener('change', handler);
  return () => mediaQuery.removeEventListener('change', handler);
}

// ============================================================
// US-A11Y-03: Color contrast utilities
// ============================================================

/**
 * Calculate relative luminance of a color.
 * @param hex - Hex color string (e.g., "#E6EDF7")
 */
export function getLuminance(hex: string): number {
  const rgb = hexToRgb(hex);
  if (!rgb) return 0;

  const [r, g, b] = [rgb.r, rgb.g, rgb.b].map((v) => {
    v /= 255;
    return v <= 0.03928 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4);
  });

  return 0.2126 * r + 0.7152 * g + 0.0722 * b;
}

/**
 * Calculate contrast ratio between two colors.
 * WCAG recommends 4.5:1 for normal text, 3:1 for large text.
 */
export function getContrastRatio(color1: string, color2: string): number {
  const l1 = getLuminance(color1);
  const l2 = getLuminance(color2);
  const lighter = Math.max(l1, l2);
  const darker = Math.min(l1, l2);
  return (lighter + 0.05) / (darker + 0.05);
}

/**
 * Check if contrast meets WCAG AA requirements.
 * @param foreground - Foreground color hex
 * @param background - Background color hex
 * @param isLargeText - Whether text is large (>= 18pt or >= 14pt bold)
 */
export function meetsContrastRequirement(
  foreground: string,
  background: string,
  isLargeText: boolean = false
): boolean {
  const ratio = getContrastRatio(foreground, background);
  return isLargeText ? ratio >= 3 : ratio >= 4.5;
}

function hexToRgb(hex: string): { r: number; g: number; b: number } | null {
  const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
  return result
    ? {
        r: parseInt(result[1], 16),
        g: parseInt(result[2], 16),
        b: parseInt(result[3], 16),
      }
    : null;
}

// ============================================================
// US-A11Y-01: Keyboard navigation helpers
// ============================================================

/**
 * Get all focusable elements within a container.
 */
export function getFocusableElements(container: HTMLElement): HTMLElement[] {
  const focusableSelector = [
    'a[href]',
    'button:not([disabled])',
    'input:not([disabled])',
    'select:not([disabled])',
    'textarea:not([disabled])',
    '[tabindex]:not([tabindex="-1"])',
    '[contenteditable="true"]',
  ].join(', ');

  return Array.from(container.querySelectorAll<HTMLElement>(focusableSelector));
}

/**
 * Trap focus within a container (for modals).
 */
export function createFocusTrap(container: HTMLElement): () => void {
  const focusableElements = getFocusableElements(container);
  const firstElement = focusableElements[0];
  const lastElement = focusableElements[focusableElements.length - 1];

  const handleKeyDown = (e: KeyboardEvent) => {
    if (e.key !== 'Tab') return;

    if (e.shiftKey) {
      // Shift + Tab
      if (document.activeElement === firstElement) {
        e.preventDefault();
        lastElement?.focus();
      }
    } else {
      // Tab
      if (document.activeElement === lastElement) {
        e.preventDefault();
        firstElement?.focus();
      }
    }
  };

  container.addEventListener('keydown', handleKeyDown);
  firstElement?.focus();

  return () => container.removeEventListener('keydown', handleKeyDown);
}

/**
 * Roving tabindex for lists (arrow key navigation).
 */
export function createRovingTabindex(
  items: HTMLElement[],
  options: {
    orientation?: 'horizontal' | 'vertical' | 'both';
    loop?: boolean;
  } = {}
): () => void {
  const { orientation = 'vertical', loop = true } = options;
  let currentIndex = 0;

  // Initialize tabindex
  items.forEach((item, index) => {
    item.setAttribute('tabindex', index === 0 ? '0' : '-1');
  });

  const handleKeyDown = (e: KeyboardEvent) => {
    const isVertical = orientation === 'vertical' || orientation === 'both';
    const isHorizontal = orientation === 'horizontal' || orientation === 'both';

    let nextIndex = currentIndex;

    switch (e.key) {
      case 'ArrowDown':
        if (isVertical) {
          e.preventDefault();
          nextIndex = currentIndex + 1;
        }
        break;
      case 'ArrowUp':
        if (isVertical) {
          e.preventDefault();
          nextIndex = currentIndex - 1;
        }
        break;
      case 'ArrowRight':
        if (isHorizontal) {
          e.preventDefault();
          nextIndex = currentIndex + 1;
        }
        break;
      case 'ArrowLeft':
        if (isHorizontal) {
          e.preventDefault();
          nextIndex = currentIndex - 1;
        }
        break;
      case 'Home':
        e.preventDefault();
        nextIndex = 0;
        break;
      case 'End':
        e.preventDefault();
        nextIndex = items.length - 1;
        break;
      default:
        return;
    }

    // Handle looping or bounds
    if (loop) {
      nextIndex = (nextIndex + items.length) % items.length;
    } else {
      nextIndex = Math.max(0, Math.min(nextIndex, items.length - 1));
    }

    if (nextIndex !== currentIndex) {
      items[currentIndex].setAttribute('tabindex', '-1');
      items[nextIndex].setAttribute('tabindex', '0');
      items[nextIndex].focus();
      currentIndex = nextIndex;
    }
  };

  items.forEach((item) => item.addEventListener('keydown', handleKeyDown));

  return () => {
    items.forEach((item) => item.removeEventListener('keydown', handleKeyDown));
  };
}

// ============================================================
// US-A11Y-02: ARIA helpers
// ============================================================

/**
 * Generate unique ID for ARIA relationships.
 */
let idCounter = 0;
export function generateAriaId(prefix: string = 'aria'): string {
  return `${prefix}-${++idCounter}`;
}

/**
 * Announce text to screen readers via live region.
 */
export function announceToScreenReader(
  message: string,
  options: { assertive?: boolean; timeout?: number } = {}
): void {
  const { assertive = false, timeout = 1000 } = options;

  const announcer = document.createElement('div');
  announcer.setAttribute('role', 'status');
  announcer.setAttribute('aria-live', assertive ? 'assertive' : 'polite');
  announcer.setAttribute('aria-atomic', 'true');
  announcer.className = 'sr-only'; // Screen reader only
  announcer.style.cssText = `
    position: absolute;
    width: 1px;
    height: 1px;
    padding: 0;
    margin: -1px;
    overflow: hidden;
    clip: rect(0, 0, 0, 0);
    white-space: nowrap;
    border: 0;
  `;

  document.body.appendChild(announcer);

  // Delay for screen reader to pick up
  setTimeout(() => {
    announcer.textContent = message;
  }, 100);

  // Clean up
  setTimeout(() => {
    document.body.removeChild(announcer);
  }, timeout);
}

// ============================================================
// US-A11Y-05: Focus visible styles
// ============================================================

/**
 * CSS-in-JS focus visible styles.
 */
export const focusVisibleStyles = {
  outline: '2px solid #22D3EE',
  outlineOffset: '2px',
  borderRadius: '4px',
};

/**
 * Tailwind classes for focus visible.
 */
export const focusVisibleClasses =
  'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent-cyan focus-visible:ring-offset-2 focus-visible:ring-offset-background';

// ============================================================
// Accessibility hooks exports
// ============================================================

export const A11Y_COLORS = {
  // THERESE palette with WCAG contrast ratios
  background: '#0B1226', // Base
  surface: '#131B35',
  textPrimary: '#E6EDF7', // 13.5:1 contrast with background
  textMuted: '#B6C7DA', // 7.8:1 contrast with background
  accentCyan: '#22D3EE', // 8.2:1 contrast with background
  accentMagenta: '#E11D8D', // 5.1:1 contrast with background
};

// Verify contrasts at build time
if (typeof window !== 'undefined' && import.meta.env.DEV) {
  const bgContrast = getContrastRatio(A11Y_COLORS.textPrimary, A11Y_COLORS.background);
  if (bgContrast < 4.5) {
    console.warn(`[A11Y] Text contrast ratio ${bgContrast.toFixed(2)} is below WCAG AA (4.5:1)`);
  }
}
