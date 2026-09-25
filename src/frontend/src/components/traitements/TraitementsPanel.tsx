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
import { heureDuServeur } from '../../lib/heureDuServeur';
import { EVENEMENT_OUVRIR_TRAVAIL, destinationDuTravail } from '../../lib/destinationDuTravail';

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
      id="traitements-panneau"
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

      {/* P-097 : une frise en lecture seule. Les étapes passées n'ont plus
          l'apparence d'une carte-bouton ; chacune dit son état, son début et
          sa fin. Seul un travail en cours garde un geste (« Arrêter »). */}
      {/* Le conteneur qui défile garde une marge symétrique : une marge d'un seul
          côté rognait l'anneau de focus d'« Arrêter » (anneauNonRogne). */}
      <div className="max-h-80 overflow-y-auto px-1">
      <ol role="list" aria-label="Frise des travaux récents" className="border-l border-border pl-3">
        {traitements.map((t) => {
          const enCours = t.state === 'running' || t.state === 'queued';
          const arretDemande =
            t.state === 'cancel_requested' || arretsDemandes.has(t.id);
          const destination = destinationDuTravail(t);
          const debut = heureDuServeur(t.started_at ?? t.created_at);
          const fin = heureDuServeur(t.finished_at);
          return (
            <li
              key={t.id}
              className="relative py-1.5 before:absolute before:-left-[17px] before:top-3 before:h-2 before:w-2 before:rounded-full before:bg-border"
              data-testid="traitement"
            >
              <div className="flex items-center gap-2">
                {enCours && !arretDemande && (
                  <Spinner taille="ligne" className="shrink-0 text-accent" />
                )}
                {/* P-140 : la ligne ouvre l'objet qu'elle nomme quand on le connaît. */}
                {destination ? (
                  <button
                    type="button"
                    onClick={() => {
                      window.dispatchEvent(new CustomEvent(EVENEMENT_OUVRIR_TRAVAIL, { detail: destination }));
                      fermer();
                    }}
                    aria-label={`Ouvrir ${t.label}`}
                    title={t.label}
                    className="flex-1 truncate rounded-sm text-left text-sm font-medium text-accent underline-offset-2 hover:underline focus:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                  >
                    {t.label}
                  </button>
                ) : (
                  <span className="flex-1 truncate text-xs font-medium text-text" title={t.label}>
                    {t.label}
                  </span>
                )}
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
                {/* B-764 : un traitement terminé, en échec ou interrompu après une
                    demande d'arrêt se dit tel quel ; « Arrêt demandé » ne vaut que
                    tant qu'il tourne encore. */}
                {arretDemande && (enCours || t.state === 'cancel_requested')
                  ? LIBELLES_ETAT.cancel_requested
                  : LIBELLES_ETAT[t.state]}
                {t.step ? ` - ${t.step}` : ''}
                {t.progress != null && enCours
                  ? ` (${Math.round(t.progress * 100)} %)`
                  : ''}
              </p>
              {(debut || fin) && (
                <p className="mt-0.5 text-xs tabular-nums text-text-muted">
                  {debut ? `Début ${debut}` : ''}
                  {debut && fin ? ' · ' : ''}
                  {fin ? `Fin ${fin}` : ''}
                </p>
              )}
              {/* B-1160 : l'erreur dit quoi faire, elle se lit en entier. */}
              {t.error && (
                <p className="mt-0.5 break-words text-xs text-error">{t.error}</p>
              )}
            </li>
          );
        })}
      </ol>
      </div>
    </div>
  );
}
