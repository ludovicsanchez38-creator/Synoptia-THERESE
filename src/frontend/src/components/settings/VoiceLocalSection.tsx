/**
 * THÉRÈSE v2 - Section « Voix locale » (onglet Confidentialité)
 *
 * Activation en un clic de la reconnaissance vocale 100 % locale
 * (faster-whisper + Piper) : les modèles se téléchargent au premier usage,
 * puis plus aucun audio ne quitte la machine.
 */

import { useCallback, useEffect, useRef, useState } from 'react';
import { Loader2, Mic } from 'lucide-react';
import { Button } from '../ui/Button';
import {
  getVoiceLocalPreference,
  getVoiceLocalStatus,
  isVoiceLocalPreferred,
  setupVoiceLocal,
  setVoiceLocalPreferred,
  type VoiceLocalStatus,
} from '../../services/api/voice';

export function VoiceLocalSection() {
  const [status, setStatus] = useState<VoiceLocalStatus | null>(null);
  const [model, setModel] = useState<string>('base');
  const [useLocal, setUseLocal] = useState<boolean>(isVoiceLocalPreferred());
  const [error, setError] = useState<string | null>(null);
  const pollRef = useRef<number | null>(null);

  // BUG-129 : préférence tri-état. Si elle n'a jamais été posée alors que la
  // voix locale est PRÊTE (modèles installés avant l'existence de la
  // préférence, réinstallation, localStorage vidé), on la matérialise à true
  // dès que le statut le montre - même règle que le routage de la dictée.
  const reconcilePreference = useCallback((s: VoiceLocalStatus) => {
    if (s.ready && getVoiceLocalPreference() === null) {
      setVoiceLocalPreferred(true);
      setUseLocal(true);
    }
  }, []);

  const refresh = useCallback(async () => {
    try {
      const s = await getVoiceLocalStatus();
      setStatus(s);
      reconcilePreference(s);
      // Continuer le polling tant que le téléchargement tourne
      if (s.setup.state === 'running' && pollRef.current === null) {
        pollRef.current = window.setInterval(async () => {
          const next = await getVoiceLocalStatus().catch(() => null);
          if (next) {
            setStatus(next);
            reconcilePreference(next);
            if (next.setup.state !== 'running' && pollRef.current !== null) {
              window.clearInterval(pollRef.current);
              pollRef.current = null;
            }
          }
        }, 2000);
      }
    } catch (err) {
      console.error('Statut voix locale indisponible:', err);
    }
  }, [reconcilePreference]);

  useEffect(() => {
    refresh();
    return () => {
      if (pollRef.current !== null) window.clearInterval(pollRef.current);
    };
  }, [refresh]);

  async function handleActivate() {
    setError(null);
    try {
      await setupVoiceLocal(model);
      // BUG-129 : la préférence n'est PLUS posée ici. Le setup est asynchrone
      // (téléchargement en arrière-plan) : la poser tout de suite routait la
      // dictée vers un moteur pas encore prêt (503). C'est reconcilePreference
      // qui la pose quand le statut passe réellement à ready (polling refresh),
      // et le routage de la dictée applique la même règle côté chat.
      await refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Activation impossible');
    }
  }

  function handleToggleUseLocal() {
    const next = !useLocal;
    setUseLocal(next);
    setVoiceLocalPreferred(next);
  }

  if (!status) return null;

  const modelInfo = status.whisper_models[model];
  const downloadMb = modelInfo ? modelInfo.size_mb + 65 : 210; // + voix Piper ~60 Mo

  return (
    <section className="rounded-lg border border-border/50 p-4">
      <h4 className="text-sm font-semibold text-text flex items-center gap-2 mb-3">
        <Mic className="w-4 h-4 text-accent-cyan" />
        Voix locale souveraine
      </h4>

      {!status.stt_available ? (
        <p className="text-xs text-text-muted">
          La voix locale n'est pas embarquée dans cette version de THÉRÈSE.
          Mets l'application à jour pour en profiter.
        </p>
      ) : status.setup.state === 'running' ? (
        <div className="flex items-center gap-2 text-sm text-text-muted">
          <Loader2 className="w-4 h-4 animate-spin text-accent-cyan" />
          {status.setup.step || 'Téléchargement en cours...'}
        </div>
      ) : status.ready ? (
        <>
          <div className="rounded-lg bg-green-500/5 border border-green-500/20 p-3 mb-4">
            <p className="text-sm text-green-300">
              Voix locale prête (modèle Whisper « {status.active_whisper_model ?? status.default_whisper_model} »).
              Quand elle est activée pour le micro, ton audio ne quitte jamais ta machine.
            </p>
          </div>
          <div className="flex items-center justify-between">
            <div>
              <span className="text-sm font-medium text-text">Utiliser pour le micro</span>
              <span className="block text-xs text-text-muted">
                {useLocal
                  ? 'Transcription 100 % locale (aucun cloud)'
                  : 'Transcription via Groq (cloud)'}
              </span>
            </div>
            <button
              onClick={handleToggleUseLocal}
              className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                useLocal ? 'bg-accent-cyan' : 'bg-surface-elevated'
              }`}
              role="switch"
              aria-checked={useLocal}
              aria-label="Utiliser la voix locale pour le micro"
            >
              <span
                className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                  useLocal ? 'translate-x-6' : 'translate-x-1'
                }`}
              />
            </button>
          </div>
        </>
      ) : (
        <>
          <p className="text-xs text-text-muted mb-3">
            Reconnaissance vocale entièrement sur ta machine : un seul téléchargement
            (~{downloadMb} Mo, modèle + voix française), puis aucun audio n'est envoyé
            à un serveur externe.
          </p>
          <div className="flex items-center gap-3 mb-3">
            <label htmlFor="voice-local-model" className="text-xs text-text-muted">
              Modèle
            </label>
            <select
              id="voice-local-model"
              value={model}
              onChange={(e) => setModel(e.target.value)}
              className="px-3 py-1.5 bg-background/60 border border-border/50 rounded-lg text-sm text-text focus:outline-none focus:ring-2 focus:ring-accent-cyan/50"
            >
              {Object.entries(status.whisper_models).map(([key, info]) => (
                <option key={key} value={key}>
                  {info.label} ({info.size_mb} Mo)
                </option>
              ))}
            </select>
          </div>
          <Button variant="primary" size="sm" onClick={handleActivate}>
            Activer la voix locale
          </Button>
          {status.setup.state === 'error' && (
            <p className="text-xs text-red-400 mt-2">
              Échec du téléchargement : {status.setup.error} - réessaie (la reprise
              continue où ça s'était arrêté).
            </p>
          )}
          {error && <p className="text-xs text-red-400 mt-2">{error}</p>}
        </>
      )}
    </section>
  );
}
