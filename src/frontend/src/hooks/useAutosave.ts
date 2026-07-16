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
  const [draftError, setDraftError] = useState<string | null>(null);
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const lastSavedValueRef = useRef<string>('');
  const latestValueRef = useRef<string>('');
  const failedOperationRef = useRef<'save' | 'remove' | 'restore' | null>(null);

  const persistDraft = useCallback((key: string, content: string): boolean => {
    try {
      localStorage.setItem(key, content);
      lastSavedValueRef.current = content;
      setLastSavedAt(new Date());
      setDraftError(null);
      failedOperationRef.current = null;
      return true;
    } catch {
      failedOperationRef.current = 'save';
      setDraftError('Le brouillon reste dans le champ, mais sa copie locale n’a pas pu être enregistrée.');
      return false;
    }
  }, []);

  // Sauvegarder un brouillon (debounced)
  const saveDraft = useCallback((content: string) => {
    const key = getDraftKey(conversationId);
    if (!key) return;
    latestValueRef.current = content;

    // Annuler le timer précédent
    if (timerRef.current) {
      clearTimeout(timerRef.current);
    }

    // Ne pas sauvegarder si vide
    if (!content.trim()) {
      // Supprimer le brouillon existant si le champ est vidé
      if (lastSavedValueRef.current) {
        try {
          localStorage.removeItem(key);
          setDraftError(null);
          failedOperationRef.current = null;
        } catch {
          failedOperationRef.current = 'remove';
          setDraftError('Le brouillon vide n’a pas pu être retiré du stockage local.');
        }
        lastSavedValueRef.current = '';
      }
      return;
    }

    // Debounce la sauvegarde
    timerRef.current = setTimeout(() => {
      persistDraft(key, content);
    }, AUTOSAVE_DELAY);
  }, [conversationId, persistDraft]);

  const retrySave = useCallback(() => {
    const key = getDraftKey(conversationId);
    if (!key) return;
    if (failedOperationRef.current === 'remove') {
      try {
        localStorage.removeItem(key);
        lastSavedValueRef.current = '';
        latestValueRef.current = '';
        failedOperationRef.current = null;
        setDraftError(null);
      } catch {
        setDraftError('Le brouillon n’a toujours pas pu être retiré du stockage local.');
      }
      return;
    }
    if (failedOperationRef.current === 'restore') {
      try {
        localStorage.getItem(key);
        failedOperationRef.current = null;
        setDraftError(null);
      } catch {
        setDraftError('Le brouillon local reste indisponible.');
      }
      return;
    }
    if (latestValueRef.current.trim()) persistDraft(key, latestValueRef.current);
  }, [conversationId, persistDraft]);

  // Restaurer le brouillon
  const restoreDraft = useCallback((): string => {
    const key = getDraftKey(conversationId);
    if (!key) return '';
    try {
      const restored = localStorage.getItem(key) || '';
      lastSavedValueRef.current = restored;
      latestValueRef.current = restored;
      failedOperationRef.current = null;
      setDraftError(null);
      return restored;
    } catch {
      failedOperationRef.current = 'restore';
      setDraftError('Le brouillon local est indisponible. La saisie actuelle reste conservée dans le champ.');
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
      latestValueRef.current = '';
      failedOperationRef.current = null;
      setDraftError(null);
    } catch {
      failedOperationRef.current = 'remove';
      setDraftError('Le brouillon envoyé n’a pas pu être retiré du stockage local.');
    }
  }, [conversationId]);

  // Nettoyage du timer au démontage
  useEffect(() => {
    return () => {
      if (timerRef.current) {
        clearTimeout(timerRef.current);
      }
    };
  }, []);

  return { saveDraft, restoreDraft, clearDraft, retrySave, lastSavedAt, draftError };
}
