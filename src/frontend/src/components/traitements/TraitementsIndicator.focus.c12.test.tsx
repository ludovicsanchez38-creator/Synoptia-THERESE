/**
 * B-1029 (ronde B3 du cycle 11, D-B3-1) : fermer « Travaux en cours » de
 * l'intérieur, par Échap ou par « Fermer les travaux », laissait le focus sur
 * BODY ; le déclencheur ne disait pas qu'il ouvre un panneau (aria-expanded).
 */
import { act, fireEvent, render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import { _clearEscapeHandlers, runTopEscapeHandler } from '../../lib/escapeStack';

vi.mock('../../services/api', () => ({ listerTraitements: vi.fn().mockResolvedValue([]), annulerTraitement: vi.fn() }));

import { useProcessingTasksStore } from '../../stores/processingTasksStore';
import { TraitementsIndicator } from './TraitementsIndicator';

describe('B-1029 : le panneau des travaux rend le focus à son déclencheur', () => {
  beforeEach(() => {
    _clearEscapeHandlers();
    useProcessingTasksStore.setState({
      traitements: [], erreur: null, arretsDemandes: new Set(), panneauOuvert: false,
      demarrerSondage: vi.fn(), arreterSondage: vi.fn(),
    } as never);
  });

  function ouvrir() {
    render(<TraitementsIndicator />);
    const declencheur = screen.getByRole('button', { name: /Travaux \(0 en cours\)/ });
    declencheur.focus();
    fireEvent.click(declencheur);
    return declencheur;
  }

  it('le déclencheur porte aria-expanded et aria-controls', () => {
    const declencheur = ouvrir();
    expect(declencheur).toHaveAttribute('aria-expanded', 'true');
    const panneau = screen.getByRole('dialog', { name: 'Travaux en cours' });
    expect(declencheur).toHaveAttribute('aria-controls', panneau.id);
    fireEvent.click(declencheur);
    expect(declencheur).toHaveAttribute('aria-expanded', 'false');
  });

  it('« Fermer les travaux » rend le focus au déclencheur', () => {
    const declencheur = ouvrir();
    const fermer = screen.getByRole('button', { name: 'Fermer les travaux' });
    fermer.focus();
    fireEvent.click(fermer);
    expect(screen.queryByRole('dialog', { name: 'Travaux en cours' })).toBeNull();
    expect(declencheur).toHaveFocus();
  });

  it('Échap depuis l’intérieur rend le focus au déclencheur', () => {
    const declencheur = ouvrir();
    screen.getByRole('button', { name: 'Fermer les travaux' }).focus();
    act(() => { runTopEscapeHandler(); });
    expect(screen.queryByRole('dialog', { name: 'Travaux en cours' })).toBeNull();
    expect(declencheur).toHaveFocus();
  });

  it('une fermeture alors que le focus est ailleurs ne le vole pas', () => {
    render(<><TraitementsIndicator /><input aria-label="ailleurs" /></>);
    fireEvent.click(screen.getByRole('button', { name: /Travaux/ }));
    const ailleurs = screen.getByLabelText('ailleurs');
    ailleurs.focus();
    act(() => { useProcessingTasksStore.getState().fermerPanneau(); });
    expect(ailleurs).toHaveFocus();
  });
});
