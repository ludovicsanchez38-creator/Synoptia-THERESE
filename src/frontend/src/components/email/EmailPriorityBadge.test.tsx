/**
 * B-293 (cycle 4) : le badge de priorité affichait une pastille emoji, contraire
 * à la charte (icônes SVG ou formes dessinées).
 */
import { render } from '@testing-library/react';
import { describe, expect, it } from 'vitest';

import { EmailPriorityBadge } from './EmailPriorityBadge';

const EMOJI = /[\u{1F300}-\u{1FAFF}]/u;

describe('EmailPriorityBadge : pastille dessinée', () => {
  it.each(['high', 'medium', 'low'] as const)("%s : aucun emoji, une pastille décorative", (priority) => {
    const { container } = render(<EmailPriorityBadge priority={priority} showText />);
    expect(container.textContent ?? '').not.toMatch(EMOJI);
    const pastille = container.querySelector('span[aria-hidden="true"]');
    expect(pastille).not.toBeNull();
    expect(pastille?.className).toMatch(/rounded-full/);
    expect(pastille?.className).toMatch(/bg-(error|agent-amber|agent-green)/);
  });
});
