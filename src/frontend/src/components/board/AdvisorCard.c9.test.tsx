/**
 * B-793 (cycle 9) : la carte collait un suffixe hexadécimal d'opacité (« 30 »,
 * « 15 », « 40 ») à la couleur reçue, qui est une variable CSS
 * (`var(--color-agent-cyan)`) depuis la migration vers les jetons : halo, fond
 * d'icône et anneau devenaient des couleurs invalides, abandonnées par le navigateur.
 */
import { render } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import { AdvisorCard } from './AdvisorCard';

const couleur = 'var(--color-agent-cyan)';

describe('AdvisorCard - B-793, opacité dérivée d’une variable CSS', () => {
  it.each([
    ['en cours', { isLoading: true, isComplete: false }],
    ['achevée', { isLoading: false, isComplete: true }],
  ])('%s : aucun suffixe hexadécimal après une variable CSS, les teintes passent par color-mix', (_, etat) => {
    const { container } = render(
      <AdvisorCard role="analyst" name="L'Analyste" color={couleur} content="Analyse" isWaiting={false} {...etat} />,
    );
    const styles = [...container.querySelectorAll('[style]')].map((el) => el.getAttribute('style') ?? '').join('\n');
    expect(styles).not.toMatch(/var\(--[a-z-]+\)[0-9a-f]{2}\b/i);
    expect(styles).toMatch(/color-mix\(in srgb, var\(--color-agent-cyan\)/);
  });
});
