import { setAutomaticUpdateChecks, useAutomaticUpdateChecks } from '../../lib/updatePreference';
// Onglet "À propos" - Version actuelle + Vérification des mises à jour
// Vérifie les releases GitHub et propose le téléchargement si nouvelle version disponible

import { useState, useEffect, useCallback, useRef } from 'react';
import { RefreshCw, Download, CheckCircle, ExternalLink, Info, MessageSquareWarning } from 'lucide-react';
import { Alerte, Button, Carte, Etiquette } from '../ui';
import { useBackendStore } from '../../hooks/useBackend';
import { checkHealth } from '../../services/api';

const GITHUB_REPO = 'ludovicsanchez38-creator/Synoptia-THERESE';
const RELEASES_URL = `https://github.com/${GITHUB_REPO}/releases`;
// US-012 : invitation Discord alpha PERMANENTE (revue adversariale : l'URL
// vanity discord.gg/therese-alpha n'existait pas - Unknown Invite. Celle-ci
// est créée par le bot Thérèse sur la guilde THÉRÈSE - Alpha, sans expiration).
const DISCORD_URL = 'https://discord.gg/krDGArdbH8';

interface ReleaseInfo {
  tag_name: string;
  name: string;
  html_url: string;
  published_at: string;
  body: string;
  assets: { name: string; browser_download_url: string; size: number }[];
}

type UpdateStatus = 'idle' | 'checking' | 'up-to-date' | 'update-available' | 'error';

const VERSION_INCONNUE = 'Impossible de lire la version installée. Réessaie dans un instant.';

/** Positif si la distante est plus récente ; null si une version est illisible. */
function compareVersions(current: string, latest: string): number | null {
  const decouper = (brut: string) => {
    if (typeof brut !== 'string') return null;
    const parties = /^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)(?:-([0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?(?:\+([0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?$/.exec(brut.trim().replace(/^v/i, ''));
    if (!parties) return null;
    const pre = parties[4]?.split('.') ?? null;
    if (pre?.some((identifiant) => /^0\d+$/.test(identifiant))) return null;
    // Les métadonnées (+...) sont validées mais ne participent pas à l'ordre.
    return { coeur: parties.slice(1, 4), pre };
  };
  // Comparer les chiffres sans perte de précision sur les grands identifiants.
  const comparerNombres = (a: string, b: string) => a.length !== b.length
    ? b.length - a.length : a === b ? 0 : a < b ? 1 : -1;
  const actuel = decouper(current);
  const distant = decouper(latest);
  if (!actuel || !distant) return null;
  for (let i = 0; i < 3; i++) {
    const ecart = comparerNombres(actuel.coeur[i], distant.coeur[i]);
    if (ecart !== 0) return ecart;
  }
  if (!actuel.pre && !distant.pre) return 0;
  // Une livraison sans préversion est plus récente que la préversion du même numéro.
  if (!actuel.pre) return -1;
  if (!distant.pre) return 1;
  const identifiants = Math.max(actuel.pre.length, distant.pre.length);
  for (let i = 0; i < identifiants; i++) {
    const gauche = actuel.pre[i];
    const droite = distant.pre[i];
    if (gauche === undefined) return 1;
    if (droite === undefined) return -1;
    const gaucheNombre = /^\d+$/.test(gauche);
    const droiteNombre = /^\d+$/.test(droite);
    if (gaucheNombre && droiteNombre) {
      const ecart = comparerNombres(gauche, droite);
      if (ecart !== 0) return ecart;
      continue;
    }
    if (gaucheNombre !== droiteNombre) return gaucheNombre ? 1 : -1;
    if (gauche !== droite) return gauche < droite ? 1 : -1;
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
  const automaticChecks = useAutomaticUpdateChecks();
  const version = useBackendStore((s) => s.version);
  const [updateStatus, setUpdateStatus] = useState<UpdateStatus>('idle');
  const [latestRelease, setLatestRelease] = useState<ReleaseInfo | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [lectureVersionEnCours, setLectureVersionEnCours] = useState(false);
  const lectureVersion = useRef<ReturnType<typeof checkHealth> | null>(null);
  const lireVersion = useCallback(() => {
    // Le clic partage la lecture du montage ; une lecture terminée peut être retentée.
    if (!lectureVersion.current) {
      setLectureVersionEnCours(true);
      lectureVersion.current = checkHealth().finally(() => {
        lectureVersion.current = null;
        setLectureVersionEnCours(false);
      });
    }
    return lectureVersion.current;
  }, []);

  // Fetch la version si elle n'est pas encore disponible (panels Tauri = contexte JS séparé)
  useEffect(() => {
    if (version) return undefined;
    let annule = false;
    lireVersion()
      .then((health) => {
        if (!health.version) throw new Error(VERSION_INCONNUE);
        if (!annule) useBackendStore.getState().setConnected(health);
      })
      .catch(() => {
        if (annule) return;
        setErrorMsg(VERSION_INCONNUE);
        setUpdateStatus('error');
      });
    return () => {
      annule = true;
    };
  }, [version, lireVersion]);

  async function checkForUpdates() {
    let versionInstallee = version || useBackendStore.getState().version;
    setUpdateStatus('checking');
    setErrorMsg(null);

    try {
      if (!versionInstallee) {
        const health = await lireVersion().catch(() => { throw new Error(VERSION_INCONNUE); });
        if (!health.version) throw new Error(VERSION_INCONNUE);
        useBackendStore.getState().setConnected(health);
        versionInstallee = health.version;
        setErrorMsg(null);
      }
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

      const comparaison = compareVersions(versionInstallee, latest.tag_name);
      if (comparaison === null) {
        throw new Error('Impossible de vérifier les mises à jour : version installée ou publiée illisible.');
      }
      // Le moteur historique donne X.Y.Z pour la livraison X.Y.Z-alpha.
      // Ce numéro ne situe ni une préversion numérotée ni la finale du même cœur.
      const numero = versionInstallee.trim().replace(/^v/i, '').split('+')[0];
      const tag = latest.tag_name.trim().replace(/^v/i, '').split('+')[0];
      if (/^\d+\.\d+\.\d+$/.test(numero) && (tag === numero || (tag.startsWith(`${numero}-`) && tag !== `${numero}-alpha`))) {
        throw new Error('Impossible de vérifier la version exacte de la livraison installée. Consulte le téléchargement manuel.');
      }

      if (comparaison > 0) {
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
    // B-763 : return open(...) - sans lui, le rejet d'open() hors Tauri n'atteignait
    // jamais le catch et le repli window.open ne tournait pas (cf. openDownload).
    import('@tauri-apps/plugin-shell').then(({ open }) => {
      return open(latestRelease?.html_url || RELEASES_URL);
    }).catch(() => {
      window.open(latestRelease?.html_url || RELEASES_URL, '_blank');
    });
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

  const platformAsset = latestRelease ? getPlatformAsset(latestRelease.assets) : null;

  return (
    <div className="space-y-6">
      <label className="flex items-center gap-3 text-sm text-text">
        <input type="checkbox" checked={automaticChecks}
          onChange={(event) => setAutomaticUpdateChecks(event.target.checked)} />
        Vérifier les mises à jour automatiquement
      </label>

      {/* Version actuelle */}
      <Carte as="section" className="p-5">
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
            <Etiquette className="ml-2">Alpha</Etiquette>
          </div>
        </div>
      </Carte>

      {/* Sélecteur réversible de l'interface, appliqué au prochain bootstrap. */}

      {/* US-012 : communauté et retours - le testeur alpha doit pouvoir
          signaler un bug sans connaître l'URL Discord par coeur */}
      <Carte as="section" className="p-5">
        <h4 className="text-sm font-medium text-text mb-3 flex items-center gap-2">
          <MessageSquareWarning className="w-4 h-4 text-accent" />
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
      </Carte>

      {/* Vérification des mises à jour */}
      <Carte as="section" className="p-5">
        <h4 className="text-sm font-medium text-text mb-3 flex items-center gap-2">
          <RefreshCw className="w-4 h-4 text-accent" />
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

          {/* Région persistante : annonce l'attente puis son résultat. */}
          <div role="status" aria-live="polite" aria-atomic="true"
            className={updateStatus === 'up-to-date' || updateStatus === 'update-available' ? undefined : 'sr-only'}>
            {lectureVersionEnCours ? (
              <p className="sr-only">Lecture de la version installée en cours...</p>
            ) : updateStatus === 'checking' && (
              <p className="sr-only">Vérification des mises à jour en cours...</p>
            )}
            {updateStatus === 'up-to-date' && (
              <div className="flex items-center gap-2 text-sm text-success bg-[var(--color-success-tint)] rounded-md px-3 py-2">
                <CheckCircle className="w-4 h-4" />
                THÉRÈSE est à jour (v{version})
              </div>
            )}

            {/* Résultat : mise à jour disponible */}
            {updateStatus === 'update-available' && latestRelease && (
              <div className="rounded-md border border-accent-cyan/30 bg-accent-tint p-3">
                <p className="mb-1 text-sm font-medium text-accent">
                  Nouvelle version disponible : {latestRelease.tag_name}
                </p>
                <p className="text-xs text-text-muted">
                  {latestRelease.name || latestRelease.tag_name}
                  {latestRelease.published_at && (
                    <> - {new Date(latestRelease.published_at).toLocaleDateString('fr-FR')}</>
                  )}
                </p>
              </div>
            )}
          </div>

          {updateStatus === 'update-available' && latestRelease && (
            <div className="space-y-3">
              <div className="flex items-center gap-2 text-xs text-text-muted bg-bg/50 rounded-md px-3 py-2">
                <Info className="w-3.5 h-3.5 shrink-0" />
                Tes données sont conservées lors de la mise à jour (dossier ~/.therese/).
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
          {errorMsg && (
            <Alerte titre="Impossible de vérifier">
              {errorMsg}
              {' '}
              <a href="https://synoptia.fr/therese/alpha/" target="_blank" rel="noopener noreferrer"
                className="underline" onClick={(event) => { event.preventDefault(); openDownload(event.currentTarget.href); }}>
                Télécharger THÉRÈSE manuellement
              </a>
            </Alerte>
          )}
        </div>
      </Carte>

      {/* Crédits */}
      <div className="text-center text-xs text-text-muted space-y-1">
        <p>Synoptia SARL-U - Manosque, France</p>
        <p>"Humain d'abord - IA en soutien"</p>
      </div>
    </div>
  );
}
