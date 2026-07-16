/**
 * THÉRÈSE V3 - Ghost Text Prédictif
 *
 * Hook d'autocomplétion qui suggère la suite du texte en grisé.
 * Debounce 500ms, appel backend léger (Haiku/Ollama), Tab pour valider.
 */

import { useState, useEffect, useRef, useCallback } from 'react';
import { request } from '../services/api/core';

// L'endpoint POST /api/chat/complete n'est pas implémenté côté backend : sans
// ce garde, chaque frappe déclenchait un 404 (catché en silence mais polluant
// la console et le réseau, finding Codex 16/07). On neutralise l'appel tant que
// la suggestion prédictive n'est pas branchée ; repasser à true pour réactiver.
const GHOST_TEXT_ENABLED = false;

interface GhostTextResult {
  /** Suggestion de complétion (vide si aucune) */
  suggestion: string;
  /** Accepter la suggestion */
  accept: () => void;
  /** Ignorer la suggestion */
  dismiss: () => void;
}

/**
 * Hook de ghost text prédictif.
 *
 * @param input - Texte actuel dans le textarea
 * @param conversationId - ID conversation (contexte)
 * @param isStreaming - True si le LLM est en train de répondre
 */
export function useGhostText(
  input: string,
  conversationId: string | null,
  isStreaming: boolean,
): GhostTextResult {
  const [suggestion, setSuggestion] = useState('');
  const abortRef = useRef<AbortController | null>(null);
  const timeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const accept = useCallback(() => {
    setSuggestion('');
  }, []);

  const dismiss = useCallback(() => {
    setSuggestion('');
  }, []);

  useEffect(() => {
    // Annuler la requête précédente
    if (abortRef.current) {
      abortRef.current.abort();
      abortRef.current = null;
    }
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
      timeoutRef.current = null;
    }

    // Feature non branchée côté backend : ne déclenche aucun appel réseau.
    if (!GHOST_TEXT_ENABLED) {
      setSuggestion('');
      return;
    }

    // Conditions pour ne pas suggérer
    if (
      isStreaming ||
      input.length < 5 ||
      input.startsWith('/') ||
      input.endsWith('\n')
    ) {
      setSuggestion('');
      return;
    }

    // Debounce 500ms
    timeoutRef.current = setTimeout(async () => {
      const controller = new AbortController();
      abortRef.current = controller;

      // Timeout 800ms - si trop lent, pas de suggestion
      const timeoutId = setTimeout(() => controller.abort(), 800);

      try {
        const response = await request<{ completion: string }>('/api/chat/complete', {
          method: 'POST',
          body: JSON.stringify({
            input,
            conversation_id: conversationId,
          }),
          signal: controller.signal,
        });

        clearTimeout(timeoutId);

        if (response.completion && !controller.signal.aborted) {
          setSuggestion(response.completion);
        }
      } catch {
        // Silencieux : timeout, abort, erreur réseau
        clearTimeout(timeoutId);
        setSuggestion('');
      }
    }, 500);

    return () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
      if (abortRef.current) {
        abortRef.current.abort();
      }
    };
  }, [input, conversationId, isStreaming]);

  return { suggestion, accept, dismiss };
}
