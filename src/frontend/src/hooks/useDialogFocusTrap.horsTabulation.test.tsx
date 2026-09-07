/**
 * B-618 (persona Karim, c4) : dans la palette de la coque, Tab depuis la
 * liste « Résultats » posait le focus sur BODY, hors du dialogue, avant de
 * revenir au champ de recherche au coup suivant. Les options de la liste sont
 * des `<button role="option" tabindex="-1">` (focus itinérant) : le piège les
 * comptait comme « un focalisable après la liste » et laissait le navigateur
 * tabuler nativement, alors que rien de tabulable ne suit. Un élément à
 * `tabindex="-1"` n'est jamais dans l'ordre de tabulation, quel que soit son
 * type.
 */
import { fireEvent, render, screen } from '@testing-library/react';
import { useRef } from 'react';
import { describe, expect, it, vi } from 'vitest';
import { useDialogFocusTrap } from './useDialogFocusTrap';

function Palette() {
  const ref = useRef<HTMLDivElement>(null);
  useDialogFocusTrap(ref, { active: true, onEscape: vi.fn() });
  return (
    <div ref={ref} role="dialog" aria-label="Palette">
      <input aria-label="Rechercher" />
      <button type="button">Fermer</button>
      {/* Liste défilante : Chrome la rend focalisable au clavier quand ses
          enfants sont hors tabulation ; on simule avec tabIndex=0. */}
      <div role="listbox" aria-label="Résultats" tabIndex={0}>
        <button type="button" role="option" tabIndex={-1}>Tâches</button>
        <button type="button" role="option" tabIndex={-1}>Conversations</button>
      </div>
    </div>
  );
}

function DialogueAvecLecteur() {
  const ref = useRef<HTMLDivElement>(null);
  useDialogFocusTrap(ref, { active: true, onEscape: vi.fn() });
  return (
    <div ref={ref} role="dialog" aria-label="Voix">
      <button type="button">Fermer</button>
      <audio controls aria-label="Lecture" />
    </div>
  );
}

describe('B-463 : un lecteur avec commandes reste un arrêt de tabulation', () => {
  it('Tab depuis « Fermer » ne boucle pas : le lecteur suit', () => {
    render(<DialogueAvecLecteur />);
    const fermer = screen.getByRole('button', { name: 'Fermer' });
    fermer.focus();
    fireEvent.keyDown(document, { key: 'Tab' });
    // Sans lecteur compté comme focalisable, le piège aurait ramené le focus sur « Fermer » (premier = dernier).
    // Ici il laisse le navigateur avancer : en jsdom, le focus ne bouge pas, mais il n'a pas été forcé ailleurs.
    expect(document.activeElement).toBe(fermer);
    expect(screen.getByLabelText('Lecture')).toBeInTheDocument();
  });
});

describe('B-618 : les options à tabindex=-1 ne comptent pas comme un arrêt de tabulation', () => {
  it('Tab depuis la liste « Résultats » revient au champ de recherche', () => {
    render(<Palette />);
    const liste = screen.getByRole('listbox', { name: 'Résultats' });
    liste.focus();
    expect(document.activeElement).toBe(liste);

    fireEvent.keyDown(document, { key: 'Tab' });

    // jsdom ne déplace pas le focus sur Tab : seul le piège peut le faire
    // boucler. Sans correctif il reste sur la liste, et dans Chrome il part
    // sur BODY.
    expect(document.activeElement).toBe(screen.getByLabelText('Rechercher'));
  });

  it('Maj+Tab depuis le champ de recherche va au dernier élément tabulable, la liste, pas à une option', () => {
    render(<Palette />);
    const champ = screen.getByLabelText('Rechercher');
    champ.focus();

    fireEvent.keyDown(document, { key: 'Tab', shiftKey: true });

    expect(document.activeElement).toBe(screen.getByRole('listbox', { name: 'Résultats' }));
  });
});
