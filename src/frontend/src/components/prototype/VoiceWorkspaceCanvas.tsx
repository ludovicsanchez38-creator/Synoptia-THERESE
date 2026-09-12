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
import { Alerte, Button, Carte, Textarea } from '../ui';
import { Spinner } from '../ui/Spinner';

const AUDIO_PERIME_MESSAGE =
  'L’audio correspondait au texte précédent. Génère-le à nouveau pour entendre la nouvelle version.';

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

  function updateSpeechText(value: string) {
    if (speechUrl) {
      setSpeechUrl(null);
      setSpeechStatus(AUDIO_PERIME_MESSAGE);
    }
    setSpeechError(null);
    setSpeechText(value);
  }

  return (
    <aside ref={dialogRef} role="region" aria-labelledby="voice-workspace-title" tabIndex={-1} className="absolute inset-y-0 right-0 z-20 flex h-full w-full flex-col border-l border-border bg-surface-2 shadow-lg sm:w-[calc(100%-48px)] xl:relative xl:w-[62%] xl:min-w-[720px] xl:shadow-none" data-testid="voice-workspace-canvas">
      <header className="relative shrink-0 border-b border-border bg-surface px-5 py-4 pr-16">
        <div className="flex items-start gap-3"><span className="grid h-9 w-9 place-items-center rounded-md border border-border bg-domaine-prospects-tint text-domaine-prospects shadow-sm"><Mic className="h-4 w-4" /></span><div><h2 id="voice-workspace-title" data-dialog-autofocus tabIndex={-1} className="text-lg font-bold text-text outline-none">Voix et transcription</h2><p className="mt-0.5 text-xs text-text-muted">Importer un enregistrement, le transcrire, puis poursuivre dans le chat.</p></div></div>
        <Button type="button" variant="secondary" size="icon" onClick={onClose} aria-label="Fermer l’espace Voix" className="absolute right-3 top-3 text-text-muted"><PanelRightClose className="h-[18px] w-[18px]" /></Button>
      </header>

      {statusError && <Alerte ton="attention" className="mx-4 mt-3" titre="Statut vocal indisponible" action={<Button type="button" variant="secondary" onClick={() => void loadStatus()}>Réessayer</Button>}>{statusError}</Alerte>}

      <div className="grid min-h-0 flex-1 lg:grid-cols-2">
        <section className="overflow-y-auto border-r border-border p-5">
          <h3 className="text-sm font-bold text-text">Transcrire un fichier</h3>
          <p className="mt-1 text-xs leading-5 text-text-muted">MP3, M4A, WAV, WebM et autres formats audio reconnus.</p>
          <input ref={fileInputRef} type="file" accept="audio/*,.m4a" className="hidden" onChange={(event) => selectFile(event.target.files?.[0] ?? null)} />
          <button type="button" onClick={() => fileInputRef.current?.click()} className="mt-4 flex min-h-32 w-full items-center justify-center rounded-md border border-dashed border-border bg-surface p-5 text-center text-sm text-text-muted transition-colors hover:border-domaine-prospects hover:bg-surface-2">
            {file ? <span><FileAudio className="mx-auto mb-2 h-8 w-8 text-domaine-prospects" /><strong className="block max-w-sm truncate text-text">{file.name}</strong><span className="mt-1 block text-sm">{readableSize(file.size)} · cliquer pour remplacer</span></span> : <span><Upload className="mx-auto mb-2 h-8 w-8 text-domaine-prospects" /><strong className="block text-text">Choisir un enregistrement</strong><span className="mt-1 block text-sm">Le fichier n’est traité qu’après confirmation.</span></span>}
          </button>

          <div className={`mt-4 rounded-md border p-3 text-sm leading-5 ${usesLocalTranscription ? 'border-accent-cyan/30 bg-accent-tint text-accent' : 'border-warning/40 bg-[var(--color-warning-tint)] text-warning'}`}>
            <ShieldCheck className="mr-1 inline h-4 w-4" /><strong>{transcriptionEngine}</strong> · {usesLocalTranscription ? 'l’audio reste sur cette machine.' : 'le fichier sera envoyé à Groq après ta confirmation.'}
          </div>

          {confirmationOpen ? <Alerte ton="attention" className="mt-4" data-testid="voice-transcription-confirmation" titre={`Confirmer la transcription avec ${transcriptionEngine} ?`} action={<div className="flex flex-wrap justify-end gap-2"><Button type="button" variant="secondary" onClick={() => setConfirmationOpen(false)}>Annuler</Button><Button type="button" onClick={() => void confirmTranscription()}>Confirmer et transcrire</Button></div>} /> : <Button type="button" size="lg" onClick={prepareTranscription} disabled={!file || transcribing} className="mt-4 w-full">{transcribing ? <Spinner taille="bouton" /> : <Mic className="h-4 w-4" />}{transcribing ? 'Transcription en cours…' : 'Préparer la transcription'}</Button>}

          {transcriptionError && <Alerte className="mt-3" titre="Transcription impossible" icone={<AlertCircle className="h-4 w-4" />} action={<Button type="button" variant="secondary" onClick={prepareTranscription}>Réessayer</Button>}>{transcriptionError}</Alerte>}

          {transcript && <div className="mt-5"><label className="text-sm font-semibold text-text">Transcription<Textarea aria-label="Transcription" rows={8} value={transcript} onChange={(event) => setTranscript(event.target.value)} className="mt-2 font-normal leading-6" /></label><Button type="button" size="lg" onClick={() => onContinueInChat(`Voici la transcription d’un enregistrement :\n\n${transcript}\n\nExtrais les décisions, engagements et prochaines actions.`)} className="mt-3 w-full">Analyser dans le chat</Button></div>}
        </section>

        <section className="overflow-y-auto p-5">
          <h3 className="text-sm font-bold text-text">Lire un texte à voix haute</h3>
          <p className="mt-1 text-xs leading-5 text-text-muted">Synthèse locale Piper. Aucun texte n’est envoyé vers un service externe.</p>
          <label className="mt-4 block text-sm font-semibold text-text">Texte à lire<Textarea aria-label="Texte à lire" rows={9} value={speechText} onChange={(event) => updateSpeechText(event.target.value)} placeholder="Colle ici le texte à convertir en audio…" className="mt-2 font-normal leading-6" /></label>
          {!ttsReady && <Alerte ton="attention" className="mt-3" titre="Voix locale à activer">La voix locale doit être activée dans Paramètres → Confidentialité avant d’utiliser la synthèse.</Alerte>}
          <Button type="button" size="lg" onClick={() => void createSpeech()} disabled={!speechText.trim() || !ttsReady || speechLoading} className="mt-4 w-full">{speechLoading ? <Spinner taille="bouton" /> : <Volume2 className="h-4 w-4" />}{speechLoading ? 'Création de l’audio…' : 'Générer l’audio local'}</Button>
          {speechStatus && <p role="status" className="mt-3 rounded-md border border-info/40 bg-[var(--color-info-tint)] p-3 text-sm text-info">{speechStatus}</p>}
          {speechError && <Alerte className="mt-3" titre="Synthèse vocale impossible" icone={<AlertCircle className="h-4 w-4" />} action={<Button type="button" variant="secondary" onClick={() => void createSpeech()}>Réessayer</Button>}>{speechError}</Alerte>}
          {speechUrl && <Carte className="mt-5 p-4"><div className="mb-3 flex items-center gap-2 text-sm font-semibold text-text"><Play className="h-4 w-4 text-domaine-prospects" />Audio généré localement</div><audio controls src={speechUrl} className="w-full" /><a href={speechUrl} download="therese-tts.wav" className="mt-3 inline-flex min-h-9 items-center rounded-md border border-border bg-surface px-4 py-2 text-sm font-semibold text-text hover:bg-surface-2">Enregistrer le WAV</a></Carte>}
        </section>
      </div>
    </aside>
  );
}
