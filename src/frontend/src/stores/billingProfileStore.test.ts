import { beforeEach, describe, expect, it, vi } from 'vitest';

const { getBillingProfileStatusMock } = vi.hoisted(() => ({
  getBillingProfileStatusMock: vi.fn(),
}));

vi.mock('../services/api', () => ({
  getBillingProfileStatus: getBillingProfileStatusMock,
}));

import { useBillingProfileStore } from './billingProfileStore';

describe('billingProfileStore', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    useBillingProfileStore.setState({ missing: null });
  });

  it('passe missing à null quand le profil est complet', async () => {
    getBillingProfileStatusMock.mockResolvedValue({ is_complete: true, missing: [] });

    await useBillingProfileStore.getState().refresh();

    expect(useBillingProfileStore.getState().missing).toBeNull();
  });

  it('remplit missing avec les champs manquants quand le profil est incomplet', async () => {
    getBillingProfileStatusMock.mockResolvedValue({ is_complete: false, missing: ['SIRET', 'adresse'] });

    await useBillingProfileStore.getState().refresh();

    expect(useBillingProfileStore.getState().missing).toEqual(['SIRET', 'adresse']);
  });

  it('reflète un profil complété entre deux refresh, sans remontage de composant', async () => {
    getBillingProfileStatusMock.mockResolvedValueOnce({ is_complete: false, missing: ['SIRET'] });
    await useBillingProfileStore.getState().refresh();
    expect(useBillingProfileStore.getState().missing).toEqual(['SIRET']);

    getBillingProfileStatusMock.mockResolvedValueOnce({ is_complete: true, missing: [] });
    await useBillingProfileStore.getState().refresh();
    expect(useBillingProfileStore.getState().missing).toBeNull();
  });

  it('ignore une erreur réseau sans planter (garde-fou best-effort)', async () => {
    useBillingProfileStore.setState({ missing: ['SIRET'] });
    getBillingProfileStatusMock.mockRejectedValue(new Error('network down'));

    await expect(useBillingProfileStore.getState().refresh()).resolves.toBeUndefined();
    expect(useBillingProfileStore.getState().missing).toEqual(['SIRET']);
  });
});
