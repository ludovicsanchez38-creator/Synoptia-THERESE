import { useEffect, useRef, useState } from 'react';
import {
  AlertCircle,
  FileAudio,
  Loader2,
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
  const [error, setError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const dialogRef = useRef<HTMLElement>(null);
  useDialogFocusTrap(dialogRef, { active: true, onEscape: onClose, isolateBackground: true });

  useEffect(() => {
    let active = true;
    getVoiceLocalStatus()
      .then((value) => { if (active) setStatus(value); })
      .catch(() => { if (active) setStatus(null); });
    return () => { active = false; };
  }, []);

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
    setError(null);
  }

  function prepareTranscription() {
    if (!file) {
      setError('Choisis d’abord un fichier audio.');
      return;
    }
    setError(null);
    setConfirmationOpen(true);
  }

  async function confirmTranscription() {
    if (!file || transcribing) return;
    setConfirmationOpen(false);
    setTranscribing(true);
    setError(null);
    try {
      setTranscript(await transcribeAudio(file, file.name));
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : 'La transcription a échoué.');
    } finally {
      setTranscribing(false);
    }
  }

  async function createSpeech() {
    if (!speechText.trim() || speechLoading) return;
    setSpeechLoading(true);
    setError(null);
    try {
      const blob = await synthesizeSpeech(speechText.trim());
      if (speechUrl) URL.revokeObjectURL(speechUrl);
      setSpeechUrl(URL.createObjectURL(blob));
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : 'La synthèse vocale a échoué.');
    } finally {
      setSpeechLoading(false);
    }
  }

  return (
    <aside ref={dialogRef} role="dialog" aria-modal="true" aria-labelledby="voice-workspace-title" tabIndex={-1} className="absolute inset-y-0 right-0 z-20 flex h-full w-full flex-col border-l border-border bg-surface-2 shadow-[-18px_0_45px_rgba(16,28,54,0.12)] xl:w-[62%] xl:min-w-[720px]" data-testid="voice-workspace-canvas">
      <header className="relative shrink-0 border-b border-border bg-surface px-5 py-4 pr-16">
        <div className="flex items-start gap-3"><span className="grid h-9 w-9 place-items-center rounded-[10px] border border-text bg-[var(--k4bg)] text-[var(--k4)] shadow-[2px_2px_0_var(--btn-ink)]"><Mic className="h-4 w-4" /></span><div><h2 id="voice-workspace-title" data-dialog-autofocus tabIndex={-1} className="text-lg font-bold text-text outline-none">Voix et transcription</h2><p className="mt-0.5 text-xs text-text-muted">Importer un enregistrement, le transcrire, puis poursuivre dans le chat.</p></div></div>
        <button type="button" onClick={onClose} aria-label="Fermer l’espace Voix" className="absolute right-4 top-4 grid h-9 w-9 place-items-center rounded-[9px] border border-border bg-surface text-text-muted"><PanelRightClose className="h-4 w-4" /></button>
      </header>

      <div className="grid min-h-0 flex-1 lg:grid-cols-2">
        <section className="overflow-y-auto border-r border-border p-5">
          <h3 className="text-sm font-bold text-text">Transcrire un fichier</h3>
          <p className="mt-1 text-xs leading-5 text-text-muted">MP3, M4A, WAV, WebM et autres formats audio reconnus.</p>
          <input ref={fileInputRef} type="file" accept="audio/*,.m4a" className="hidden" onChange={(event) => selectFile(event.target.files?.[0] ?? null)} />
          <button type="button" onClick={() => fileInputRef.current?.click()} className="mt-4 flex min-h-32 w-full items-center justify-center rounded-[12px] border border-dashed border-border bg-surface p-5 text-center text-sm text-text-muted hover:border-[var(--k4)]">
            {file ? <span><FileAudio className="mx-auto mb-2 h-8 w-8 text-[var(--k4)]" /><strong className="block max-w-sm truncate text-text">{file.name}</strong><span className="mt-1 block text-xs">{readableSize(file.size)} · cliquer pour remplacer</span></span> : <span><Upload className="mx-auto mb-2 h-8 w-8 text-[var(--k4)]" /><strong className="block text-text">Choisir un enregistrement</strong><span className="mt-1 block text-xs">Le fichier n’est traité qu’après confirmation.</span></span>}
          </button>

          <div className={`mt-4 rounded-[10px] border p-3 text-xs leading-5 ${usesLocalTranscription ? 'border-accent-cyan/30 bg-accent-tint text-accent' : 'border-warning/40 bg-[var(--color-warning-tint)] text-warning'}`}>
            <ShieldCheck className="mr-1 inline h-4 w-4" /><strong>{transcriptionEngine}</strong> · {usesLocalTranscription ? 'l’audio reste sur cette machine.' : 'le fichier sera envoyé à Groq après ta confirmation.'}
          </div>

          {confirmationOpen ? <div className="mt-4 rounded-[10px] border border-warning/40 bg-[var(--color-warning-tint)] p-3 text-xs text-warning" data-testid="voice-transcription-confirmation"><strong>Confirmer la transcription avec {transcriptionEngine} ?</strong><div className="mt-3 flex justify-end gap-2"><button type="button" onClick={() => setConfirmationOpen(false)} className="rounded-[8px] border border-border bg-surface px-3 py-2 font-semibold">Annuler</button><button type="button" onClick={() => void confirmTranscription()} className="rounded-[8px] bg-text px-3 py-2 font-semibold text-white">Confirmer et transcrire</button></div></div> : <button type="button" onClick={prepareTranscription} disabled={!file || transcribing} className="mt-4 inline-flex w-full items-center justify-center gap-2 rounded-[10px] bg-text px-4 py-3 text-sm font-semibold text-white disabled:opacity-50">{transcribing ? <Loader2 className="h-4 w-4 animate-spin" /> : <Mic className="h-4 w-4" />}{transcribing ? 'Transcription en cours…' : 'Préparer la transcription'}</button>}

          {error && <div role="alert" className="mt-3 rounded-[9px] border border-error/40 bg-[var(--color-error-tint)] p-3 text-xs text-error"><AlertCircle className="mr-1 inline h-4 w-4" />{error}</div>}

          {transcript && <div className="mt-5"><label className="text-xs font-semibold text-text">Transcription<textarea aria-label="Transcription" rows={8} value={transcript} onChange={(event) => setTranscript(event.target.value)} className="mt-2 w-full rounded-[10px] border border-border bg-surface p-3 text-sm font-normal leading-6 text-text" /></label><button type="button" onClick={() => onContinueInChat(`Voici la transcription d’un enregistrement :\n\n${transcript}\n\nExtrais les décisions, engagements et prochaines actions.`)} className="mt-3 w-full rounded-[9px] bg-[#7C3AED] px-4 py-2.5 text-xs font-semibold text-white">Analyser dans le chat</button></div>}
        </section>

        <section className="overflow-y-auto p-5">
          <h3 className="text-sm font-bold text-text">Lire un texte à voix haute</h3>
          <p className="mt-1 text-xs leading-5 text-text-muted">Synthèse locale Piper. Aucun texte n’est envoyé vers un service externe.</p>
          <label className="mt-4 block text-xs font-semibold text-text">Texte à lire<textarea aria-label="Texte à lire" rows={9} value={speechText} onChange={(event) => setSpeechText(event.target.value)} placeholder="Colle ici le texte à convertir en audio…" className="mt-2 w-full rounded-[10px] border border-border bg-surface p-3 text-sm font-normal leading-6 text-text" /></label>
          {!ttsReady && <div className="mt-3 rounded-[9px] border border-warning/40 bg-[var(--color-warning-tint)] p-3 text-xs leading-5 text-warning">La voix locale doit être activée dans Paramètres → Confidentialité avant d’utiliser la synthèse.</div>}
          <button type="button" onClick={() => void createSpeech()} disabled={!speechText.trim() || !ttsReady || speechLoading} className="mt-4 inline-flex w-full items-center justify-center gap-2 rounded-[10px] bg-text px-4 py-3 text-sm font-semibold text-white disabled:opacity-50">{speechLoading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Volume2 className="h-4 w-4" />}{speechLoading ? 'Création de l’audio…' : 'Générer l’audio local'}</button>
          {speechUrl && <div className="mt-5 rounded-[12px] border border-border bg-surface p-4"><div className="mb-3 flex items-center gap-2 text-xs font-semibold text-text"><Play className="h-4 w-4 text-[var(--k4)]" />Audio généré localement</div><audio controls src={speechUrl} className="w-full" /><a href={speechUrl} download="therese-tts.wav" className="mt-3 inline-flex rounded-[8px] border border-text px-3 py-2 text-xs font-semibold text-text">Enregistrer le WAV</a></div>}
        </section>
      </div>
    </aside>
  );
}
