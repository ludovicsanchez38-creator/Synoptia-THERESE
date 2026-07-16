import { useEffect, useMemo, useRef, useState } from 'react';
import {
  AlertCircle,
  Download,
  Image as ImageIcon,
  Loader2,
  PanelRightClose,
  RefreshCw,
  ShieldCheck,
  Sparkles,
} from 'lucide-react';
import {
  downloadGeneratedImage,
  generateImage,
  getImageDownloadUrl,
  getImageStatus,
  listGeneratedImages,
  type ImageProvider,
  type ImageGenerateRequest,
  type ImageProviderStatus,
  type ImageResponse,
} from '../../services/api/images';
import { getCloudConsent, recordCloudConsent } from '../../lib/consent';
import { useDialogFocusTrap } from '../../hooks/useDialogFocusTrap';

const PROVIDERS: Array<{ id: ImageProvider; label: string; availability: keyof ImageProviderStatus }> = [
  { id: 'gpt-image-2', label: 'GPT Image 2', availability: 'openai_available' },
  { id: 'nanobanan-pro', label: 'Nano Banana', availability: 'gemini_available' },
  { id: 'fal-flux-pro', label: 'Fal Flux Pro', availability: 'fal_available' },
];

interface ImageGenerationSnapshot {
  request: Required<Pick<ImageGenerateRequest, 'prompt' | 'provider' | 'size' | 'quality'>>;
  providerLabel: string;
}

function formatDate(value: string): string {
  const date = new Date(value);
  return Number.isNaN(date.getTime())
    ? 'Date inconnue'
    : date.toLocaleString('fr-FR', { dateStyle: 'medium', timeStyle: 'short' });
}

export function ImagesWorkspaceCanvas({ onClose }: { onClose: () => void }) {
  const [providerStatus, setProviderStatus] = useState<ImageProviderStatus | null>(null);
  const [images, setImages] = useState<ImageResponse[]>([]);
  const [provider, setProvider] = useState<ImageProvider>('gpt-image-2');
  const [prompt, setPrompt] = useState('');
  const [size, setSize] = useState<'1024x1024' | '1536x1024' | '1024x1536'>('1024x1024');
  const [quality, setQuality] = useState<'low' | 'medium' | 'high'>('medium');
  const [loading, setLoading] = useState(true);
  const [pending, setPending] = useState(false);
  const [confirmationSnapshot, setConfirmationSnapshot] = useState<ImageGenerationSnapshot | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [errorField, setErrorField] = useState<'prompt' | 'provider' | null>(null);
  const [errorContext, setErrorContext] = useState<'load' | 'generation' | null>(null);
  const [downloadError, setDownloadError] = useState<string | null>(null);
  const [selected, setSelected] = useState<ImageResponse | null>(null);
  const generationLocked = useRef(false);
  const dialogRef = useRef<HTMLElement>(null);
  const confirmationRef = useRef<HTMLDivElement>(null);
  useDialogFocusTrap(dialogRef, { active: true, onEscape: onClose, isolateBackground: true });

  // La confirmation d'une action payante remplace le bouton en bas de la colonne
  // scrollable : à 1280×900 elle naissait sous le pli (finding Codex CODEX-09).
  // On l'amène à l'écran dès qu'elle apparaît pour qu'Annuler / Confirmer soient
  // visibles sans deviner qu'il faut faire défiler.
  useEffect(() => {
    if (confirmationSnapshot) {
      confirmationRef.current?.scrollIntoView?.({ behavior: 'smooth', block: 'nearest' });
    }
  }, [confirmationSnapshot]);

  async function refresh() {
    setLoading(true);
    setError(null);
    setErrorField(null);
    setErrorContext(null);
    try {
      const [status, history] = await Promise.all([getImageStatus(), listGeneratedImages(50)]);
      setProviderStatus(status);
      setImages(history.images);
      setSelected((current) => current ?? history.images[0] ?? null);
      const active = PROVIDERS.find((item) => item.id === status.active_provider && status[item.availability]);
      const firstAvailable = PROVIDERS.find((item) => status[item.availability]);
      if (active || firstAvailable) setProvider((active || firstAvailable)!.id);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : 'Impossible de charger le studio Images.');
      setErrorContext('load');
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void refresh();
  }, []);

  const activeProvider = useMemo(
    () => PROVIDERS.find((item) => item.id === provider) ?? PROVIDERS[0],
    [provider],
  );

  function requestGeneration() {
    if (prompt.trim().length < 8) {
      setError('Décris le visuel en au moins 8 caractères.');
      setErrorField('prompt');
      setErrorContext(null);
      requestAnimationFrame(() => document.getElementById('image-prompt')?.focus());
      return;
    }
    if (!providerStatus?.[activeProvider.availability]) {
      setError(`Le moteur ${activeProvider.label} n’est pas configuré.`);
      setErrorField('provider');
      setErrorContext(null);
      requestAnimationFrame(() => document.getElementById(`image-provider-${provider}`)?.focus());
      return;
    }
    setError(null);
    setErrorField(null);
    setErrorContext(null);
    setConfirmationSnapshot({
      request: { prompt: prompt.trim(), provider, size, quality },
      providerLabel: activeProvider.label,
    });
  }

  async function confirmGeneration() {
    if (generationLocked.current) return;
    if (!confirmationSnapshot) return;
    const snapshot = confirmationSnapshot;
    const snapshotProvider = PROVIDERS.find((item) => item.id === snapshot.request.provider);
    if (snapshot.request.prompt.trim().length < 8 || !snapshotProvider || !providerStatus?.[snapshotProvider.availability]) {
      setError('L’instantané de génération n’est plus valide. Reprends la préparation.');
      setErrorContext('generation');
      setConfirmationSnapshot(null);
      return;
    }
    generationLocked.current = true;
    setPending(true);
    setConfirmationSnapshot(null);
    setError(null);
    setErrorField(null);
    setErrorContext(null);
    try {
      if (!getCloudConsent()?.accepted) {
        recordCloudConsent(undefined, {
          provider: snapshot.providerLabel,
          dataCategories: ['description du visuel', 'format', 'qualité'],
        });
      }
      const created = await generateImage(snapshot.request);
      setImages((current) => [created, ...current.filter((image) => image.id !== created.id)]);
      setSelected(created);
      setPrompt('');
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : 'La génération a échoué.');
      setErrorContext('generation');
    } finally {
      generationLocked.current = false;
      setPending(false);
    }
  }

  async function saveSelectedImage() {
    if (!selected) return;
    setDownloadError(null);
    try {
      await downloadGeneratedImage(selected.id);
    } catch (reason) {
      setDownloadError(reason instanceof Error ? reason.message : 'L’image n’a pas pu être enregistrée.');
    }
  }

  return (
    <aside ref={dialogRef} role="dialog" aria-modal="true" aria-labelledby="images-workspace-title" tabIndex={-1} className="absolute inset-y-0 right-0 z-20 flex h-full w-full flex-col border-l border-border bg-surface-2 shadow-[-18px_0_45px_rgba(16,28,54,0.12)] xl:w-[62%] xl:min-w-[720px]" data-testid="images-workspace-canvas">
      <header className="flex shrink-0 items-start gap-3 border-b border-border bg-surface px-5 py-4 pr-16">
        <span className="grid h-9 w-9 place-items-center rounded-[10px] border border-text bg-[var(--k3bg)] text-[var(--k3)] shadow-[2px_2px_0_var(--btn-shadow-color)]"><ImageIcon className="h-4 w-4" /></span>
        <div>
          <h2 id="images-workspace-title" data-dialog-autofocus tabIndex={-1} className="text-lg font-bold text-text outline-none">Studio Images</h2>
          <p className="mt-0.5 text-xs text-text-muted">Génération réelle, aperçu local et historique conservé.</p>
        </div>
        <button type="button" onClick={onClose} aria-label="Fermer le studio Images" className="absolute right-3 top-3 grid h-11 w-11 place-items-center rounded-[9px] border border-border bg-surface text-text-muted"><PanelRightClose className="h-4 w-4" /></button>
      </header>

      <div className="grid min-h-0 flex-1 lg:grid-cols-[minmax(300px,0.8fr)_minmax(360px,1.2fr)]">
        <section className="overflow-y-auto border-r border-border p-5">
          <h3 className="text-sm font-bold text-text">Nouveau visuel</h3>
          <fieldset disabled={confirmationSnapshot !== null} onChangeCapture={() => setConfirmationSnapshot(null)} className="contents disabled:opacity-70" data-testid="image-generation-fields">
          <label className="mt-4 block text-xs font-semibold text-text">Description
            <textarea id="image-prompt" aria-label="Description du visuel" aria-invalid={errorField === 'prompt'} aria-describedby={errorField === 'prompt' ? 'image-generation-error' : undefined} value={prompt} onChange={(event) => { setPrompt(event.target.value); if (errorField === 'prompt') { setError(null); setErrorField(null); } }} rows={6} placeholder="Décris le sujet, la composition, le style et ce qui ne doit pas apparaître…" className="mt-2 w-full resize-y rounded-[10px] border border-border bg-surface p-3 text-sm font-normal leading-6 text-text outline-none focus:border-accent" />
          </label>

          <fieldset className="mt-4">
            <legend className="text-xs font-semibold text-text">Moteur</legend>
            <div className="mt-2 grid gap-2">
              {PROVIDERS.map((item) => {
                const available = Boolean(providerStatus?.[item.availability]);
                return <label key={item.id} className={`flex items-center gap-2 rounded-[9px] border px-3 py-2 text-xs ${provider === item.id ? 'border-text bg-surface text-text' : 'border-border text-text-muted'} ${available ? '' : 'opacity-50'}`}><input id={`image-provider-${item.id}`} type="radio" name="image-provider" value={item.id} checked={provider === item.id} disabled={!available} aria-invalid={errorField === 'provider' && provider === item.id} aria-describedby={errorField === 'provider' && provider === item.id ? 'image-generation-error' : undefined} onChange={() => { setProvider(item.id); setErrorField(null); setError(null); }} /><span className="font-semibold">{item.label}</span><span className="ml-auto text-xs">{available ? 'disponible' : 'non configuré'}</span></label>;
              })}
            </div>
          </fieldset>

          <div className="mt-4 grid grid-cols-2 gap-3">
            <label className="text-xs font-semibold text-text">Format<select aria-label="Format de l’image" value={size} onChange={(event) => setSize(event.target.value as typeof size)} className="mt-2 w-full rounded-[9px] border border-border bg-surface px-3 py-2 font-normal"><option value="1024x1024">Carré</option><option value="1536x1024">Paysage</option><option value="1024x1536">Portrait</option></select></label>
            <label className="text-xs font-semibold text-text">Qualité<select aria-label="Qualité de l’image" value={quality} onChange={(event) => setQuality(event.target.value as typeof quality)} className="mt-2 w-full rounded-[9px] border border-border bg-surface px-3 py-2 font-normal"><option value="low">Économique</option><option value="medium">Standard</option><option value="high">Haute</option></select></label>
          </div>

          <div className="mt-4 rounded-[10px] border border-accent-cyan/30 bg-accent-tint p-3 text-xs leading-5 text-accent"><ShieldCheck className="mr-1 inline h-4 w-4" />La demande sera transmise au moteur choisi. Rien ne part avant confirmation.</div>
          </fieldset>
          {error && <div id="image-generation-error" role="alert" className="mt-3 rounded-[9px] border border-error/40 bg-[var(--color-error-tint)] p-3 text-sm text-error"><p><AlertCircle className="mr-1 inline h-4 w-4" />{error}</p>{errorContext && <button type="button" onClick={() => errorContext === 'load' ? void refresh() : requestGeneration()} className="mt-2 rounded-md border border-error px-3 py-2 font-semibold">Réessayer</button>}</div>}
          {confirmationSnapshot ? <div ref={confirmationRef} className="mt-4 rounded-[10px] border border-warning/40 bg-[var(--color-warning-tint)] p-3 text-xs text-warning" data-testid="image-generation-confirmation"><strong>Confirmer la génération avec {confirmationSnapshot.providerLabel} ?</strong><p className="mt-1 font-semibold">Prompt : {confirmationSnapshot.request.prompt}</p><p>Format {confirmationSnapshot.request.size}, qualité {confirmationSnapshot.request.quality}. Cette action peut consommer un crédit du fournisseur.</p>{!getCloudConsent()?.accepted && <p className="mt-1">En confirmant ce premier usage cloud, tu consens à transmettre ces données à {confirmationSnapshot.providerLabel}.</p>}<div className="mt-3 flex justify-end gap-2"><button type="button" onClick={() => setConfirmationSnapshot(null)} className="rounded-[8px] border border-border bg-surface px-3 py-2 font-semibold">Annuler</button><button type="button" onClick={() => void confirmGeneration()} disabled={pending} className="rounded-[8px] bg-text px-3 py-2 font-semibold text-white">Confirmer et générer</button></div></div> : <button type="button" onClick={requestGeneration} disabled={pending || loading} className="mt-4 inline-flex w-full items-center justify-center gap-2 rounded-[10px] bg-text px-4 py-3 text-sm font-semibold text-white disabled:opacity-50">{pending ? <Loader2 className="h-4 w-4 animate-spin" /> : <Sparkles className="h-4 w-4" />}{pending ? 'Génération en cours…' : 'Préparer la génération'}</button>}
        </section>

        <section className="min-h-0 overflow-y-auto p-5">
          <div className="flex items-center justify-between gap-3"><div><h3 className="text-sm font-bold text-text">Historique réel</h3><p className="mt-0.5 text-xs text-text-muted">{images.length} image{images.length > 1 ? 's' : ''} chargée{images.length > 1 ? 's' : ''} sur 50 maximum</p></div><button type="button" onClick={() => void refresh()} disabled={loading} className="grid h-11 w-11 place-items-center rounded-[8px] border border-border bg-surface text-text-muted" aria-label="Actualiser l’historique"><RefreshCw className={`h-3.5 w-3.5 ${loading ? 'animate-spin' : ''}`} /></button></div>
          {loading ? <div className="grid min-h-64 place-items-center text-sm text-text-muted" role="status"><Loader2 className="mb-2 h-5 w-5 animate-spin" />Chargement des images…</div> : images.length === 0 ? <div className="mt-5 grid min-h-64 place-items-center rounded-[13px] border border-dashed border-border bg-surface text-center text-sm text-text-muted"><div><ImageIcon className="mx-auto mb-2 h-8 w-8 opacity-40" />Aucune image générée pour le moment.</div></div> : <><div className="mt-4 grid grid-cols-2 gap-3 sm:grid-cols-3" aria-label="Historique des images">{images.map((image) => <button key={image.id} type="button" aria-pressed={selected?.id === image.id} onClick={() => { setSelected(image); setDownloadError(null); }} className={`overflow-hidden rounded-[11px] border bg-surface text-left ${selected?.id === image.id ? 'border-text ring-2 ring-accent/30' : 'border-border'}`}><img src={getImageDownloadUrl(image.id)} alt={image.prompt} className="aspect-square w-full object-cover" /><span className="block truncate px-2 py-2 text-xs font-medium text-text">{image.prompt}</span></button>)}</div>{selected && <div className="mt-4 rounded-[13px] border border-border bg-surface p-4" data-testid="selected-generated-image"><img src={getImageDownloadUrl(selected.id)} alt={selected.prompt} className="max-h-[420px] w-full rounded-[9px] object-contain" /><div className="mt-3 flex items-start gap-3"><div className="min-w-0 flex-1"><p className="text-sm font-semibold leading-5 text-text">{selected.prompt}</p><p className="mt-1 text-xs text-text-muted">{selected.provider} · {formatDate(selected.created_at)}</p></div><button type="button" onClick={() => void saveSelectedImage()} className="inline-flex min-h-11 shrink-0 items-center gap-1.5 rounded-[8px] border border-text bg-surface px-3 py-2 text-sm font-semibold text-text"><Download className="h-3.5 w-3.5" />Enregistrer</button></div>{downloadError && <div role="alert" className="mt-3 rounded-[9px] border border-error/40 bg-[var(--color-error-tint)] p-3 text-sm text-error"><p>{downloadError}</p><button type="button" onClick={() => void saveSelectedImage()} className="mt-2 rounded-md border border-error px-3 py-2 font-semibold">Réessayer</button></div>}</div>}</>}
        </section>
      </div>
    </aside>
  );
}
