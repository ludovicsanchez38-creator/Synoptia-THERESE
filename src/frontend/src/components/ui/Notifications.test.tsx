/**
 * BUG-134 - lisibilité des toasts (retour Dr_logic, facturation) : le message
 * secondaire utilisait le token le plus terne (text-text-muted) sur un fond
 * translucide - « Renseigne la description d'au moins une ligne » ressortait à
 * peine. Spec : message en token primaire (text-text) + break-words pour
 * qu'une longue chaîne sans espace ne déborde jamais du toast.
 */

import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { useRef } from 'react';
import { beforeEach, describe, expect, it } from 'vitest';
import { Notifications } from './Notifications';
import { useStatusStore } from '../../stores/statusStore';
import { useDialogFocusTrap } from '../../hooks/useDialogFocusTrap';

function ModalAvecNotification() {
  const ref = useRef<HTMLDivElement>(null);
  useDialogFocusTrap(ref, { active: true, isolateBackground: true });
  return (
    <div>
      <div ref={ref} role="dialog" aria-modal="true" aria-label="Formulaire">
        <button>Enregistrer</button>
      </div>
      <Notifications />
    </div>
  );
}

describe('BUG-134 - toast lisible', () => {
  beforeEach(() => {
    useStatusStore.setState({ notifications: [] });
  });

  it('le message secondaire utilise le token primaire, pas le muted', () => {
    useStatusStore.setState({
      notifications: [
        {
          id: 'n1',
          type: 'warning',
          title: 'Champ requis',
          message: "Renseigne la description d'au moins une ligne",
          timestamp: new Date(),
        },
      ],
    });
    render(<Notifications />);

    const message = screen.getByText("Renseigne la description d'au moins une ligne");
    expect(message.className).toContain('text-text');
    expect(message.className).not.toContain('text-text-muted');
  });

  it('un message long sans espace ne déborde pas (break-words)', () => {
    useStatusStore.setState({
      notifications: [
        {
          id: 'n2',
          type: 'error',
          title: 'Erreur',
          message: 'https://exemple.fr/tres/long/chemin/sans/espace/qui/pourrait/deborder',
          timestamp: new Date(),
        },
      ],
    });
    render(<Notifications />);

    const message = screen.getByText(/tres\/long\/chemin/);
    expect(message.className).toContain('break-words');
  });

  it('reste fermable quand une modale isole le reste de la coque', async () => {
    useStatusStore.setState({
      notifications: [
        { id: 'n3', type: 'error', title: 'Échec du formulaire', timestamp: new Date() },
      ],
    });
    render(<ModalAvecNotification />);

    const fermer = screen.getByRole('button', { name: /Fermer la notification/ });
    await waitFor(() => expect(fermer.closest('[inert]')).toBeNull());
    fireEvent.click(fermer);

    await waitFor(() => expect(screen.queryByText('Échec du formulaire')).toBeNull());
  });
});
