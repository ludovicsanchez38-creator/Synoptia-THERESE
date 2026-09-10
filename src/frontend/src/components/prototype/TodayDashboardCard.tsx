import { useEffect, useState } from 'react';

import { useDemoMask } from '../../hooks';
import {
  libelleDuRepli,
  lireLeReglage,
  motActif,
  motsUtiles,
  oublierLesAutresJours,
  REGLAGE_PAR_DEFAUT,
  ecrireLeReglage,
  seuilDuReglage,
  type ReglageDuBrief,
} from '../../lib/variateurDuBrief';
import { BoutonOuvrirLaVue } from './BoutonOuvrirLaVue';
import {
  AlertCircle,
  Calendar,
  ChevronRight,
  ListTodo,
  Mail,
  Receipt,
  Sparkles,
  Users,
} from 'lucide-react';
import type { SetupStatus, TodayDashboard } from '../../services/api/dashboard';
import type { AppView } from '../../stores/navigationStore';
import { buildTodayAttentionItems, nombreNonAffiche, nommerLesSources, sourcesPresentes, todayBriefTitle, type AttentionKind, type TodayAttentionItem } from './prototypeReadModels';
import type { ReadResource } from './usePrototypeReadData';
import { Alerte } from '../ui/Alerte';
import { Button } from '../ui/Button';
import { Carte, CarteTete } from '../ui/Carte';
import { EtatVide } from '../ui/EtatVide';
import { Etiquette } from '../ui/Etiquette';
import { Ligne, type DomaineLigne } from '../ui/Ligne';
import { CLASSES_SEGMENTS, classeSegment } from '../ui/segments.classes';
import { Squelette } from '../ui/Squelette';
import { SetupChecklist } from '../home/SetupChecklist';

/*
 * DA « Application affinée », lot 2 (11/09/2026) : la carte du brief prend la
 * forme de la maquette `accueil.html` en consommant les primitives du lot 1.
 * Mêmes données, mêmes états, mêmes destinations ; design challengé six fois
 * avant le code : `docs/plans/2026-09-10-da-lot2-accueil-design.md`.
 */

const attentionIcons = {
  event: Calendar,
  task: ListTodo,
  follow_up: Mail,
  invoice: Receipt,
  prospect: Users,
} satisfies Record<AttentionKind, typeof Calendar>;

// B-363 : un domaine, une couleur. Depuis le lot 2, la couleur vient de la
// `Ligne` (`domaine`), la carte ne connaît que la correspondance.
const DOMAINE_DE_KIND: Record<AttentionKind, DomaineLigne> = {
  event: 'agenda',
  task: 'taches',
  follow_up: 'prospects',
  invoice: 'factures',
  prospect: 'prospects',
};

const pluriel = (n: number, un: string, plusieurs: string) => (n > 1 ? plusieurs : un);

function metaDesPannes(pannes: string[]): string {
  return `${pannes.join(', ')} ${pluriel(pannes.length, 'indisponible', 'indisponibles')}`;
}

function SqueletteDeLigne() {
  return (
    <div className="grid grid-cols-[2rem_1fr_auto] items-center gap-3 border-t border-border px-4 py-3">
      <Squelette largeur="w-8" classeBarre="h-8 rounded-sm" />
      <div className="flex flex-col gap-2">
        <Squelette largeur="w-[60%]" />
        <Squelette largeur="w-[40%]" />
      </div>
      <span />
    </div>
  );
}

const CLASSE_BOUTON_VUE =
  'inline-flex h-9 items-center rounded-md border border-border bg-surface px-4 text-sm font-semibold text-text transition-colors hover:bg-surface-2 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-bg';

export function TodayDashboardCard({
  resource,
  onRetry,
  onOpenView,
  onOpenItem,
  setup = null,
  onSetupEmail,
}: {
  resource: ReadResource<TodayDashboard>;
  onRetry: () => void;
  onOpenView: (view: AppView) => void;
  /**
   * Ouvrir l'objet que l'item désigne (entrée 8 du plan du 28/08, B-563).
   * Facultatif : sans lui, la ligne ouvre la vue de son domaine.
   */
  onOpenItem?: (item: TodayAttentionItem) => void;
  /** B1 (0.48) : l'état vide dit la vérité - sans compte email, le brief
      ne peut rien préparer. La coque charge le SetupStatus et le passe. */
  setup?: SetupStatus | null;
  onSetupEmail?: () => void;
}) {
  // Le masque du mode démo : l'écran par défaut ne laisse aucun vrai nom.
  const { maskText } = useDemoMask();
  const items = resource.status === 'ready' ? buildTodayAttentionItems(resource.data) : [];
  // Une lecture qui a échoué ne dit RIEN de l'état réel : compter ses données
  // pour zéro, c'est annoncer une journée calme qu'on n'a pas constatée.
  const sourcesEnPanne =
    resource.status === 'ready' ? nommerLesSources(resource.data.indisponibles) : [];
  const presentes = resource.status === 'ready' ? sourcesPresentes(resource.data) : [];
  // Entrée 11b : le brief montre six éléments, le reste se déroule ici plutôt
  // que sur un autre écran. Depuis le 29/08, le seuil est réglable.
  const [toutAfficher, setToutAfficher] = useState(false);
  const jour = resource.status === 'ready' ? resource.data.date : null;
  const [reglage, setReglage] = useState<ReglageDuBrief>(REGLAGE_PAR_DEFAUT);
  const [jourConnu, setJourConnu] = useState<string | null>(null);
  // Le réglage vit et meurt avec la journée civile du backend : dès qu'elle
  // change, on repart du défaut sans attendre un remontage.
  if (jour !== null && jour !== jourConnu) {
    setJourConnu(jour);
    setReglage(lireLeReglage(jour));
    setToutAfficher(false);
  }

  // La purge est un effet de bord : elle n'a rien à faire dans le corps du
  // rendu, que StrictMode rejoue et que React peut abandonner.
  useEffect(() => {
    if (jour !== null) oublierLesAutresJours(jour);
  }, [jour]);

  const motsOfferts = motsUtiles(items.length);
  const motCoche = motActif(reglage, items.length);
  const seuil = seuilDuReglage(reglage);
  const visibleItems = toutAfficher || seuil === null ? items : items.slice(0, seuil);
  const replies = items.slice(visibleItems.length);
  const retardsReplies = replies.filter((item) => item.urgent).length;

  function choisirLeReglage(valeur: ReglageDuBrief) {
    setReglage(valeur);
    // Le réglage l'emporte sur une expansion ponctuelle déjà faite.
    setToutAfficher(false);
    if (jour !== null) ecrireLeReglage(jour, valeur);
  }

  // Le geste principal et la ligne ouvrent la même chose, par le même chemin.
  function ouvrir(item: TodayAttentionItem) {
    if (onOpenItem) onOpenItem(item);
    else onOpenView(item.targetView);
  }

  // Corps, par priorité (inchangée) : la liste gagne dès qu'elle n'est pas
  // vide ; sinon la messagerie absente ; sinon la panne ; sinon le vide.
  const sansMessagerie = items.length === 0 && setup !== null && setup.has_email === false;
  const videNonConstate = items.length === 0 && !sansMessagerie && sourcesEnPanne.length > 0;
  const nbRetards = items.filter((item) => item.urgent).length;
  const nonAffiches = resource.status === 'ready' ? nombreNonAffiche(resource.data) : 0;

  let titre = 'Ta journée';
  let meta = 'Lecture des sources locales';
  if (resource.status === 'error') meta = 'Lecture impossible';
  else if (resource.status === 'ready' && items.length > 0) {
    titre = todayBriefTitle(items.length);
    meta = `${items.length} ${pluriel(items.length, 'élément', 'éléments')}`;
    if (nbRetards > 0) meta += `, dont ${nbRetards} en retard`;
    if (nonAffiches > 0) meta += `, et ${nonAffiches} ${pluriel(nonAffiches, 'autre non affiché', 'autres non affichés')}`;
    if (sourcesEnPanne.length > 0) meta += ` · ${metaDesPannes(sourcesEnPanne)}`;
  } else if (resource.status === 'ready' && sansMessagerie) meta = 'Messagerie non branchée';
  else if (resource.status === 'ready' && videNonConstate) meta = `${metaDesPannes(sourcesEnPanne)}, lecture incomplète`;
  else if (resource.status === 'ready') {
    titre = todayBriefTitle(0);
    meta = 'Aucune échéance, aucune facture en attente';
  }

  const listeDeMiseEnRoute = setup !== null && (
    <div className="px-4 pb-4">
      {/* L'étape messagerie est masquée quand le message dédié la porte déjà :
          deux invitations pour le même geste en valent zéro. */}
      <SetupChecklist niveau="h3" status={setup.has_email === false ? { ...setup, has_email: true } : setup} />
    </div>
  );

  return (
    <Carte as="section" aria-labelledby="today-dashboard-title" data-testid="today-dashboard-card">
      <CarteTete
        idTitre="today-dashboard-title"
        icone={<Sparkles className="h-[18px] w-[18px]" />}
        titre={titre}
        meta={meta}
        actions={
          <>
            <BoutonOuvrirLaVue vue="calendar" onOuvrir={() => onOpenView('calendar')} className={CLASSE_BOUTON_VUE} />
            {resource.status === 'ready' && items.length > 0 && (
              <Button
                variant="primary"
                size="md"
                className="h-auto min-h-9 min-w-0 max-w-full whitespace-normal text-left max-[840px]:basis-full"
                onClick={() => ouvrir(items[0])}
              >
                Commencer : {maskText(items[0].title)}
              </Button>
            )}
          </>
        }
      />

      {/* Le variateur (plan du 29/08) : trois mots écrits, un seul choix
          (radiogroup), habillé des segments de la DA. Il n'apparaît que
          lorsqu'il a de quoi replier. */}
      {resource.status === 'ready' && motsOfferts.length > 1 && (
        <div className="flex flex-wrap items-center gap-2 border-t border-border px-4 py-2">
          <span id="variateur-brief-libelle" className="text-sm text-text-muted">
            Montre-moi
          </span>
          <div role="radiogroup" aria-labelledby="variateur-brief-libelle" className={CLASSES_SEGMENTS}>
            {motsOfferts.map(({ valeur, mot }) => (
              <label
                key={valeur}
                /* La radio est hors écran (`sr-only`) : l'anneau se dessine
                   sur le mot, sinon personne ne saurait, au clavier, où il est. */
                className={`cursor-pointer transition-colors focus-within:outline focus-within:outline-[3px] focus-within:outline-offset-2 focus-within:outline-ring ${classeSegment(motCoche?.valeur === valeur)}`}
              >
                <input
                  type="radio"
                  name="variateur-brief"
                  className="sr-only"
                  checked={motCoche?.valeur === valeur}
                  onChange={() => choisirLeReglage(valeur)}
                  /* Une radio déjà cochée n'émet pas `change` : sans ce clic,
                     revenir à « l'essentiel » depuis une liste dépliée ne
                     ferait rien, et le mot mentirait. */
                  onClick={() => {
                    if (motCoche?.valeur === valeur) choisirLeReglage(valeur);
                  }}
                />
                {mot}
              </label>
            ))}
          </div>
        </div>
      )}

      {/* La panne est nommée dans tous les corps, une seule fois, au-dessus.
          Un seul « Réessayer » dans la carte : ici seulement si le corps n'en
          porte pas (le vide non constaté a le sien). */}
      {resource.status === 'ready' && sourcesEnPanne.length > 0 && (
        <div className="px-4 pt-3">
          <Alerte
            data-testid="today-dashboard-indisponible"
            icone={<AlertCircle className="h-[18px] w-[18px]" />}
            action={
              videNonConstate ? undefined : (
                <Button variant="ghost" size="md" onClick={onRetry}>
                  Réessayer
                </Button>
              )
            }
          >
            Je n’ai pas pu lire {sourcesEnPanne.join(', ')}. Ce qui en vient manque
            ici : ce n’est pas forcément une journée calme.
          </Alerte>
        </div>
      )}

      {resource.status === 'loading' ? (
        <>
          <div aria-hidden="true">
            <SqueletteDeLigne />
            <SqueletteDeLigne />
            <SqueletteDeLigne />
          </div>
          <p role="status" className="px-4 py-3 text-sm text-text-muted">
            Je rassemble ta journée…
          </p>
        </>
      ) : resource.status === 'error' ? (
        <div className="px-4 pt-3 pb-4">
          <Alerte
            data-testid="today-dashboard-error"
            titre="Brief indisponible"
            icone={<AlertCircle className="h-[18px] w-[18px]" />}
            action={
              <Button variant="secondary" size="md" onClick={onRetry}>
                Réessayer
              </Button>
            }
          >
            {resource.error}
          </Alerte>
        </div>
      ) : items.length > 0 ? (
        <div>
          {visibleItems.map((item) => {
            const Icon = attentionIcons[item.kind];
            return (
              <Ligne
                key={item.id}
                domaine={DOMAINE_DE_KIND[item.kind]}
                puce={<Icon className="h-[18px] w-[18px]" />}
                titre={maskText(item.title)}
                detail={maskText(item.detail)}
                droite={
                  <>
                    {/* La maquette peint les factures en attention, les retards
                        de tâches et de relances en erreur : présentation seule,
                        `urgent` reste ce qu'il est pour le tri et le repli. */}
                    <Etiquette ton={item.kind === 'invoice' ? 'attention' : item.urgent ? 'erreur' : 'neutre'}>
                      {item.badge}
                    </Etiquette>
                    <ChevronRight className="h-[18px] w-[18px]" />
                  </>
                }
                onClick={() => ouvrir(item)}
              />
            );
          })}
          {items.length > visibleItems.length && (
            <Button
              variant="ghost"
              size="md"
              /* Entrée 11b : la suite se déroule ici, pas sur un autre écran. */
              onClick={() => setToutAfficher(true)}
              className="w-full border-t border-border"
            >
              {libelleDuRepli(replies.length, retardsReplies)}
            </Button>
          )}
        </div>
      ) : sansMessagerie ? (
        <>
          <EtatVide
            data-testid="today-dashboard-setup-email"
            titre="Branche tes mails pour que je te prépare la journée"
            action={
              <Button variant="primary" size="md" onClick={onSetupEmail}>
                Brancher mes mails
              </Button>
            }
          >
            Sans boîte connectée, le brief ne voit ni messages à traiter ni relances.
          </EtatVide>
          {listeDeMiseEnRoute}
        </>
      ) : videNonConstate ? (
        <>
          {/* Le vide n'est pas constaté : il n'a pas pu être lu. Surtout, il ne
              prend pas la formulation du vide constaté. */}
          <EtatVide
            data-testid="today-dashboard-incomplet"
            titre="Ta journée est incomplète"
            action={
              <Button variant="secondary" size="md" onClick={onRetry}>
                Réessayer
              </Button>
            }
          >
            Rien ne remonte, mais la lecture n’a pas abouti : ce n’est pas une
            journée calme constatée.
          </EtatVide>
          {listeDeMiseEnRoute}
        </>
      ) : (
        <>
          <EtatVide data-testid="today-dashboard-empty" titre="Ta journée est dégagée.">
            Quand tu ajouteras une tâche, un rendez-vous ou une facture, ils
            apparaîtront ici avec leur échéance.
          </EtatVide>
          {listeDeMiseEnRoute}
        </>
      )}

      {resource.status === 'ready' && (presentes.length > 0 || sourcesEnPanne.length > 0) && (
        <div className="flex flex-wrap items-center gap-1.5 border-t border-border bg-surface-2 px-4 py-2.5 text-xs font-medium text-text-muted">
          <span className="mr-1">Lu dans</span>
          {presentes.map((s) => (
            <Etiquette key={s.cle} domaine={s.domaine}>
              {s.nom}
            </Etiquette>
          ))}
          {sourcesEnPanne.map((nom) => (
            <Etiquette key={`panne-${nom}`} ton="neutre">
              {nom} indisponible
            </Etiquette>
          ))}
        </div>
      )}
    </Carte>
  );
}
