/**
 * P-148 : la vue d'ensemble de ce qu'une fenêtre rassemble, famille par
 * famille (Conversations, Documents, Tâches, Contacts). Générique : la
 * fenêtre d'un fil de travail (P-104) la nourrira de sa propre route, et une
 * famille de plus s'ajoute à la liste sans retoucher cette structure.
 *
 * Trois rendus distincts : la lecture en cours, la panne (bandeau
 * `role="alert"` avec « Réessayer ») et le vide, qui dit comment rattacher.
 * Une famille illisible (`total: null`) est une panne, jamais un « 0 ».
 * Chaque ligne est une liste nommée par son libellé et son total, écrit dans
 * le texte ; un élément qui mène quelque part est un vrai bouton dont le nom
 * dit la destination.
 */
import { useId, useLayoutEffect } from 'react';
import { AlertCircle } from 'lucide-react';

import { Alerte } from './Alerte';
import { Button } from './Button';

export interface ElementDEnsemble {
  id: string;
  libelle: string;
  detail?: string;
  /** Nom du bouton : il contient le libellé et dit la destination. */
  nomAccessible?: string;
  /** Sans lui, l'élément reste un texte : aucune destination inventée. */
  onOuvrir?: () => void;
}

export interface FamilleDEnsemble {
  cle: string;
  libelle: string;
  /** `null` : la famille n'a pas pu être lue. */
  total: number | null;
  /** Une phrase sous le libellé (« 4 ouvertes, dont 1 en retard »). */
  resume?: string;
  elements: ElementDEnsemble[];
  texteDuVide: string;
  /** Le geste sous la liste (« Tout afficher », « Voir les 9 tâches dans Tâches »). */
  action?: { libelle: string; onClick: () => void; enCours?: boolean };
  /** Tout est affiché mais le moteur en compte davantage : la phrase qui le dit. */
  incomplete?: string;
}

export type EtatDeLEnsemble = 'chargement' | 'panne' | 'pret';

function idDeLaFamille(prefixe: string, cle: string): string {
  return `${prefixe}-famille-${cle}`;
}

export function VueDEnsemble({
  titre,
  etat,
  familles,
  onReessayer,
  messageDePanne,
  messageDeChargement,
  prefixe,
  focaliser,
  onFocalise,
}: {
  /** Sans titre, l'hôte nomme lui-même la région (il peut y ajouter ses sections). */
  titre?: string;
  etat: EtatDeLEnsemble;
  familles: FamilleDEnsemble[];
  onReessayer: () => void;
  messageDePanne: string;
  messageDeChargement: string;
  /** Préfixe des identifiants (plusieurs vues peuvent coexister). */
  prefixe?: string;
  /**
   * La famille dont le titre reprend le focus : « Tout afficher » disparaît
   * quand la liste est complète, le focus y revient au lieu de tomber sur la page.
   */
  focaliser?: string | null;
  onFocalise?: () => void;
}) {
  const genere = useId();
  const base = prefixe ?? `ensemble${genere.replace(/[^a-zA-Z0-9-]/g, '')}`;
  const idTitre = `${base}-titre`;

  useLayoutEffect(() => {
    if (!focaliser) return;
    document.getElementById(idDeLaFamille(base, focaliser))?.focus();
    onFocalise?.();
  }, [focaliser, base, onFocalise]);

  const contenu = (
    <>
      {etat === 'panne' ? (
        <Alerte
          titre={messageDePanne}
          icone={<AlertCircle className="h-4 w-4" />}
          action={<Button variant="secondary" size="md" onClick={onReessayer}>Réessayer</Button>}
        />
      ) : (
        <>
          {etat === 'chargement' && (
            <p role="status" className="sr-only">{messageDeChargement}</p>
          )}
          {familles.map((famille) => (
            <LigneDEnsemble
              key={famille.cle}
              id={idDeLaFamille(base, famille.cle)}
              famille={famille}
              enChargement={etat === 'chargement'}
              onReessayer={onReessayer}
            />
          ))}
        </>
      )}
    </>
  );

  if (!titre) {
    return <div className="space-y-3" data-testid="vue-d-ensemble">{contenu}</div>;
  }
  return (
    <section aria-labelledby={idTitre} className="space-y-3" data-testid="vue-d-ensemble">
      <h3 id={idTitre} className="text-sm font-semibold text-text">{titre}</h3>
      {contenu}
    </section>
  );
}

function LigneDEnsemble({
  id,
  famille,
  enChargement,
  onReessayer,
}: {
  id: string;
  famille: FamilleDEnsemble;
  enChargement: boolean;
  onReessayer: () => void;
}) {
  const { libelle, total, resume, elements, texteDuVide, action, incomplete } = famille;
  const entete = enChargement || total === null ? libelle : `${libelle} (${total})`;
  return (
    <div className="space-y-1.5" data-famille={famille.cle}>
      {/* Focalisable par programme : « Tout afficher » disparaît quand la
          liste est complète, le focus y revient au lieu de tomber sur la page. */}
      <h4 id={id} tabIndex={-1} className="text-sm text-text-muted outline-none">{entete}</h4>
      {enChargement ? (
        <p className="text-sm text-text-muted">Chargement…</p>
      ) : total === null ? (
        <Alerte
          titre={`${libelle} : lecture impossible pour l’instant.`}
          icone={<AlertCircle className="h-4 w-4" />}
          action={<Button variant="secondary" size="md" onClick={onReessayer}>Réessayer</Button>}
        />
      ) : total === 0 ? (
        <p className="text-sm text-text-muted">{texteDuVide}</p>
      ) : (
        <>
          {resume && <p className="text-sm text-text">{resume}</p>}
          <ul aria-labelledby={id} className="space-y-1">
            {elements.map((element) => (
              <li key={element.id}>
                {element.onOuvrir ? (
                  <button
                    type="button"
                    onClick={element.onOuvrir}
                    aria-label={element.nomAccessible}
                    className="flex w-full items-center justify-between gap-2 rounded-md border border-border bg-surface-2 px-3 py-2 text-left text-sm hover:bg-surface-elevated focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                  >
                    <span className="min-w-0 truncate text-text">{element.libelle}</span>
                    {element.detail && <span className="shrink-0 text-xs text-text-muted">{element.detail}</span>}
                  </button>
                ) : (
                  <div className="flex items-center justify-between gap-2 rounded-md border border-border bg-surface-2 px-3 py-2 text-sm">
                    <span className="min-w-0 truncate text-text">{element.libelle}</span>
                    {element.detail && <span className="shrink-0 text-xs text-text-muted">{element.detail}</span>}
                  </div>
                )}
              </li>
            ))}
          </ul>
          {incomplete && <p className="text-sm text-warning">{incomplete}</p>}
          {action && (
            <Button variant="ghost" size="md" onClick={action.onClick} disabled={action.enCours}>
              {action.enCours ? 'Chargement…' : action.libelle}
            </Button>
          )}
        </>
      )}
    </div>
  );
}
