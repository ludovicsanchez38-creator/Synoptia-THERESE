/**
 * B-1218 : chaque champ de clé de la modale des variables porte le nom de sa
 * variable, et le bouton qui montre ou masque la valeur a un nom.
 */
import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

import { EnvVarModal } from './EnvVarModal';

describe('B-1218 : noms accessibles de la modale des variables', () => {
  it('deux clés, deux noms distincts, et un bouton œil nommé', () => {
    render(
      <EnvVarModal
        preset={{ id: 'x', name: 'Service X', description: 'Test', env_required: ['GITHUB_TOKEN', 'STRIPE_API_KEY'] }}
        onSubmit={vi.fn()}
        onCancel={vi.fn()}
      />,
    );
    const champs = screen.getAllByLabelText(/Valeur de|Clé|Token|clé/i);
    const noms = champs.map((c) => c.getAttribute('aria-label') ?? '');
    expect(new Set(noms).size).toBe(noms.length);
    fireEvent.change(champs[0], { target: { value: 'secret' } });
    // B-1227 : bouton bascule, nom FIXE et état porté par aria-pressed seul.
    const oeil = screen.getByRole('button', { name: /Afficher la valeur de/ });
    const nomAvant = oeil.getAttribute('aria-label');
    fireEvent.click(oeil);
    expect({ nomFixe: oeil.getAttribute('aria-label') === nomAvant, presse: oeil.getAttribute('aria-pressed') })
      .toEqual({ nomFixe: true, presse: 'true' });
  });
});
