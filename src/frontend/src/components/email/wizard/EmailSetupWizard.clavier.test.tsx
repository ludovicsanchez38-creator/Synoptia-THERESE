/**
 * B-093 : l'assistant « Configuration Email » annonçait `aria-modal="true"`
 * sans tenir aucune des promesses qui vont avec.
 *
 * Mesuré au navigateur : le focus restait HORS du dialogue à l'ouverture, et
 * trois Tab plus loin il s'échappait vers l'arrière-plan (« Aller au contenu
 * principal », « Contrôle des données », « Rechercher ⌘K », « Travaux ») que
 * `aria-modal` déclare pourtant inerte. Échap ne fermait pas l'assistant : la
 * cascade de la coque repliait TOUTE la vue Email embarquée, et `onCancel`
 * n'était jamais appelé.
 *
 * Le fichier ne posait ni `useDialogFocusTrap` ni le moindre handler clavier.
 */
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

vi.mock('../../../services/api', async () => {
  const reel = await vi.importActual<typeof import('../../../services/api')>('../../../services/api');
  return {
    ...reel,
    getEmailSetupStatus: vi.fn().mockResolvedValue({ google_credentials: null }),
  };
});

import { EmailSetupWizard } from './EmailSetupWizard';

describe("B-093 : l'assistant Email tient sa promesse de modale", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("à l'ouverture, le focus entre dans le dialogue", async () => {
    render(<EmailSetupWizard onComplete={() => {}} onCancel={() => {}} />);

    const dialogue = await screen.findByRole('dialog', { name: /Configuration Email/i });
    await waitFor(() => expect(dialogue.contains(document.activeElement)).toBe(true));
  });

  it('Tab depuis le dernier élément focalisable revient au premier, sans atteindre le fond', async () => {
    render(
      <>
        <button type="button">Arrière-plan</button>
        <EmailSetupWizard onComplete={() => {}} onCancel={() => {}} />
      </>,
    );

    const dialogue = await screen.findByRole('dialog', { name: /Configuration Email/i });
    const focalisables = dialogue.querySelectorAll<HTMLElement>(
      'button:not([disabled]), [href], input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"]):not([disabled])',
    );
    expect(focalisables.length).toBeGreaterThan(1);

    const premier = focalisables[0];
    const dernier = focalisables[focalisables.length - 1];
    dernier.focus();
    fireEvent.keyDown(document, { key: 'Tab' });

    expect(document.activeElement).toBe(premier);
    expect(screen.getByRole('button', { name: 'Arrière-plan' })).not.toBe(document.activeElement);
  });

  it('Échap ferme l’assistant lui-même, une seule fois', async () => {
    const annuler = vi.fn();
    render(<EmailSetupWizard onComplete={() => {}} onCancel={annuler} />);

    await screen.findByRole('dialog', { name: /Configuration Email/i });
    fireEvent.keyDown(document, { key: 'Escape' });

    expect(annuler).toHaveBeenCalledTimes(1);
  });
});
