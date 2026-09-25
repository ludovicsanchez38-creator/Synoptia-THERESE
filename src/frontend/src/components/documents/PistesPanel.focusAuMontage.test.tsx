/**
 * B-1370 (persona Hugo, cycle 13) : ouvrir un document posait le focus sur
 * « Replier le volet Pistes », à l'autre bout de l'écran. Le transfert de
 * B-288 (rendre le focus au bouton qui remplace celui qu'on vient de
 * cliquer) s'appliquait à tout focus perdu dès le second passage de l'effet :
 * le double montage de StrictMode, ou la liste des documents démontée à
 * l'ouverture, suffisait. Il ne joue plus qu'après un clic sur la bascule.
 */
import { fireEvent, render, screen } from '@testing-library/react';
import { StrictMode } from 'react';
import { describe, expect, it, vi } from 'vitest';

import { PistesPanel } from './PistesPanel';

describe('B-1370 : le volet Pistes ne prend pas le focus à l’ouverture', () => {
  it('monté avec un focus perdu, il le laisse à la page', () => {
    (document.activeElement as HTMLElement | null)?.blur();
    render(
      <StrictMode>
        <PistesPanel pistes={[]} onExplore={vi.fn()} onIgnore={vi.fn()} />
      </StrictMode>,
    );

    expect(document.activeElement).not.toBe(screen.getByRole('button', { name: 'Replier le volet Pistes' }));
  });

  it('B-288 tient toujours : replier rend le focus au bouton « Déplier »', () => {
    render(
      <StrictMode>
        <PistesPanel pistes={[]} onExplore={vi.fn()} onIgnore={vi.fn()} />
      </StrictMode>,
    );
    const replier = screen.getByRole('button', { name: 'Replier le volet Pistes' });
    replier.focus();
    fireEvent.click(replier);

    expect(document.activeElement).toBe(screen.getByRole('button', { name: /Déplier le volet Pistes/ }));
  });
});
