/**
 * B-769 (cycle 9) : l'étape de choix affichait un emoji (U+2728) dans un texte
 * d'interface, contraire à la charte (B-293). La garde de B-293 ne couvrait que
 * U+1F300-1FAFF : les pictogrammes du bloc U+2600-27BF lui échappaient.
 */
import { render } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import { ChoiceStep } from './ChoiceStep';

/** Emoji et pictogrammes : blocs U+1F300-1FAFF et U+2600-27BF. */
export const EMOJI_OU_PICTOGRAMME = /[\u{1F300}-\u{1FAFF}\u{2600}-\u{27BF}]/u;

describe('ChoiceStep - B-769, aucun emoji dans les textes', () => {
  it.each([null, { client_id: 'x', client_secret: 'y' }])('credentials MCP = %o', (mcpCredentials) => {
    const { container } = render(<ChoiceStep onSelect={vi.fn()} mcpCredentials={mcpCredentials as never} />);
    expect(container.textContent ?? '').not.toMatch(EMOJI_OU_PICTOGRAMME);
  });
});
