import { useEffect, useRef, useCallback, useState } from 'react';

const AUTOSAVE_DELAY = 5000; // 5 secondes

function getDraftKey(conversationId: string | null): string | null {
  if (!conversationId) return null;
  return `therese-draft-${conversationId}`;
}

/**
 * Hook d'autosave pour les brouillons de messages.
 * Sauvegarde le contenu du textarea dans localStorage (debounced 5s).
 * Restaure le brouillon au chargement d'une conversation.
 */
export function useAutosave(conversationId: string | null) {
  const [lastSavedAt, setLastSavedAt] = useState<Date | null>(null);
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const lastSavedValueRef = useRef<string>('');

  // Sauvegarder un brouillon (debounced)
  const saveDraft = useCallback((content: string) => {
    const key = getDraftKey(conversationId);
    if (!key) return;

    // Annuler le timer précédent
    if (timerRef.current) {
      clearTimeout(timerRef.current);
    }

    // Ne pas sauvegarder si vide
    if (!content.trim()) {
      // Supprimer le brouillon existant si le champ est vidé
      if (lastSavedValueRef.current) {
        try { localStorage.removeItem(key); } catch { /* ignore */ }
        lastSavedValueRef.current = '';
      }
      return;
    }

    // Debounce la sauvegarde
    timerRef.current = setTimeout(() => {
      try {
        localStorage.setItem(key, content);
        lastSavedValueRef.current = content;
        setLastSavedAt(new Date());
      } catch {
        // localStorage plein ou indisponible - ignorer silencieusement
      }
    }, AUTOSAVE_DELAY);
  }, [conversationId]);

  // Restaurer le brouillon
  const restoreDraft = useCallback((): string => {
    const key = getDraftKey(conversationId);
    if (!key) return '';
    try {
      return localStorage.getItem(key) || '';
    } catch {
      return '';
    }
  }, [conversationId]);

  // Supprimer le brouillon (après envoi réussi)
  const clearDraft = useCallback(() => {
    const key = getDraftKey(conversationId);
    if (!key) return;
    try {
      localStorage.removeItem(key);
      lastSavedValueRef.current = '';
    } catch { /* ignore */ }
  }, [conversationId]);

  // Nettoyage du timer au démontage
  useEffect(() => {
    return () => {
      if (timerRef.current) {
        clearTimeout(timerRef.current);
      }
    };
  }, []);

  return { saveDraft, restoreDraft, clearDraft, lastSavedAt };
}
