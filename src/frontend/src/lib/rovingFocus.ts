import type { KeyboardEvent } from 'react';

type RovingOrientation = 'horizontal' | 'vertical' | 'both';

export function handleRovingFocus(
  event: KeyboardEvent<HTMLElement>,
  selector: string,
  orientation: RovingOrientation = 'both',
): void {
  const forward = orientation !== 'vertical' && event.key === 'ArrowRight'
    || orientation !== 'horizontal' && event.key === 'ArrowDown';
  const backward = orientation !== 'vertical' && event.key === 'ArrowLeft'
    || orientation !== 'horizontal' && event.key === 'ArrowUp';
  if (!forward && !backward && event.key !== 'Home' && event.key !== 'End') return;

  const group = event.currentTarget.closest<HTMLElement>(
    '[role="radiogroup"], [role="tablist"], [role="toolbar"]',
  ) ?? event.currentTarget.parentElement;
  if (!group) return;
  const items = Array.from(group.querySelectorAll<HTMLElement>(selector)).filter(
    (item) => !item.hasAttribute('disabled') && item.getAttribute('aria-disabled') !== 'true',
  );
  if (items.length === 0) return;

  event.preventDefault();
  const currentIndex = Math.max(0, items.indexOf(event.currentTarget));
  let nextIndex = currentIndex;
  if (event.key === 'Home') nextIndex = 0;
  else if (event.key === 'End') nextIndex = items.length - 1;
  else if (forward) nextIndex = (currentIndex + 1) % items.length;
  else if (backward) nextIndex = (currentIndex - 1 + items.length) % items.length;

  const next = items[nextIndex];
  next.focus();
  next.click();
}
