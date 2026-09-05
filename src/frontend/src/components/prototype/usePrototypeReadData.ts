import { useCallback, useEffect, useState } from 'react';
import { fetchTodayDashboard, type TodayDashboard } from '../../services/api/dashboard';
import { useContactsStore } from '../../stores/contactsStore';

export const TODAY_REFRESH_INTERVAL_MS = 5 * 60_000;

// B-426 : pendant une revalidation (ou après un échec de revalidation), les
// données déjà affichées restent portées par la ressource au lieu de
// disparaître ; `data` n'est garanti non nul que sur `ready`.
export type ReadResource<T> =
  | { status: 'loading'; data: T | null; error: null }
  | { status: 'ready'; data: T; error: null }
  | { status: 'error'; data: T | null; error: string };

export function useTodayDashboardResource() {
  const [resource, setResource] = useState<ReadResource<TodayDashboard>>({
    status: 'loading',
    data: null,
    error: null,
  });

  const refresh = useCallback(async () => {
    // B-426 : on garde les données affichées le temps de la revalidation.
    setResource((prev) => ({ status: 'loading', data: prev.data, error: null }));
    try {
      const data = await fetchTodayDashboard();
      setResource({ status: 'ready', data, error: null });
    } catch {
      setResource((prev) => ({
        status: 'error',
        data: prev.data,
        error: 'Le brief du jour est indisponible pour le moment.',
      }));
    }
  }, []);

  useEffect(() => {
    void refresh();
    // B-317 : la coque reste montée quand on quitte puis rouvre l'accueil.
    // Le brief ne pouvait donc plus se relire après son premier chargement et
    // gardait « 0 élément » malgré des créations métier ultérieures. Le focus,
    // le retour de visibilité et une cadence bornée couvrent aussi le cas où
    // l'utilisateur laisse l'accueil ouvert.
    const onFocus = () => void refresh();
    const onVisibilityChange = () => {
      if (document.visibilityState === 'visible') void refresh();
    };
    const interval = window.setInterval(() => void refresh(), TODAY_REFRESH_INTERVAL_MS);
    window.addEventListener('focus', onFocus);
    document.addEventListener('visibilitychange', onVisibilityChange);
    return () => {
      window.clearInterval(interval);
      window.removeEventListener('focus', onFocus);
      document.removeEventListener('visibilitychange', onVisibilityChange);
    };
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
