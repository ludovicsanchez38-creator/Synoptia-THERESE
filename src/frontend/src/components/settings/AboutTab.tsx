// Onglet "À propos" - Version actuelle + Vérification des mises à jour
// Vérifie les releases GitHub et propose le téléchargement si nouvelle version disponible

import { useState } from 'react';
import { RefreshCw, Download, CheckCircle, ExternalLink, Info } from 'lucide-react';
import { Button } from '../ui/Button';
import { useBackendStore } from '../../hooks/useBackend';

const GITHUB_REPO = 'ludovicsanchez38-creator/Synoptia-THERESE';
const RELEASES_URL = `https://github.com/${GITHUB_REPO}/releases`;

interface ReleaseInfo {
  tag_name: string;
  name: string;
  html_url: string;
  published_at: string;
  body: string;
  assets: { name: string; browser_download_url: string; size: number }[];
}

type UpdateStatus = 'idle' | 'checking' | 'up-to-date' | 'update-available' | 'error';

function compareVersions(current: string, latest: string): number {
  // Nettoyer les préfixes (v, alpha, etc.)
  const clean = (v: string) => v.replace(/^v/, '').replace(/-alpha.*$/, '');
  const a = clean(current).split('.').map(Number);
  const b = clean(latest).split('.').map(Number);
  for (let i = 0; i < Math.max(a.length, b.length); i++) {
    const diff = (b[i] || 0) - (a[i] || 0);
    if (diff !== 0) return diff;
  }
  return 0;
}

function formatBytes(bytes: number): string {
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(0)} Ko`;
  return `${(bytes / (1024 * 1024)).toFixed(0)} Mo`;
}

function getPlatformAsset(assets: ReleaseInfo['assets']): ReleaseInfo['assets'][0] | null {
  const platform = navigator.platform.toLowerCase();
  if (platform.includes('mac')) {
    return assets.find(a => a.name.endsWith('.dmg')) || null;
  }
  if (platform.includes('win')) {
    return assets.find(a => a.name.endsWith('.msi') || a.name.endsWith('.exe')) || null;
  }
  // Linux
  return assets.find(a => a.name.endsWith('.AppImage') || a.name.endsWith('.deb')) || null;
}

export function AboutTab() {
  const version = useBackendStore((s) => s.version);
  const [updateStatus, setUpdateStatus] = useState<UpdateStatus>('idle');
  const [latestRelease, setLatestRelease] = useState<ReleaseInfo | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  async function checkForUpdates() {
    setUpdateStatus('checking');
    setErrorMsg(null);

    try {
      const response = await fetch(
        `https://api.github.com/repos/${GITHUB_REPO}/releases`,
        { headers: { Accept: 'application/vnd.github.v3+json' } }
      );

      if (!response.ok) {
        throw new Error(`GitHub API : ${response.status}`);
      }

      const releases: ReleaseInfo[] = await response.json();
      if (!releases.length) {
        throw new Error('Aucune release trouvée');
      }

      // Prendre la première release (la plus récente, y compris pre-release)
      const latest = releases[0];
      setLatestRelease(latest);

      const currentVersion = version || '0.0.0';
      if (compareVersions(currentVersion, latest.tag_name) > 0) {
        setUpdateStatus('update-available');
      } else {
        setUpdateStatus('up-to-date');
      }
    } catch (err) {
      setErrorMsg(err instanceof Error ? err.message : 'Erreur inconnue');
      setUpdateStatus('error');
    }
  }

  function openReleasePage() {
    // Utiliser le shell Tauri pour ouvrir dans le navigateur
    import('@tauri-apps/plugin-shell').then(({ open }) => {
      open(latestRelease?.html_url || RELEASES_URL);
    }).catch(() => {
      window.open(latestRelease?.html_url || RELEASES_URL, '_blank');
    });
  }

  function openDownload(url: string) {
    import('@tauri-apps/plugin-shell').then(({ open }) => {
      open(url);
    }).catch(() => {
      window.open(url, '_blank');
    });
  }

  const platformAsset = latestRelease ? getPlatformAsset(latestRelease.assets) : null;

  return (
    <div className="space-y-6">
      {/* Version actuelle */}
      <div className="bg-surface/50 rounded-lg p-5 border border-border/30">
        <div className="flex items-center gap-3 mb-4">
          <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-accent-cyan to-accent-magenta flex items-center justify-center">
            <span className="text-lg font-bold text-white">T</span>
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
            <span className="ml-2 text-accent-cyan font-medium">Alpha</span>
          </div>
        </div>
      </div>

      {/* Vérification des mises à jour */}
      <div className="bg-surface/50 rounded-lg p-5 border border-border/30">
        <h4 className="text-sm font-medium text-text mb-3 flex items-center gap-2">
          <RefreshCw className="w-4 h-4 text-accent-cyan" />
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
            <div className="flex items-center gap-2 text-sm text-green-400 bg-green-500/10 rounded-md px-3 py-2">
              <CheckCircle className="w-4 h-4" />
              THÉRÈSE est à jour (v{version})
            </div>
          )}

          {/* Résultat : mise à jour disponible */}
          {updateStatus === 'update-available' && latestRelease && (
            <div className="space-y-3">
              <div className="bg-accent-cyan/10 border border-accent-cyan/30 rounded-md p-3">
                <p className="text-sm text-accent-cyan font-medium mb-1">
                  Nouvelle version disponible : {latestRelease.tag_name}
                </p>
                <p className="text-xs text-text-muted">
                  {latestRelease.name || latestRelease.tag_name}
                  {latestRelease.published_at && (
                    <> - {new Date(latestRelease.published_at).toLocaleDateString('fr-FR')}</>
                  )}
                </p>
              </div>

              <div className="flex items-center gap-2 text-xs text-text-muted bg-bg/50 rounded-md px-3 py-2">
                <Info className="w-3.5 h-3.5 shrink-0" />
                Vos données sont conservées lors de la mise à jour (dossier ~/.therese/).
              </div>

              {/* Bouton téléchargement direct pour la plateforme */}
              {platformAsset && (
                <Button
                  variant="primary"
                  onClick={() => openDownload(platformAsset.browser_download_url)}
                  className="w-full justify-center"
                >
                  <Download className="w-4 h-4 mr-2" />
                  Télécharger {platformAsset.name} ({formatBytes(platformAsset.size)})
                </Button>
              )}

              {/* Lien vers la page des releases */}
              <Button
                variant="ghost"
                onClick={openReleasePage}
                className="w-full justify-center text-text-muted"
              >
                <ExternalLink className="w-4 h-4 mr-2" />
                Voir toutes les versions sur GitHub
              </Button>
            </div>
          )}

          {/* Résultat : erreur */}
          {updateStatus === 'error' && (
            <div className="text-sm text-red-400 bg-red-500/10 rounded-md px-3 py-2">
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
