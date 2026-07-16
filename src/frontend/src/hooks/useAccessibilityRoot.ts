import { useEffect } from 'react';

export function useAccessibilityRoot(fontSize: string, reduceMotion: boolean): void {
  useEffect(() => {
    const root = document.documentElement;
    const previousFontSize = root.style.fontSize;
    root.style.fontSize = fontSize;
    root.style.setProperty('--therese-root-font-size', fontSize);

    return () => {
      root.style.fontSize = previousFontSize;
      root.style.removeProperty('--therese-root-font-size');
    };
  }, [fontSize]);

  useEffect(() => {
    const root = document.documentElement;
    if (reduceMotion) root.setAttribute('data-reduce-motion', 'true');
    else root.removeAttribute('data-reduce-motion');

    return () => root.removeAttribute('data-reduce-motion');
  }, [reduceMotion]);
}
