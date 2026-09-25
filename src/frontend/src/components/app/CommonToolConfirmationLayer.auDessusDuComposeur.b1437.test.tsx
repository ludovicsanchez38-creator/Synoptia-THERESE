/**
 * B-1437 (recette P-146, lots 1 et 4) : la carte de confirmation était fixée
 * à 96 px du bas de la fenêtre ; le composeur, plus haut, en était recouvert
 * de 14 à 27 px (cadre et zone de saisie). La carte se pose au-dessus du bord
 * haut réel du composeur.
 */
import { act, render, screen } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { useToolConfirmationStore } from '../../stores/toolConfirmationStore';
import { CommonToolConfirmationLayer } from './CommonToolConfirmationLayer';

vi.mock('../../services/api/chat', () => ({ confirmTool: vi.fn() }));

describe('B-1437 : la carte ne recouvre pas le composeur', () => {
  let composeur: HTMLDivElement;
  beforeEach(() => {
    useToolConfirmationStore.setState({ pending: [], hauteurCalque: 0 });
    composeur = document.createElement('div');
    composeur.setAttribute('data-zone-composeur', '');
    composeur.getBoundingClientRect = () => ({ top: 600, bottom: 800, left: 0, right: 1000, width: 1000, height: 200, x: 0, y: 600, toJSON: () => ({}) });
    document.body.appendChild(composeur);
    vi.spyOn(window, 'innerHeight', 'get').mockReturnValue(800);
  });
  afterEach(() => { composeur.remove(); vi.restoreAllMocks(); });

  it('se pose 8 px au-dessus du bord haut du composeur', () => {
    render(<CommonToolConfirmationLayer />);
    act(() => {
      useToolConfirmationStore.getState().add({ confirmation_id: 'c-1', tool_name: 'create_contact', arguments: { first_name: 'Julien' } });
    });
    const calque = screen.getByTestId('common-tool-confirmation-layer');
    expect(calque.style.bottom).toBe('208px');
  });
});
