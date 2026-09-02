/**
 * B-001 : un profil qu'on n'a pas pu lire ne se tait pas.
 *
 * Le formulaire n'affichait son avertissement que sur une liste de champs
 * manquants. Quand la lecture du profil échouait, le store retombait sur la
 * valeur d'un profil COMPLET (`missing: null`, `catch` vide) : l'écran était
 * alors strictement identique à celui d'un profil vérifié et conforme, et la
 * personne saisissait sa facture en croyant ses mentions légales en place.
 *
 * Le test rend le formulaire plutôt que de relire le JSX : c'est la promesse
 * d'écran qui est en cause, pas la présence d'une chaîne dans un fichier.
 */
import { render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

const { getBillingProfileStatusMock } = vi.hoisted(() => ({
  getBillingProfileStatusMock: vi.fn(),
}));

vi.mock('../../services/api', async () => {
  const reel = await vi.importActual<typeof import('../../services/api')>('../../services/api');
  return {
    ...reel,
    listContacts: vi.fn().mockResolvedValue([]),
    getBillingProfileStatus: getBillingProfileStatusMock,
  };
});

import { useBillingProfileStore } from '../../stores/billingProfileStore';

import { InvoiceForm } from './InvoiceForm';

const AVERTISSEMENT_ILLISIBLE = /Impossible de vérifier les infos de ta société/;

describe("B-001 : le formulaire annonce un profil qu'il n'a pas pu lire", () => {
  beforeEach(() => {
    getBillingProfileStatusMock.mockReset();
    useBillingProfileStore.setState({ missing: null, statutLecture: 'jamais_lu' });
  });

  it('affiche un avertissement quand la lecture du profil échoue', async () => {
    getBillingProfileStatusMock.mockRejectedValue(new Error('backend éteint'));

    render(<InvoiceForm invoice={null} onClose={vi.fn()} onSave={vi.fn()} />);

    await waitFor(() =>
      expect(screen.getByText(AVERTISSEMENT_ILLISIBLE)).toBeInTheDocument(),
    );
  });

  it("n'avertit de rien quand le profil est lu et complet", async () => {
    getBillingProfileStatusMock.mockResolvedValue({ is_complete: true, missing: [] });

    render(<InvoiceForm invoice={null} onClose={vi.fn()} onSave={vi.fn()} />);

    await waitFor(() => expect(useBillingProfileStore.getState().statutLecture).toBe('lu'));
    expect(screen.queryByText(AVERTISSEMENT_ILLISIBLE)).not.toBeInTheDocument();
    expect(screen.queryByText(/Infos de ta société incomplètes/)).not.toBeInTheDocument();
  });

  it("garde l'avertissement des champs manquants quand le profil EST lu", async () => {
    getBillingProfileStatusMock.mockResolvedValue({ is_complete: false, missing: ['SIRET'] });

    render(<InvoiceForm invoice={null} onClose={vi.fn()} onSave={vi.fn()} />);

    await waitFor(() =>
      expect(screen.getByText(/Infos de ta société incomplètes/)).toBeInTheDocument(),
    );
    expect(screen.queryByText(AVERTISSEMENT_ILLISIBLE)).not.toBeInTheDocument();
  });
});
