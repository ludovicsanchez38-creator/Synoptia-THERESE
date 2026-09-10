// Onglet "À propos" - Version actuelle + Vérification des mises à jour
// Utilise le même plugin Tauri que le bandeau pour ne jamais comparer deux sources.

import { useState, useEffect } from 'react';
import { RefreshCw, CheckCircle, ExternalLink, Info, MessageSquareWarning } from 'lucide-react';
import { Button } from '../ui/Button';
import { useBackendStore } from '../../hooks/useBackend';
import { checkHealth } from '../../services/api';


// US-012 : invitation Discord alpha PERMANENTE (revue adversariale : l'URL
// vanity discord.gg/therese-alpha n'existait pas - Unknown Invite. Celle-ci
// est créée par le bot Thérèse sur la guilde THÉRÈSE - Alpha, sans expiration).
const DISCORD_URL = 'https://discord.gg/krDGArdbH8';

type UpdateStatus = 'idle' | 'checking' | 'up-to-date' | 'update-available' | 'error';

export function AboutTab() {
  const version = useBackendStore((s) => s.version);
  const [updateStatus, setUpdateStatus] = useState<UpdateStatus>('idle');
  const [latestVersion, setLatestVersion] = useState<string | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  // Fetch la version si elle n'est pas encore disponible (panels Tauri = contexte JS séparé)
  useEffect(() => {
    if (!version) {
      checkHealth()
        .then((health) => {
          useBackendStore.getState().setConnected(health);
        })
        .catch(() => {});
    }
  }, [version]);

  async function checkForUpdates() {
    setUpdateStatus('checking');
    setErrorMsg(null);

    try {
      if (!('__TAURI__' in window)) {
        throw new Error('La vérification des mises à jour est disponible dans l’application installée.');
      }
      // BUG-178 : GitHub et Tauri n'avaient pas le même manifeste ni le même
      // circuit d'installation. Les réglages interrogent désormais exactement
      // le plugin consommé par UpdateBanner.
      const { check } = await import('@tauri-apps/plugin-updater');
      const update = await check();
      if (update?.available) {
        setLatestVersion(update.version);
        setUpdateStatus('update-available');
      } else {
        setLatestVersion(null);
        setUpdateStatus('up-to-date');
      }
    } catch (err) {
      setErrorMsg(err instanceof Error ? err.message : 'Erreur inconnue');
      setUpdateStatus('error');
    }
  }


  function openDownload(url: string) {
    // return open(url) : propage le rejet d'open() au catch (hors Tauri,
    // open() rejette en async - sans le return, le fallback ne tournait jamais)
    import('@tauri-apps/plugin-shell').then(({ open }) => {
      return open(url);
    }).catch(() => {
      window.open(url, '_blank');
    });
  }

  return (
    <div className="space-y-6">
      {/* Version actuelle */}
      <div className="bg-surface/50 rounded-md p-5 border border-border/30">
        <div className="flex items-center gap-3 mb-4">
          <div className="w-10 h-10 rounded-sm bg-accent-fill border-[1.5px] border-[var(--btn-ink)] flex items-center justify-center">
            <span className="text-lg font-bold text-accent-ink">T</span>
          </div>
          <div>
            <h3 className="text-lg font-semibold text-text">THÉRÈSE</h3>
            <p className="text-sm text-text-muted">L'assistante souveraine des entrepreneurs français</p>
          </div>
        </div>

        <div className="grid grid-cols-2 gap-3 text-sm">
          <div className="bg-bg/50 rounded-md px-3 py-2">
            <span className="text-text-muted">Version</span>
            <span className="ml-2 text-text font-mono">{version || '...'}</span>
          </div>
          <div className="bg-bg/50 rounded-md px-3 py-2">
            <span className="text-text-muted">Phase</span>
            <span className="ml-2 text-accent-cyan-ink font-medium">Alpha</span>
          </div>
        </div>
      </div>

      {/* Sélecteur réversible de l'interface, appliqué au prochain bootstrap. */}

      {/* US-012 : communauté et retours - le testeur alpha doit pouvoir
          signaler un bug sans connaître l'URL Discord par coeur */}
      <div className="bg-surface/50 rounded-md p-5 border border-border/30">
        <h4 className="text-sm font-medium text-text mb-3 flex items-center gap-2">
          <MessageSquareWarning className="w-4 h-4 text-accent-cyan-ink" />
          Un bug ? Une idée ?
        </h4>
        <p className="text-sm text-text-muted mb-3">
          La communauté alpha vit sur Discord : signale les bugs dans
          <span className="text-text font-medium"> #bugs</span>, propose tes idées dans
          <span className="text-text font-medium"> #feedback</span>.
        </p>
        <Button
          variant="secondary"
          onClick={() => openDownload(DISCORD_URL)}
          className="w-full justify-center"
          data-testid="discord-feedback-btn"
        >
          <ExternalLink className="w-4 h-4 mr-2" />
          Rejoindre le Discord / Signaler un bug
        </Button>
      </div>

      {/* Vérification des mises à jour */}
      <div className="bg-surface/50 rounded-md p-5 border border-border/30">
        <h4 className="text-sm font-medium text-text mb-3 flex items-center gap-2">
          <RefreshCw className="w-4 h-4 text-accent-cyan-ink" />
          Mises à jour
        </h4>

        <div className="space-y-3">
          <Button
            variant="secondary"
            onClick={checkForUpdates}
            disabled={updateStatus === 'checking'}
            className="w-full justify-center"
          >
            {updateStatus === 'checking' ? (
              <>
                <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
                Vérification...
              </>
            ) : (
              <>
                <RefreshCw className="w-4 h-4 mr-2" />
                Vérifier les mises à jour
              </>
            )}
          </Button>

          {/* Résultat : à jour */}
          {updateStatus === 'up-to-date' && (
            <div className="flex items-center gap-2 text-sm text-success bg-[var(--color-success-tint)] rounded-md px-3 py-2">
              <CheckCircle className="w-4 h-4" />
              THÉRÈSE est à jour (v{version})
            </div>
          )}

          {/* Résultat : mise à jour disponible */}
          {updateStatus === 'update-available' && latestVersion && (
            <div className="space-y-3">
              <div className="bg-accent-cyan/10 border border-accent-cyan/30 rounded-md p-3">
                <p className="text-sm text-accent-cyan-ink font-medium mb-1">
                  Nouvelle version disponible : {latestVersion}
                </p>
                <p className="text-xs text-text-muted">
                  Le bandeau de mise à jour utilise ce même résultat pour télécharger et installer la version.
                </p>
              </div>

              <div className="flex items-center gap-2 text-xs text-text-muted bg-bg/50 rounded-md px-3 py-2">
                <Info className="w-3.5 h-3.5 shrink-0" />
                Tes données sont conservées lors de la mise à jour (dossier ~/.therese/).
              </div>


            </div>
          )}

          {/* Résultat : erreur */}
          {updateStatus === 'error' && (
            <div className="text-sm text-error bg-[var(--color-error-tint)] rounded-md px-3 py-2">
              Impossible de vérifier : {errorMsg}
            </div>
          )}
        </div>
      </div>

      {/* Crédits */}
      <div className="text-center text-xs text-text-muted space-y-1">
        <p>Synoptia SARL-U - Manosque, France</p>
        <p>"Humain d'abord - IA en soutien"</p>
      </div>
    </div>
  );
}
