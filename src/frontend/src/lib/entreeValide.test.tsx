/**
 * B-1365 (personas Hugo et Zoé, cycle 13) : Entrée ne validait ni le contact,
 * ni la tâche, ni le projet, ni le nouveau document, ni la nouvelle section,
 * ni le dossier à synchroniser ; seul le devis réagissait. Un contact à deux
 * champs coûtait 14 frappes hors saisie.
 */
import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import { entreeValide } from './entreeValide';

function Formulaire({ action, desactive = false }: { action: () => void; desactive?: boolean }) {
  return (
    <div onKeyDown={entreeValide(action, desactive)}>
      <input aria-label="Nom" />
      <textarea aria-label="Notes" />
      <input aria-label="Actif" type="checkbox" />
    </div>
  );
}

describe('entreeValide (B-1365)', () => {
  it('Entrée dans un champ texte valide', () => {
    const action = vi.fn();
    render(<Formulaire action={action} />);
    fireEvent.keyDown(screen.getByLabelText('Nom'), { key: 'Enter' });
    expect(action).toHaveBeenCalledTimes(1);
  });

  it('Entrée dans une zone de texte fait un retour à la ligne, pas un envoi', () => {
    const action = vi.fn();
    render(<Formulaire action={action} />);
    fireEvent.keyDown(screen.getByLabelText('Notes'), { key: 'Enter' });
    fireEvent.keyDown(screen.getByLabelText('Actif'), { key: 'Enter' });
    expect(action).not.toHaveBeenCalled();
  });

  it('ni Maj+Entrée, ni une composition de caractères, ni un formulaire désactivé', () => {
    const action = vi.fn();
    const { unmount } = render(<Formulaire action={action} />);
    fireEvent.keyDown(screen.getByLabelText('Nom'), { key: 'Enter', shiftKey: true });
    fireEvent.keyDown(screen.getByLabelText('Nom'), { key: 'Enter', isComposing: true });
    unmount();
    render(<Formulaire action={action} desactive />);
    fireEvent.keyDown(screen.getByLabelText('Nom'), { key: 'Enter' });
    expect(action).not.toHaveBeenCalled();
  });
});
