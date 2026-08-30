import { useCallback, useEffect, useRef, useState } from 'react';
import {
  AlertCircle,
  FileAudio,
  Mic,
  PanelRightClose,
  Play,
  ShieldCheck,
  Upload,
  Volume2,
} from 'lucide-react';
import {
  getVoiceLocalPreference,
  getVoiceLocalStatus,
  synthesizeSpeech,
  transcribeAudio,
  type VoiceLocalStatus,
} from '../../services/api/voice';
import { useDialogFocusTrap } from '../../hooks/useDialogFocusTrap';
import { usePanneauCouvrant } from '../../hooks/usePanneauCouvrant';
import { Spinner } from '../ui/Spinner';

function readableSize(bytes: number): string {
  if (bytes < 1_048_576) return `${Math.max(1, Math.round(bytes / 1024))} Ko`;
  return `${(bytes / 1_048_576).toFixed(1)} Mo`;
}

export function VoiceWorkspaceCanvas({
  onClose,
  onContinueInChat,
}: {
  onClose: () => void;
  onContinueInChat: (prompt: string) => void;
}) {
  const [status, setStatus] = useState<VoiceLocalStatus | null>(null);
  const [file, setFile] = useState<File | null>(null);
  const [transcript, setTranscript] = useState('');
  const [confirmationOpen, setConfirmationOpen] = useState(false);
  const [transcribing, setTranscribing] = useState(false);
  const [speechText, setSpeechText] = useState('');
  const [speechLoading, setSpeechLoading] = useState(false);
  const [speechUrl, setSpeechUrl] = useState<string | null>(null);
  const [transcriptionError, setTranscriptionError] = useState<string | null>(null);
  const [speechError, setSpeechError] = useState<string | null>(null);
  const [speechStatus, setSpeechStatus] = useState<string | null>(null);
  const [statusError, setStatusError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const dialogRef = useRef<HTMLElement>(null);
  // Hotfix 0.48.1 : isolation seulement quand le panneau RECOUVRE la zone.
  // Revue passe 2 : le clavier reste À LA PAGE en toutes circonstances -
  // le rail et l'en-tête sont actifs, un piège les rendrait inatteignables,
  // et un réarmement au redimensionnement volerait Escape à une modale.
  const estCouvrant = usePanneauCouvrant();
  useDialogFocusTrap(dialogRef, {
    active: true,
    onEscape: onClose,
    isolateBackground: estCouvrant,
    piegeClavier: false,
  });

  const loadStatus = useCallback(async () => {
    setStatusError(null);
    try {
      setStatus(await getVoiceLocalStatus());
    } catch (reason) {
      setStatus(null);
      setStatusError(reason instanceof Error ? reason.message : 'Le statut des moteurs vocaux est indisponible.');
    }
  }, []);

  useEffect(() => {
    void loadStatus();
  }, [loadStatus]);

  useEffect(() => () => {
    if (speechUrl) URL.revokeObjectURL(speechUrl);
  }, [speechUrl]);

  const preference = getVoiceLocalPreference();
  const usesLocalTranscription = preference === true || (preference === null && status?.ready === true);
  const transcriptionEngine = usesLocalTranscription ? 'Whisper local' : 'Groq Whisper cloud';
  const ttsReady = Boolean(status?.tts_available && status?.tts_voice_downloaded);

  function selectFile(selected: File | null) {
    setFile(selected);
    setTranscript('');
    setConfirmationOpen(false);
    setTranscriptionError(null);
  }

  function prepareTranscription() {
    if (!file) {
      setTranscriptionError('Choisis d’abord un fichier audio.');
      return;
    }
    setTranscriptionError(null);
    setConfirmationOpen(true);
  }

  async function confirmTranscription() {
    if (!file || transcribing) return;
    setConfirmationOpen(false);
    setTranscribing(true);
    setTranscriptionError(null);
    try {
      setTranscript(await transcribeAudio(file, file.name));
    } catch (reason) {
      setTranscriptionError(reason instanceof Error ? reason.message : 'La transcription a échoué.');
    } finally {
      setTranscribing(false);
    }
  }

  async function createSpeech() {
    if (!speechText.trim() || speechLoading) return;
    setSpeechLoading(true);
    setSpeechError(null);
    setSpeechStatus('Création de l’audio local…');
    try {
      const blob = await synthesizeSpeech(speechText.trim());
      if (speechUrl) URL.revokeObjectURL(speechUrl);
      setSpeechUrl(URL.createObjectURL(blob));
      setSpeechStatus('Audio local généré.');
    } catch (reason) {
      setSpeechStatus(null);
      setSpeechError(reason instanceof Error ? reason.message : 'La synthèse vocale a échoué.');
    } finally {
      setSpeechLoading(false);
    }
  }

  return (
    <aside ref={dialogRef} role="region" aria-labelledby="voice-workspace-title" tabIndex={-1} className="absolute inset-y-0 right-0 z-20 flex h-full w-full flex-col border-l border-border bg-surface-2 shadow-[-18px_0_45px_rgba(16,28,54,0.12)] sm:w-[calc(100%-48px)] xl:relative xl:w-[62%] xl:min-w-[720px] xl:shadow-none" data-testid="voice-workspace-canvas">
      <header className="relative shrink-0 border-b border-border bg-surface px-5 py-4 pr-16">
        <div className="flex items-start gap-3"><span className="grid h-9 w-9 place-items-center rounded-md border border-text bg-domaine-prospects-tint text-domaine-prospects shadow-[var(--shadow-card)]"><Mic className="h-4 w-4" /></span><div><h2 id="voice-workspace-title" data-dialog-autofocus tabIndex={-1} className="text-lg font-bold text-text outline-none">Voix et transcription</h2><p className="mt-0.5 text-xs text-text-muted">Importer un enregistrement, le transcrire, puis poursuivre dans le chat.</p></div></div>
        <button type="button" onClick={onClose} aria-label="Fermer l’espace Voix" className="absolute right-3 top-3 grid h-11 w-11 place-items-center rounded-md border border-border bg-surface text-text-muted"><PanelRightClose className="h-4 w-4" /></button>
      </header>

      {statusError && <div role="alert" className="mx-4 mt-3 rounded-md border border-warning/40 bg-[var(--color-warning-tint)] p-3 text-sm text-warning"><p>Statut vocal indisponible : {statusError}</p><button type="button" onClick={() => void loadStatus()} className="mt-2 rounded-md border border-warning px-3 py-2 font-semibold">Réessayer</button></div>}

      <div className="grid min-h-0 flex-1 lg:grid-cols-2">
        <section className="overflow-y-auto border-r border-border p-5">
          <h3 className="text-sm font-bold text-text">Transcrire un fichier</h3>
          <p className="mt-1 text-xs leading-5 text-text-muted">MP3, M4A, WAV, WebM et autres formats audio reconnus.</p>
          <input ref={fileInputRef} type="file" accept="audio/*,.m4a" className="hidden" onChange={(event) => selectFile(event.target.files?.[0] ?? null)} />
          <button type="button" onClick={() => fileInputRef.current?.click()} className="mt-4 flex min-h-32 w-full items-center justify-center rounded-md border border-dashed border-border bg-surface p-5 text-center text-sm text-text-muted hover:border-domaine-prospects">
            {file ? <span><FileAudio className="mx-auto mb-2 h-8 w-8 text-domaine-prospects" /><strong className="block max-w-sm truncate text-text">{file.name}</strong><span className="mt-1 block text-xs">{readableSize(file.size)} · cliquer pour remplacer</span></span> : <span><Upload className="mx-auto mb-2 h-8 w-8 text-domaine-prospects" /><strong className="block text-text">Choisir un enregistrement</strong><span className="mt-1 block text-xs">Le fichier n’est traité qu’après confirmation.</span></span>}
          </button>

          <div className={`mt-4 rounded-md border p-3 text-xs leading-5 ${usesLocalTranscription ? 'border-accent-cyan/30 bg-accent-tint text-accent' : 'border-warning/40 bg-[var(--color-warning-tint)] text-warning'}`}>
            <ShieldCheck className="mr-1 inline h-4 w-4" /><strong>{transcriptionEngine}</strong> · {usesLocalTranscription ? 'l’audio reste sur cette machine.' : 'le fichier sera envoyé à Groq après ta confirmation.'}
          </div>

          {confirmationOpen ? <div className="mt-4 rounded-md border border-warning/40 bg-[var(--color-warning-tint)] p-3 text-sm text-warning" data-testid="voice-transcription-confirmation"><strong>Confirmer la transcription avec {transcriptionEngine} ?</strong><div className="mt-3 flex justify-end gap-2"><button type="button" onClick={() => setConfirmationOpen(false)} className="rounded-sm border border-border bg-surface px-3 py-2 font-semibold">Annuler</button><button type="button" onClick={() => void confirmTranscription()} className="rounded-sm bg-accent-fill px-3 py-2 font-semibold text-accent-ink">Confirmer et transcrire</button></div></div> : <button type="button" onClick={prepareTranscription} disabled={!file || transcribing} className="mt-4 inline-flex w-full items-center justify-center gap-2 rounded-md bg-accent-fill px-4 py-3 text-sm font-semibold text-accent-ink disabled:opacity-50">{transcribing ? <Spinner taille="bouton" /> : <Mic className="h-4 w-4" />}{transcribing ? 'Transcription en cours…' : 'Préparer la transcription'}</button>}

          {transcriptionError && <div role="alert" className="mt-3 rounded-md border border-error/40 bg-[var(--color-error-tint)] p-3 text-sm text-error"><p><AlertCircle className="mr-1 inline h-4 w-4" />{transcriptionError}</p><button type="button" onClick={prepareTranscription} className="mt-2 rounded-md border border-error px-3 py-2 font-semibold">Réessayer</button></div>}

          {transcript && <div className="mt-5"><label className="text-sm font-semibold text-text">Transcription<textarea aria-label="Transcription" rows={8} value={transcript} onChange={(event) => setTranscript(event.target.value)} className="mt-2 w-full rounded-md border border-border bg-surface p-3 text-sm font-normal leading-6 text-text" /></label><button type="button" onClick={() => onContinueInChat(`Voici la transcription d’un enregistrement :\n\n${transcript}\n\nExtrais les décisions, engagements et prochaines actions.`)} className="mt-3 min-h-11 w-full rounded-md bg-domaine-taches px-4 py-2.5 text-sm font-semibold text-white">Analyser dans le chat</button></div>}
        </section>

        <section className="overflow-y-auto p-5">
          <h3 className="text-sm font-bold text-text">Lire un texte à voix haute</h3>
          <p className="mt-1 text-xs leading-5 text-text-muted">Synthèse locale Piper. Aucun texte n’est envoyé vers un service externe.</p>
          <label className="mt-4 block text-sm font-semibold text-text">Texte à lire<textarea aria-label="Texte à lire" rows={9} value={speechText} onChange={(event) => { setSpeechUrl(null); setSpeechStatus(null); setSpeechError(null); setSpeechText(event.target.value); }} placeholder="Colle ici le texte à convertir en audio…" className="mt-2 w-full rounded-md border border-border bg-surface p-3 text-sm font-normal leading-6 text-text" /></label>
          {!ttsReady && <div className="mt-3 rounded-md border border-warning/40 bg-[var(--color-warning-tint)] p-3 text-xs leading-5 text-warning">La voix locale doit être activée dans Paramètres → Confidentialité avant d’utiliser la synthèse.</div>}
          <button type="button" onClick={() => void createSpeech()} disabled={!speechText.trim() || !ttsReady || speechLoading} className="mt-4 inline-flex w-full items-center justify-center gap-2 rounded-md bg-accent-fill px-4 py-3 text-sm font-semibold text-accent-ink disabled:opacity-50">{speechLoading ? <Spinner taille="bouton" /> : <Volume2 className="h-4 w-4" />}{speechLoading ? 'Création de l’audio…' : 'Générer l’audio local'}</button>
          {speechStatus && <p role="status" className="mt-3 rounded-md border border-info/40 bg-[var(--color-info-tint)] p-3 text-sm text-info">{speechStatus}</p>}
          {speechError && <div role="alert" className="mt-3 rounded-md border border-error/40 bg-[var(--color-error-tint)] p-3 text-sm text-error"><p><AlertCircle className="mr-1 inline h-4 w-4" />{speechError}</p><button type="button" onClick={() => void createSpeech()} className="mt-2 rounded-md border border-error px-3 py-2 font-semibold">Réessayer</button></div>}
          {speechUrl && <div className="mt-5 rounded-md border border-border bg-surface p-4"><div className="mb-3 flex items-center gap-2 text-xs font-semibold text-text"><Play className="h-4 w-4 text-domaine-prospects" />Audio généré localement</div><audio controls src={speechUrl} className="w-full" /><a href={speechUrl} download="therese-tts.wav" className="mt-3 inline-flex rounded-sm border border-text px-3 py-2 text-xs font-semibold text-text">Enregistrer le WAV</a></div>}
        </section>
      </div>
    </aside>
  );
}
