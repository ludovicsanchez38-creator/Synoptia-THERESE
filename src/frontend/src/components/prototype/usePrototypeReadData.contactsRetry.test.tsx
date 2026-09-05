/**
 * B-546 : un incident réseau au premier montage figeait la liste des
 * contacts en erreur pour toute la session. Le garde d'auto-chargement ne
 * retentait jamais tant qu'`error` restait posé dans le magasin, alors que la
 * ressource sœur du brief (B-317) se relit au focus et au retour de
 * visibilité.
 */
import { act, renderHook, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import { useContactsStore } from '../../stores/contactsStore';
import { useContactsResource } from './usePrototypeReadData';

describe('B-546 : la liste des contacts en erreur se relit au retour du focus', () => {
  const fetchContacts = vi.fn(async () => undefined);
  beforeEach(() => {
    fetchContacts.mockClear();
    useContactsStore.setState({
      contacts: [],
      loading: false,
      loaded: false,
      error: 'Impossible de charger les contacts.',
      fetchContacts,
    } as never);
  });

  it('retente au focus de la fenêtre', async () => {
    renderHook(() => useContactsResource());
    expect(fetchContacts).not.toHaveBeenCalled();

    act(() => window.dispatchEvent(new Event('focus')));

    await waitFor(() => expect(fetchContacts).toHaveBeenCalledTimes(1));
  });
});
