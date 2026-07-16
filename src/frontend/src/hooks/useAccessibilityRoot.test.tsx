import { render } from '@testing-library/react';
import { afterEach, describe, expect, it } from 'vitest';
import { useAccessibilityRoot } from './useAccessibilityRoot';

function Harness({ fontSize, reduceMotion }: { fontSize: string; reduceMotion: boolean }) {
  useAccessibilityRoot(fontSize, reduceMotion);
  return null;
}

describe('useAccessibilityRoot', () => {
  afterEach(() => {
    document.documentElement.style.removeProperty('font-size');
    document.documentElement.style.removeProperty('--therese-root-font-size');
    document.documentElement.removeAttribute('data-reduce-motion');
  });

  it('applique la taille de texte à la racine du document', () => {
    const { rerender } = render(<Harness fontSize="16px" reduceMotion={false} />);
    expect(document.documentElement.style.fontSize).toBe('16px');
    expect(document.documentElement.style.getPropertyValue('--therese-root-font-size')).toBe('16px');

    rerender(<Harness fontSize="18px" reduceMotion={false} />);
    expect(document.documentElement.style.fontSize).toBe('18px');
  });

  it('pose et retire la préférence de réduction des animations sur la racine', () => {
    const { rerender } = render(<Harness fontSize="16px" reduceMotion />);
    expect(document.documentElement).toHaveAttribute('data-reduce-motion', 'true');

    rerender(<Harness fontSize="16px" reduceMotion={false} />);
    expect(document.documentElement).not.toHaveAttribute('data-reduce-motion');
  });
});
