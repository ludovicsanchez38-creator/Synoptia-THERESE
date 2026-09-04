/**
 * B-011 : le bouton d'envoi du formulaire de facture était HORS du formulaire.
 *
 * Mesuré au navigateur : `nb_form: 1`, `boutons_submit_dans_le_form: 0`, et le
 * seul `type="submit"` de la page (« Créer ») avait `.form === null`. Une frappe
 * Entrée dans un champ ne déclenchait AUCUN événement submit, les six champs
 * `required` n'étaient jamais évalués, et `onSubmit={handleSubmit}` était du
 * code mort : tout passait par un `onClick` posé à côté.
 *
 * Le formulaire se ferme avant le pied de page (la barre d'actions est hors du
 * bloc défilant, à dessein) : le lien se fait donc par `id` + attribut `form`,
 * sans déplacer quoi que ce soit à l'écran.
 */
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import { InvoiceForm } from './InvoiceForm';
import { useBillingProfileStore } from '../../stores/billingProfileStore';

const { createInvoiceMock, getBillingProfileStatusMock } = vi.hoisted(() => ({
  createInvoiceMock: vi.fn(),
  getBillingProfileStatusMock: vi.fn().mockResolvedValue({ is_complete: true, missing: [] }),
}));

vi.mock('../../services/api', async () => {
  const actual = await vi.importActual<typeof import('../../services/api')>('../../services/api');
  return {
    ...actual,
    listContacts: vi.fn().mockResolvedValue([
      { id: 'contact-1', first_name: 'Jean', last_name: 'Dupont', email: 'jean@example.com' },
    ]),
    createInvoice: createInvoiceMock,
    getBillingProfileStatus: getBillingProfileStatusMock,
  };
});

async function remplirLeFormulaire() {
  // B-307 : le <select> existe avant que listContacts ait livré ses options.
  // Attendre seulement son label laissait fireEvent viser une valeur encore
  // absente, course visible uniquement dans la suite complète sous charge.
  await screen.findByRole('option', { name: 'Jean Dupont' });
  const client = screen.getByLabelText(/Client/i);
  fireEvent.change(client, { target: { value: 'contact-1' } });
  expect(client).toHaveValue('contact-1');
  fireEvent.change(screen.getByPlaceholderText('Description'), { target: { value: 'Prestation' } });
  fireEvent.change(screen.getByLabelText('Prix HT ligne 1'), { target: { value: '100' } });
}

describe('B-011 : le bouton d’envoi appartient au formulaire', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    createInvoiceMock.mockResolvedValue({ id: 'inv-1' });
    getBillingProfileStatusMock.mockResolvedValue({ is_complete: true, missing: [] });
    useBillingProfileStore.setState({ missing: null });
  });

  it('le seul bouton de soumission de l’écran est associé au formulaire', async () => {
    const { container } = render(<InvoiceForm invoice={null} onClose={vi.fn()} onSave={vi.fn()} />);

    await screen.findByLabelText(/Client/i);
    const formulaire = container.querySelector('form');
    expect(formulaire).not.toBeNull();

    const soumissions = Array.from(
      container.querySelectorAll<HTMLButtonElement>('button[type="submit"]'),
    );
    expect(soumissions).toHaveLength(1);
    // `.form` vaut null quand le bouton est orphelin : c'est le défaut mesuré.
    expect(soumissions[0].form).toBe(formulaire);
    expect(soumissions[0].textContent).toMatch(/Créer/);
  });

  it('une soumission du formulaire (chemin de la touche Entrée) crée la facture une seule fois', async () => {
    const { container } = render(<InvoiceForm invoice={null} onClose={vi.fn()} onSave={vi.fn()} />);

    await remplirLeFormulaire();

    const formulaire = container.querySelector('form') as HTMLFormElement;
    // `requestSubmit` est exactement ce que déclenche la soumission implicite
    // au clavier : elle valide les champs requis puis émet `submit`.
    formulaire.requestSubmit();

    await waitFor(() => expect(createInvoiceMock).toHaveBeenCalledTimes(1));
  });

  it('un clic sur Créer ne crée qu’une seule facture', async () => {
    render(<InvoiceForm invoice={null} onClose={vi.fn()} onSave={vi.fn()} />);

    await remplirLeFormulaire();
    fireEvent.click(screen.getByRole('button', { name: /Créer/i }));

    await waitFor(() => expect(createInvoiceMock).toHaveBeenCalledTimes(1));
  });

  it('les champs requis sont réellement évalués par le formulaire avant l’envoi', async () => {
    render(<InvoiceForm invoice={null} onClose={vi.fn()} onSave={vi.fn()} />);

    // Contact renseigné, description laissée VIDE : le champ porte `required`.
    fireEvent.change(await screen.findByLabelText(/Client/i), { target: { value: 'contact-1' } });
    const description = screen.getByPlaceholderText('Description') as HTMLInputElement;

    const invalide = vi.fn();
    description.addEventListener('invalid', invalide);

    fireEvent.click(screen.getByRole('button', { name: /Créer/i }));

    // L'événement `invalid` n'est émis que par la validation NATIVE, au cours
    // de la soumission. Il prouve deux choses d'un coup : le bouton soumet
    // vraiment le formulaire, et rien ne coupe l'action par défaut du clic —
    // un `onClick={handleSubmit}` resté en place appellerait `preventDefault`
    // et la validation ne tournerait jamais, comme avant le correctif.
    expect(invalide).toHaveBeenCalledTimes(1);
    expect(createInvoiceMock).not.toHaveBeenCalled();
  });
});
