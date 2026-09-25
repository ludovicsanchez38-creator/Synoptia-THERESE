/**
 * B-1392 (persona Zoé, cycle 13) : Échap, la croix ou un clic sur le fond
 * jetaient la saisie du formulaire de contact, sans demander. Les formulaires
 * Tâche et Rendez-vous posent déjà « Abandonner les modifications ? » (B-973) ;
 * la même question vaut ici, et seulement quand la saisie a changé.
 */
import { act, cleanup, fireEvent, render, screen } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { _clearEscapeHandlers, runTopEscapeHandler } from '../../lib/escapeStack';
import { useContactsStore } from '../../stores/contactsStore';
import { ContactModal } from './ContactModal';

const QUESTION = 'Abandonner les modifications ?';

describe('B-1392 : le formulaire de contact demande avant de jeter la saisie', () => {
  beforeEach(() => {
    _clearEscapeHandlers();
    useContactsStore.setState({ createContact: vi.fn().mockResolvedValue(undefined) });
  });
  afterEach(() => cleanup());

  function ouvrirEtSaisir(onClose = vi.fn()) {
    render(<ContactModal isOpen onClose={onClose} contact={null} />);
    fireEvent.change(screen.getByLabelText(/Prénom/), { target: { value: 'Zoé' } });
    return onClose;
  }

  it('Échap pose la question, un second Échap rend la saisie', () => {
    const onClose = ouvrirEtSaisir();
    let consomme = false;
    act(() => { consomme = runTopEscapeHandler(); });
    expect(consomme).toBe(true);
    expect(screen.getByText(QUESTION)).toBeInTheDocument();
    expect(onClose).not.toHaveBeenCalled();

    act(() => { runTopEscapeHandler(); });
    expect(screen.queryByText(QUESTION)).not.toBeInTheDocument();
    expect((screen.getByLabelText(/Prénom/) as HTMLInputElement).value).toBe('Zoé');
  });

  it('la croix, le fond et « Annuler » posent la question ; « Abandonner » ferme', () => {
    const onClose = ouvrirEtSaisir();
    fireEvent.click(screen.getByRole('button', { name: 'Fermer' }));
    expect(screen.getByText(QUESTION)).toBeInTheDocument();
    expect(onClose).not.toHaveBeenCalled();

    fireEvent.click(screen.getByRole('button', { name: 'Abandonner' }));
    expect(onClose).toHaveBeenCalledTimes(1);
  });

  it('un formulaire intact se ferme sans question', () => {
    const onClose = vi.fn();
    render(<ContactModal isOpen onClose={onClose} contact={null} />);
    let consomme = true;
    act(() => { consomme = runTopEscapeHandler(); });
    expect(consomme).toBe(false);
    fireEvent.click(screen.getByRole('button', { name: 'Annuler' }));
    expect(onClose).toHaveBeenCalledTimes(1);
    expect(screen.queryByText(QUESTION)).not.toBeInTheDocument();
  });
});
