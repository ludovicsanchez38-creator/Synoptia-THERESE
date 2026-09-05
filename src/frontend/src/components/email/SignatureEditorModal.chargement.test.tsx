/**
 * B-396 (05/09/2026) : quand la lecture de la signature échouait, le message
 * d'erreur s'affichait mais la zone restait vide et ACTIVE, « Enregistrer »
 * aussi : un clic envoyait une signature vide et le serveur l'écrasait.
 */
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

const getEmailSignature = vi.fn();
const updateEmailSignature = vi.fn();
vi.mock('../../services/api/email', () => ({
  getEmailSignature: (...args: unknown[]) => getEmailSignature(...args),
  updateEmailSignature: (...args: unknown[]) => updateEmailSignature(...args),
}));

import { SignatureEditorModal } from './SignatureEditorModal';

describe('B-396 - un chargement en échec ne laisse pas écraser la signature', () => {
  it('désactive la saisie et Enregistrer, et ne fait aucun PUT', async () => {
    getEmailSignature.mockRejectedValueOnce(new Error('réseau'));
    render(<SignatureEditorModal accountId="a1" accountEmail="marie@atelier.test" onClose={vi.fn()} />);

    const alerte = await screen.findByRole('alert');
    expect(alerte.textContent).toMatch(/Impossible de charger/);

    const zone = screen.getByRole('textbox') as HTMLTextAreaElement;
    expect(zone.disabled).toBe(true);
    const enregistrer = screen.getByRole('button', { name: /Enregistrer/ }) as HTMLButtonElement;
    expect(enregistrer.disabled).toBe(true);

    fireEvent.click(enregistrer);
    await waitFor(() => expect(updateEmailSignature).not.toHaveBeenCalled());
  });

  it('un chargement réussi laisse tout actif', async () => {
    getEmailSignature.mockResolvedValueOnce({ signature_html: '<p>Marie</p>' });
    render(<SignatureEditorModal accountId="a1" accountEmail="marie@atelier.test" onClose={vi.fn()} />);

    const zone = (await screen.findByRole('textbox')) as HTMLTextAreaElement;
    await waitFor(() => expect(zone.disabled).toBe(false));
    expect((screen.getByRole('button', { name: /Enregistrer/ }) as HTMLButtonElement).disabled).toBe(false);
  });
});
