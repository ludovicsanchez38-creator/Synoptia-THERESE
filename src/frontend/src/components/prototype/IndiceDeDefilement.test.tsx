/**
 * B-562 (05/09/2026) : à l'arrivée sur l'accueil, la rangée des sources et
 * des parcours tombait sous le composeur flottant sans qu'aucun signe ne dise
 * qu'il reste du contenu plus bas. Un indice de défilement s'affiche tant que
 * le fil n'est pas au bout.
 */
import { createRef } from 'react';
import { act, fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import { IndiceDeDefilement } from './IndiceDeDefilement';

function conteneur(scrollHeight: number, clientHeight: number, scrollTop = 0) {
  const div = document.createElement('div');
  Object.defineProperty(div, 'scrollHeight', { value: scrollHeight, configurable: true });
  Object.defineProperty(div, 'clientHeight', { value: clientHeight, configurable: true });
  div.scrollTop = scrollTop;
  const scrollTo = vi.fn((options?: ScrollToOptions) => { div.scrollTop = options?.top ?? 0; });
  div.scrollTo = scrollTo as unknown as typeof div.scrollTo;
  document.body.appendChild(div);
  const ref = createRef<HTMLDivElement>();
  (ref as { current: HTMLDivElement | null }).current = div;
  return { div, ref, scrollTo };
}

describe('IndiceDeDefilement (B-562)', () => {
  it('visible quand du contenu reste sous le bord, absent quand tout est vu', () => {
    const { div, ref } = conteneur(2000, 800);
    render(<IndiceDeDefilement cible={ref} />);
    expect(screen.getByRole('button', { name: /Voir la suite/ })).toBeInTheDocument();

    act(() => { div.scrollTop = 1200; fireEvent.scroll(div); });
    expect(screen.queryByRole('button', { name: /Voir la suite/ })).not.toBeInTheDocument();
  });

  it('absent quand rien ne dépasse', () => {
    const { ref } = conteneur(700, 800);
    render(<IndiceDeDefilement cible={ref} />);
    expect(screen.queryByRole('button', { name: /Voir la suite/ })).not.toBeInTheDocument();
  });

  it('un clic fait défiler jusqu’au bout', () => {
    const { ref, scrollTo } = conteneur(2000, 800);
    render(<IndiceDeDefilement cible={ref} />);
    fireEvent.click(screen.getByRole('button', { name: /Voir la suite/ }));
    expect(scrollTo).toHaveBeenCalledWith(expect.objectContaining({ top: 2000 }));
  });
});
