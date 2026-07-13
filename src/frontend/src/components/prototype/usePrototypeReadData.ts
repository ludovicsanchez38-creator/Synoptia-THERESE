import { useCallback, useEffect, useState } from 'react';
import { fetchTodayDashboard, type TodayDashboard } from '../../services/api/dashboard';
import { useContactsStore } from '../../stores/contactsStore';

export type ReadResource<T> =
  | { status: 'loading'; data: null; error: null }
  | { status: 'ready'; data: T; error: null }
  | { status: 'error'; data: null; error: string };

export function useTodayDashboardResource() {
  const [resource, setResource] = useState<ReadResource<TodayDashboard>>({
    status: 'loading',
    data: null,
    error: null,
  });

  const refresh = useCallback(async () => {
    setResource({ status: 'loading', data: null, error: null });
    try {
      const data = await fetchTodayDashboard();
      setResource({ status: 'ready', data, error: null });
    } catch {
      setResource({
        status: 'error',
        data: null,
        error: 'Le brief du jour est indisponible pour le moment.',
      });
    }
  }, []);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  return { resource, refresh };
}

export function useContactsResource() {
  const contacts = useContactsStore((state) => state.contacts);
  const loading = useContactsStore((state) => state.loading);
  const loaded = useContactsStore((state) => state.loaded);
  const error = useContactsStore((state) => state.error);
  const fetchContacts = useContactsStore((state) => state.fetchContacts);

  const refresh = useCallback(async () => {
    try {
      await fetchContacts();
    } catch {
      // L’état d’erreur exploitable par l’interface est conservé dans le store.
    }
  }, [fetchContacts]);

  useEffect(() => {
    if (!loaded && !loading && !error) {
      void refresh();
    }
  }, [error, loaded, loading, refresh]);

  const resource: ReadResource<typeof contacts> = loading
    ? { status: 'loading', data: null, error: null }
    : error
      ? { status: 'error', data: null, error }
      : { status: 'ready', data: contacts, error: null };

  return { resource, refresh };
}
