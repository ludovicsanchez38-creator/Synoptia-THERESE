/**
 * B-070 — deux marqueurs d'autofocus dans un même dialogue, donc un mort.
 *
 * `useDialogFocusTrap` choisit par `dialog.querySelector('[data-dialog-autofocus]')`,
 * qui rend la PREMIÈRE occurrence dans l'ordre du document. Le centre de
 * capacités en portait deux : le titre, dans l'en-tête, et le champ de
 * recherche, plus bas. Le titre gagnait toujours ; le marqueur du champ ne
 * servait à rien alors que le code laissait croire l'inverse, et il fallait
 * tabuler pour atteindre la recherche.
 *
 * L'arbitrage retenu est celui de la fiche : dans un centre qui s'ouvre pour
 * chercher, le focus va au champ de recherche. Le second test ferme la porte
 * au doublon plutôt qu'à ce seul cas — c'est la concurrence de marqueurs qui
 * est le défaut, pas le nom de celui qui l'emportait.
 */
import { render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

import { CapabilityCenter, TrustCenter } from './CapabilityCenter';

describe('CapabilityCenter — un seul marqueur d’autofocus par dialogue', () => {
  it('à l’ouverture, le focus arrive dans le champ de recherche', () => {
    render(<CapabilityCenter onClose={vi.fn()} onChoose={vi.fn()} />);

    const champ = screen.getByLabelText('Rechercher une capacité');
    expect(document.activeElement).toBe(champ);
  });

  it('aucun dialogue ne porte plus d’un marqueur d’autofocus', () => {
    const { container } = render(
      <>
        <CapabilityCenter onClose={vi.fn()} onChoose={vi.fn()} />
        <TrustCenter onClose={vi.fn()} onOpenPrivacy={vi.fn()} onOpenAdvanced={vi.fn()} />
      </>,
    );

    const dialogues = Array.from(container.querySelectorAll('[role="dialog"]'));
    expect(dialogues.length).toBeGreaterThan(1);
    for (const dialogue of dialogues) {
      const marqueurs = Array.from(dialogue.querySelectorAll('[data-dialog-autofocus]'));
      expect(
        marqueurs.map((element) => element.tagName),
        `${dialogue.getAttribute('aria-label') ?? dialogue.getAttribute('aria-labelledby')} porte ${marqueurs.length} marqueurs`,
      ).toHaveLength(1);
    }
  });
});
