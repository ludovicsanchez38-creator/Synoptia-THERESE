/**
 * Le panneau des traitements longs (0.46).
 *
 * La promesse affichée est la promesse tenable : « Arrêter » envoie la
 * demande ; tant que le producteur n'a pas réellement fini, l'état montre
 * « Arrêt demandé - fin de l'étape en cours ». Jamais un arrêt annoncé
 * pendant que le travail continue.
 */
import { useEffect } from 'react';
import { Square, X } from 'lucide-react';

import { pushEscapeHandler } from '../../lib/escapeStack';

import type { Traitement } from '../../services/api';
import { useProcessingTasksStore } from '../../stores/processingTasksStore';
import { Spinner } from '../ui/Spinner';
import { Alerte, Button, EtatVide } from '../ui';

const LIBELLES_ETAT: Record<Traitement['state'], string> = {
  queued: 'En file',
  running: 'En cours',
  cancel_requested: "Arrêt demandé - fin de l'étape en cours",
  cancelled: 'Arrêté',
  interrupted: 'Interrompu (redémarrage)',
  done: 'Terminé',
  failed: 'En échec',
};

export function TraitementsPanel() {
  const traitements = useProcessingTasksStore((s) => s.traitements);
  const erreur = useProcessingTasksStore((s) => s.erreur);
  const arretsDemandes = useProcessingTasksStore((s) => s.arretsDemandes);
  const annuler = useProcessingTasksStore((s) => s.annuler);
  const fermer = useProcessingTasksStore((s) => s.fermerPanneau);

  // B-651 (ronde B, D1) : un role=dialog qu'Échap ne fermait pas. Le panneau
  // s'inscrit dans la pile d'Échap, première moitié de la cascade de la coque
  // (les overlays portés par les stores) ; le retrait suit le démontage.
  useEffect(() => pushEscapeHandler(fermer), [fermer]);

  return (
    <div
      className="absolute right-0 top-full z-50 mt-2 w-96 max-w-[90vw] rounded-md border border-border bg-surface p-3 shadow-lg"
      role="dialog"
      aria-label="Travaux en cours"
    >
      <div className="mb-2 flex items-center justify-between">
        <h3 className="text-sm font-semibold text-text">Travaux récents</h3>
        <Button
          type="button"
          variant="ghost"
          size="icon"
          onClick={fermer}
          aria-label="Fermer les travaux"
        >
          <X className="h-4 w-4" />
        </Button>
      </div>

      {erreur && (
        <Alerte className="mb-2" titre="Chargement incomplet">{erreur}</Alerte>
      )}

      {traitements.length === 0 && !erreur && (
        <EtatVide titre="Aucun travail récent." className="py-6" />
      )}

      <ul className="max-h-80 space-y-2 overflow-y-auto">
        {traitements.map((t) => {
          const enCours = t.state === 'running' || t.state === 'queued';
          const arretDemande =
            t.state === 'cancel_requested' || arretsDemandes.has(t.id);
          return (
            <li
              key={t.id}
              className="rounded-sm border border-border/60 bg-surface-2 p-2"
              data-testid="traitement"
            >
              <div className="flex items-center gap-2">
                {enCours && !arretDemande && (
                  <Spinner taille="ligne" className="shrink-0 text-accent" />
                )}
                <span className="flex-1 truncate text-xs font-medium text-text">
                  {t.label}
                </span>
                {t.can_cancel && !arretDemande && (
                  <Button
                    type="button"
                    variant="secondary"
                    size="sm"
                    onClick={() => void annuler(t.id)}
                    aria-label={`Arrêter ${t.label}`}
                    className="hover:border-error hover:text-error"
                  >
                    <Square className="h-3 w-3" />
                    Arrêter
                  </Button>
                )}
              </div>
              <p className="mt-1 text-xs text-text-muted">
                {arretDemande && t.state !== 'cancelled'
                  ? LIBELLES_ETAT.cancel_requested
                  : LIBELLES_ETAT[t.state]}
                {t.step ? ` - ${t.step}` : ''}
                {t.progress != null && enCours
                  ? ` (${Math.round(t.progress * 100)} %)`
                  : ''}
              </p>
              {t.error && (
                <p className="mt-0.5 truncate text-xs text-error">{t.error}</p>
              )}
            </li>
          );
        })}
      </ul>
    </div>
  );
}
