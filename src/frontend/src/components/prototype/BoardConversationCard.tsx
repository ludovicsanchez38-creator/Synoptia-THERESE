import { useState, type ReactNode } from 'react';
import { BoutonOuvrirLaVue } from './BoutonOuvrirLaVue';
import { formaterCout } from '../../lib/coutAffiche';
import {
  AlertCircle,
  Check,
  CheckCircle2,
  ChevronRight,
  ExternalLink,
  Gavel,
  Globe,
  History,
  Play,
  Plus,
  ShieldCheck,
  Square,
  Users,
} from 'lucide-react';
import type {
  AdvisorInfo,
  AdvisorRole,
  BoardDecisionDetail,
  BoardMode,
  BoardRequest,
  BoardSynthesis,
} from '../../services/api/board';
import { CharacterPortrait } from './DecisionMissionPrototype';
import type { BoardRunState, BoardWorkspaceData, PrototypeAdvisorState } from './usePrototypeBoardData';
import type { ReadResource } from './usePrototypeReadData';
import { grantCloudConsent } from '../../lib/consent';
import { handleRovingFocus } from '../../lib/rovingFocus';
import { Alerte } from '../ui/Alerte';
import { Button } from '../ui/Button';
import { Carte, CarteTete } from '../ui/Carte';
import { CompactMarkdown } from '../ui/CompactMarkdown';
import { EtatVide } from '../ui/EtatVide';
import { Etiquette, type TonEtiquette } from '../ui/Etiquette';
import { FormField } from '../ui/FormField';
import { Ligne } from '../ui/Ligne';
import { Spinner } from '../ui/Spinner';
import { Squelette } from '../ui/Squelette';
import { Textarea } from '../ui/Textarea';

/*
 * DA « Application affinée », lot 7 (11/09/2026) : la carte d'historique et
 * le canevas de Décision prennent la forme de la maquette `decision.html` en
 * consommant les primitives du lot 1. Mêmes données, mêmes états, mêmes
 * destinations ; aucun appel réseau, aucun store, aucun parcours ne change.
 * Design challengé sept fois avant le code :
 * `docs/plans/2026-09-11-da-lot7-decision-design.md`.
 */

export type BoardTarget = string | 'new-board' | 'current' | null;

const advisorOrder: AdvisorRole[] = ['analyst', 'strategist', 'devil', 'pragmatic', 'visionary'];
const advisorPortraits: Record<AdvisorRole, number> = {
  analyst: 1, strategist: 2, devil: 3, pragmatic: 4, visionary: 5,
};

/** La taille d'icône du lot : 18 px partout, sauf les tailles nommées du Spinner. */
const ICONE = 'h-[18px] w-[18px]';

/** La grille des avis, celle de la maquette (`decision.html:15`). */
const GRILLE_AVIS = 'grid grid-cols-[repeat(auto-fill,minmax(16rem,1fr))] gap-3';

/* Même chaîne que `TodayDashboardCard.tsx:84-85` (lot 2). Recopiée et non
   partagée : les deux écrans ne bougent pas dans le même commit. */
const CLASSE_BOUTON_VUE =
  'inline-flex h-9 items-center rounded-md border border-border bg-surface px-4 text-sm font-semibold text-text transition-colors hover:bg-surface-2 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-bg';

/**
 * Le conteneur des deux chargements du canevas. Il lui reste ces deux
 * appelants : les quatre autres états passent aux primitives. En colonne,
 * sans quoi le texte et les barres se rangeraient côte à côte.
 */
function StateShell({ children }: { children: ReactNode }) {
  return (
    <div className="flex min-h-48 flex-col items-center justify-center gap-3 px-5 py-8">
      {children}
    </div>
  );
}

function ChargementDuCanevas({ texte }: { texte: string }) {
  return (
    <StateShell>
      <p role="status" className="text-sm text-text-muted">{texte}</p>
      {/* `w-full max-w-sm` : la racine d'un Squelette n'a pas de largeur
          propre, un `w-[80%]` y vaudrait 80 % de zéro sous `items-center`. */}
      <Squelette className="w-full max-w-sm" largeur="w-[80%]" />
      <Squelette className="w-full max-w-sm" largeur="w-[60%]" />
    </StateShell>
  );
}

/** La rangée de chargement de l'historique (lot 2, `TodayDashboardCard.tsx:71-81`). */
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

const LIMITE_DECISIONS_ACCUEIL = 30;

function libelleDecisionsChargees(n: number): string {
  // Revue 30/08 : l'accueil ne lit que 30 décisions. Au plafond, le
  // total réel n'est pas un fait.
  if (n >= LIMITE_DECISIONS_ACCUEIL) {
    return `${n} décisions chargées (total non mesuré)`;
  }
  return `${n} décision${n > 1 ? 's' : ''} enregistrée${n > 1 ? 's' : ''}`;
}

function formatDate(value: string): string {
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? 'Date inconnue' : date.toLocaleString('fr-FR', {
    day: '2-digit', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit',
  });
}

function confidenceLabel(value: string): string {
  // Revue 30/08 : la valeur mesure l'accord entre conseillers, pas
  // la solidité factuelle de la recommandation.
  if (value === 'high') return 'Consensus élevé';
  if (value === 'medium') return 'Consensus moyen';
  if (value === 'low') return 'Consensus faible';
  return value || 'Consensus inconnu';
}

/** Un consensus faible est un accord entre avis, jamais une erreur (revue 30/08). */
function tonDuConsensus(value: string): TonEtiquette {
  return value === 'high' ? 'succes' : 'neutre';
}

/** Le mode n'est affiché que s'il a été enregistré : sinon c'est un fait non mesuré. */
function segmentDeMode(mode: string | undefined, avecPrefixe: boolean): string {
  if (!mode) return '';
  const nom = mode === 'sovereign' ? 'Souverain' : 'Cloud';
  return avecPrefixe ? `Mode ${nom.toLowerCase()}` : nom;
}

/** Les segments d'une meta, séparés par « · ». */
function joindre(segments: ReactNode[]): ReactNode[] {
  const sortie: ReactNode[] = [];
  segments.forEach((segment, index) => {
    if (index > 0) sortie.push(<span key={`sep-${index}`}> · </span>);
    sortie.push(<span key={index}>{segment}</span>);
  });
  return sortie;
}

// ---------------------------------------------------------------------------
// La carte d'historique
// ---------------------------------------------------------------------------

export function BoardHistoryCard({
  resource,
  run,
  onRetry,
  onOpenDecision,
  onNewBoard,
  onOpenCurrent,
  onOpenClassic,
}: {
  resource: ReadResource<BoardWorkspaceData>;
  run: BoardRunState;
  onRetry: () => void;
  onOpenDecision: (decisionId: string) => void;
  onNewBoard: () => void;
  onOpenCurrent: () => void;
  onOpenClassic: () => void;
}) {
  const decisions = resource.status === 'ready' ? resource.data.decisions.slice(0, 5) : [];
  const hasCurrentRun = run.status !== 'idle';

  return (
    /* `overflow-hidden` : la dernière rangée est le dernier élément de la
       carte et son survol n'a pas de rayon (`Ligne.tsx`), il déborderait les
       coins arrondis du bas. */
    <Carte
      as="section"
      className="overflow-hidden"
      aria-labelledby="board-history-title"
      data-testid="board-history-card"
    >
      <CarteTete
        idTitre="board-history-title"
        icone={<Gavel className={ICONE} />}
        titre="Décision"
        meta={resource.status === 'ready'
          ? libelleDecisionsChargees(resource.data.decisions.length)
          : 'Lecture de l’historique local'}
        actions={
          <>
            <Button variant="primary" size="md" className="gap-1.5" onClick={onNewBoard}>
              <Plus className={ICONE} />Nouvelle question
            </Button>
            <BoutonOuvrirLaVue vue="board" onOuvrir={onOpenClassic} className={CLASSE_BOUTON_VUE} />
          </>
        }
      />

      {hasCurrentRun && (
        /* Le testid vit sur l'enveloppe : `Ligne` n'a pas de rest props. La
           rangée n'est pas peinte, un domaine colore sa puce. */
        <div data-testid="board-current-run">
          <Ligne
            domaine="prospects"
            puce={run.status === 'running'
              ? <Spinner taille="bouton" />
              : run.status === 'complete'
                ? <CheckCircle2 aria-hidden="true" className={ICONE} />
                : <AlertCircle aria-hidden="true" className={ICONE} />}
            titre={run.question}
            detail={run.phase || run.status}
            coupe
            droite={<ChevronRight aria-hidden="true" className={ICONE} />}
            onClick={onOpenCurrent}
          />
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
            Je consulte les décisions…
          </p>
        </>
      ) : resource.status === 'error' ? (
        <div className="px-4 pt-3 pb-4">
          <Alerte
            data-testid="board-history-error"
            titre="Historique indisponible"
            icone={<AlertCircle className={ICONE} />}
            action={
              <Button variant="secondary" size="md" onClick={onRetry}>
                Réessayer
              </Button>
            }
          >
            {resource.error}
          </Alerte>
        </div>
      ) : decisions.length === 0 ? (
        <EtatVide
          data-testid="board-history-empty"
          titre="Aucune décision enregistrée"
          action={
            <Button variant="primary" size="md" onClick={onNewBoard}>
              Convoquer le Board
            </Button>
          }
        >
          Une délibération ne démarrera qu’après ta confirmation.
        </EtatVide>
      ) : (
        <div>
          {decisions.map((decision) => (
            <Ligne
              key={decision.id}
              domaine="prospects"
              puce={<History aria-hidden="true" className={ICONE} />}
              titre={decision.question}
              detail={decision.recommendation}
              coupe
              droite={
                <>
                  <span className="text-sm text-text-muted">
                    {formatDate(decision.created_at)}
                    {decision.mode ? ` · ${segmentDeMode(decision.mode, false)}` : ''}
                  </span>
                  <Etiquette ton={tonDuConsensus(decision.confidence)}>
                    {confidenceLabel(decision.confidence)}
                  </Etiquette>
                  <ChevronRight aria-hidden="true" className={ICONE} />
                </>
              }
              onClick={() => onOpenDecision(decision.id)}
            />
          ))}
        </div>
      )}
    </Carte>
  );
}

// ---------------------------------------------------------------------------
// La question et sa meta
// ---------------------------------------------------------------------------

function CarteQuestion({
  question,
  contexte,
  meta,
}: {
  question: string;
  contexte?: string | null;
  meta: ReactNode;
}) {
  return (
    /* `p-4` : `Carte` ne pose aucune marge intérieure. */
    <Carte as="section" className="p-4">
      <h3 className="text-lg font-bold leading-6">{question}</h3>
      <p className="mt-1 text-sm font-medium text-text-muted">{meta}</p>
      {contexte && (
        <p className="mt-3 border-t border-border pt-3 text-sm leading-5 text-text-muted">
          {contexte}
        </p>
      )}
    </Carte>
  );
}

/** Un avis « rendu » : il a du texte, ou il s'est déclaré terminé. */
function estRendu(advisor: PrototypeAdvisorState): boolean {
  return advisor.content.trim().length > 0 || advisor.isComplete;
}

function etiquetteDuRun(run: BoardRunState, completed: number): ReactNode {
  if (run.status === 'running') {
    return <Etiquette ton="info">{`Délibération en cours · ${completed}/5 avis`}</Etiquette>;
  }
  if (run.status === 'complete') {
    return <Etiquette ton="succes">Décision enregistrée</Etiquette>;
  }
  if (run.status === 'error') {
    const rendus = Object.values(run.advisors).filter(estRendu).length;
    if (rendus > 0) {
      /* Sans dénominateur : un `error` posé à la synthèse laisse cinq avis
         rendus, et « partielle · 5/5 » dirait partiel et complet à la fois. */
      return (
        <Etiquette ton="attention">
          {`Délibération partielle · ${rendus} avis rendu${rendus > 1 ? 's' : ''}`}
        </Etiquette>
      );
    }
  }
  return null;
}

function metaDuRun(run: BoardRunState, completed: number): ReactNode {
  const segments: ReactNode[] = [];
  const statut = etiquetteDuRun(run, completed);
  if (statut) segments.push(statut);
  segments.push(segmentDeMode(run.mode, true));
  segments.push('5 conseillers');
  if (run.status === 'complete' && run.decisionId) {
    segments.push(`Identifiant : ${run.decisionId}`);
  }
  return joindre(segments);
}

function metaDuDetail(decision: BoardDecisionDetail): ReactNode {
  const segments: ReactNode[] = [
    <Etiquette ton="succes">Décision enregistrée</Etiquette>,
  ];
  const mode = segmentDeMode(decision.mode, true);
  if (mode) segments.push(mode);
  const n = decision.opinions.length;
  segments.push(`${n} conseiller${n > 1 ? 's' : ''}`);
  segments.push(formatDate(decision.created_at));
  return joindre(segments);
}

// ---------------------------------------------------------------------------
// La synthèse
// ---------------------------------------------------------------------------

function TeteDeSynthese() {
  /* `CarteTete` imposerait un `h2` : le canevas en a déjà un, et la question
     est un `h3`. Mêmes classes, à la main. */
  return (
    <div className="flex flex-wrap items-center gap-3 px-4 pt-4 pb-2">
      <span
        aria-hidden="true"
        className="grid h-8 w-8 shrink-0 place-items-center rounded-full bg-accent-tint text-accent"
      >
        <Gavel className={ICONE} />
      </span>
      <div className="min-w-0 flex-1">
        <h3>Synthèse</h3>
        <p className="text-xs font-medium text-text-muted">
          Ce que les avis ont en commun, et ce qui les sépare
        </p>
      </div>
    </div>
  );
}

function CarteSynthese({ synthesis }: { synthesis: BoardSynthesis | null }) {
  return (
    <Carte
      as="article"
      className="border-l-[3px] border-l-accent-fill"
      data-testid="board-synthesis"
    >
      <TeteDeSynthese />
      <div className="space-y-3 px-4 pb-4">
        {synthesis ? (
          <>
            <div className="flex items-start gap-3 rounded-sm bg-accent-tint p-3">
              <Check aria-hidden="true" className={`${ICONE} shrink-0 text-accent`} />
              <p className="text-sm">
                <span className="font-semibold text-accent">Recommandation : </span>
                <b className="text-accent">{synthesis.recommendation}</b>
              </p>
            </div>
            <div>
              <Etiquette ton={tonDuConsensus(synthesis.confidence)}>
                {confidenceLabel(synthesis.confidence)}
              </Etiquette>
            </div>
            <div>
              <h4 className="text-sm font-bold text-text">Consensus</h4>
              <ul className="mt-2 space-y-2 text-sm leading-5 text-text">
                {synthesis.consensus_points.map((point) => (
                  <li key={point} className="flex gap-2">
                    <CheckCircle2 aria-hidden="true" className={`${ICONE} mt-0.5 shrink-0 text-success`} />
                    {point}
                  </li>
                ))}
              </ul>
            </div>
            <div>
              <h4 className="text-sm font-bold text-text">Prochaines étapes</h4>
              <ol className="mt-2 space-y-2 text-sm leading-5 text-text">
                {synthesis.next_steps.map((step, index) => (
                  <li key={step} className="flex gap-2">
                    <span className="font-bold text-domaine-prospects">{index + 1}</span>
                    {step}
                  </li>
                ))}
              </ol>
            </div>
          </>
        ) : (
          <>
            <p className="text-sm text-text-muted">
              Synthèse en préparation, elle arrive après le dernier avis.
            </p>
            <Squelette largeur="w-[80%]" />
            <Squelette largeur="w-[60%]" />
          </>
        )}
      </div>
    </Carte>
  );
}

// ---------------------------------------------------------------------------
// Les avis
// ---------------------------------------------------------------------------

function AdvisorOpinionCard({
  advisor,
  info,
  enCours,
}: {
  advisor?: PrototypeAdvisorState;
  info: AdvisorInfo;
  enCours: boolean;
}) {
  const contenu = advisor?.content ?? '';
  const aDuContenu = contenu.trim().length > 0;
  const streaming = enCours && Boolean(advisor?.isRunning);
  const meta = advisor?.provider || info.personality;
  const pastille = <span className="h-2 w-2 rounded-full bg-border" />;

  /* Table du design, premier match. Pas de Spinner hors d'un run : après une
     erreur, un conseiller reste `isRunning: true` sans que rien ne tourne. */
  const icone = streaming
    ? <Spinner taille="ligne" />
    : aDuContenu && advisor?.isComplete
      ? <CheckCircle2 aria-hidden="true" className={`${ICONE} text-success`} />
      : pastille;

  return (
    <Carte as="section" className="p-3">
      <div className="flex items-center gap-2.5">
        <CharacterPortrait index={advisorPortraits[info.role]} className="h-8 w-8 rounded-full" />
        <div className="min-w-0 flex-1">
          <strong className="block text-sm font-semibold">{info.name}</strong>
          {meta ? <p className="truncate text-sm text-text-muted">{meta}</p> : null}
        </div>
        {icone}
      </div>

      {aDuContenu ? (
        streaming ? (
          <p className="mt-3 whitespace-pre-wrap text-sm leading-5 text-text">
            {contenu}
            <span aria-hidden="true" className="ml-1 inline-block h-3.5 w-0.5 animate-pulse bg-accent align-text-bottom" />
          </p>
        ) : (
          <CompactMarkdown className="mt-3 text-sm leading-6">{contenu}</CompactMarkdown>
        )
      ) : enCours ? (
        <div className="mt-3 space-y-2">
          {streaming && <Etiquette ton="neutre">Réfléchit…</Etiquette>}
          <Squelette largeur="w-[80%]" />
          <Squelette largeur="w-[60%]" />
        </div>
      ) : (
        <div className="mt-3">
          <Etiquette ton="erreur">Avis non rendu</Etiquette>
        </div>
      )}
    </Carte>
  );
}

function CarteAvisSauvegarde({ opinion }: { opinion: BoardDecisionDetail['opinions'][number] }) {
  const aDuContenu = opinion.content.trim().length > 0;
  return (
    <Carte as="section" className="p-3">
      <div className="flex items-center gap-2.5">
        <CharacterPortrait index={advisorPortraits[opinion.role]} className="h-8 w-8 rounded-full" />
        <div className="min-w-0 flex-1">
          <strong className="block text-sm font-semibold">{opinion.name}</strong>
          {/* Sans cette garde, une décision enregistrée avant le suivi des
              fournisseurs afficherait « provider inconnu » sur chaque carte. */}
          {(opinion.provider || opinion.model) && (
            <p className="truncate text-sm text-text-muted">
              {opinion.provider || 'provider inconnu'} · {opinion.model || 'modèle non mesuré'}
              {typeof opinion.cost_eur === 'number' ? ` · ${formaterCout(opinion.cost_eur, 4)}` : ''}
            </p>
          )}
        </div>
      </div>
      {aDuContenu ? (
        <CompactMarkdown className="mt-3 text-sm leading-6">{opinion.content}</CompactMarkdown>
      ) : (
        <div className="mt-3">
          <Etiquette ton="erreur">Avis non rendu</Etiquette>
        </div>
      )}
    </Carte>
  );
}

function Divergences({ synthesis }: { synthesis: BoardSynthesis }) {
  return (
    <section>
      <h3 className="text-base">Où les avis divergent</h3>
      {synthesis.divergence_points.length > 0 ? (
        <ul className="mt-2 space-y-2 text-sm leading-5 text-text">
          {synthesis.divergence_points.map((point) => <li key={point}>{point}</li>)}
        </ul>
      ) : (
        <p className="mt-2 text-sm text-text-muted">Aucune divergence enregistrée.</p>
      )}
    </section>
  );
}

// ---------------------------------------------------------------------------
// Le run en cours
// ---------------------------------------------------------------------------

function BoardRunView({
  run,
  advisors,
  onCancel,
  onReset,
}: {
  run: BoardRunState;
  advisors: AdvisorInfo[];
  onCancel: () => void;
  onReset: () => void;
}) {
  const completed = Object.values(run.advisors).filter((advisor) => advisor.isComplete).length;
  const [cancelConfirmationOpen, setCancelConfirmationOpen] = useState(false);
  const enCours = run.status === 'running';

  return (
    <div className="space-y-4" data-testid="board-run-view">
      <CarteQuestion question={run.question} contexte={run.context} meta={metaDuRun(run, completed)} />

      {/* La progression reste au-dessus des cinq cartes : dans un panneau qui
          défile, le seul indicateur vivant ne doit pas tomber sous elles. */}
      {enCours && (
        /* La teinte de l'accent : c'est la seule zone vivante d'un panneau
           qui défile, elle ne doit pas se lire comme un blanc. */
        <div className="rounded-md border border-accent-cyan/30 bg-accent-tint p-3">
          <div className="flex items-center gap-2 text-sm font-semibold text-accent" role="status">
            {run.isSearchingWeb
              ? <Globe aria-hidden="true" className={`${ICONE} animate-pulse`} />
              : <Spinner taille="bouton" />}
            {run.phase}
          </div>
          <div
            className="mt-2 h-1.5 overflow-hidden rounded-full bg-surface"
            role="progressbar"
            aria-label="Progression de la délibération"
            aria-valuemin={0}
            aria-valuemax={5}
            aria-valuenow={completed}
            aria-valuetext={`${completed} conseiller${completed > 1 ? 's' : ''} sur 5 terminé${completed > 1 ? 's' : ''}`}
          >
            <div
              className="h-full bg-domaine-prospects transition-[width]"
              style={{ width: `${Math.max(4, completed / 5 * 100)}%` }}
            />
          </div>
        </div>
      )}

      {(run.synthesis || enCours) && <CarteSynthese synthesis={run.synthesis} />}

      <div className={GRILLE_AVIS}>{advisorOrder.map((role) => {
        const info = advisors.find((advisor) => advisor.role === role)
          || { role, name: role, emoji: '', color: '', personality: '' };
        return <AdvisorOpinionCard key={role} advisor={run.advisors[role]} info={info} enCours={enCours} />;
      })}</div>

      {run.synthesis && <Divergences synthesis={run.synthesis} />}

      {(run.status === 'error' || run.status === 'persistence_error') && (
        <Alerte titre={run.status === 'persistence_error' ? 'Sauvegarde non vérifiée.' : 'Délibération incomplète.'}>
          {[run.error, 'Les avis partiels restent visibles mais aucune conclusion ne doit être considérée comme sauvegardée.']
            .filter(Boolean).join(' ')}
        </Alerte>
      )}
      {run.status === 'cancelled' && (
        <div className="rounded-md border border-warning/40 bg-[var(--color-warning-tint)] p-3 text-sm text-warning">
          Délibération annulée. Aucun résultat complet n’est présenté comme une décision.
        </div>
      )}

      {enCours && cancelConfirmationOpen ? (
        /* Fond `surface` : `Button danger` rend la teinte d'erreur, le geste
           destructeur disparaîtrait sur un bloc de la même teinte. */
        <div
          className="rounded-md border border-error/40 bg-surface p-3 text-sm text-text"
          data-testid="board-cancel-confirmation"
        >
          <strong className="text-error">Annuler la délibération engagée ?</strong>
          <p className="mt-1">
            Les appels en cours seront interrompus. Tu peux aussi masquer ce panneau et laisser le Board continuer en arrière-plan.
          </p>
          <div className="mt-3 flex justify-end gap-2">
            <Button variant="secondary" size="md" onClick={() => setCancelConfirmationOpen(false)}>
              Continuer en arrière-plan
            </Button>
            <Button
              variant="danger"
              size="md"
              onClick={() => { setCancelConfirmationOpen(false); onCancel(); }}
            >
              Confirmer l’annulation
            </Button>
          </div>
        </div>
      ) : (
        <div className="flex justify-end gap-2">
          {enCours ? (
            <Button
              variant="danger"
              size="md"
              className="gap-1.5"
              onClick={() => setCancelConfirmationOpen(true)}
            >
              <Square className={`${ICONE} fill-current`} />Annuler la délibération
            </Button>
          ) : (
            <Button variant="primary" size="md" onClick={onReset}>Nouvelle question</Button>
          )}
        </div>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Le formulaire
// ---------------------------------------------------------------------------

function NewBoardForm({
  advisors,
  run,
  onStart,
}: {
  advisors: AdvisorInfo[];
  run: BoardRunState;
  onStart: (request: BoardRequest) => Promise<void>;
}) {
  const [question, setQuestion] = useState('');
  const [context, setContext] = useState('');
  const [mode, setMode] = useState<BoardMode>('cloud');
  const [confirmationSnapshot, setConfirmationSnapshot] = useState<(BoardRequest & { advisorCount: number }) | null>(null);
  const [error, setError] = useState<string | null>(null);

  function validateSnapshot(snapshot: BoardRequest): string | null {
    if (snapshot.question.trim().length < 10) {
      return 'La question doit contenir au moins 10 caractères.';
    }
    if (snapshot.mode !== 'cloud' && snapshot.mode !== 'sovereign') {
      return 'Le mode de délibération figé est invalide.';
    }
    return null;
  }

  function requestConfirmation() {
    const snapshot = {
      question: question.trim(),
      context: context.trim() || undefined,
      mode,
      advisorCount: advisors.length || 5,
    };
    const validationError = validateSnapshot(snapshot);
    if (validationError) {
      setError(validationError);
      requestAnimationFrame(() => document.getElementById('board-question')?.focus());
      return;
    }
    setError(null);
    setConfirmationSnapshot(snapshot);
  }

  function confirmStart() {
    if (!confirmationSnapshot) return;
    const validationError = validateSnapshot(confirmationSnapshot);
    if (validationError) {
      setError(validationError);
      setConfirmationSnapshot(null);
      return;
    }
    if (confirmationSnapshot.mode === 'cloud') {
      // Consentement dédié au Board : il vaut pour l'ENSEMBLE des
      // fournisseurs configurés des conseillers (multi-fournisseurs).
      grantCloudConsent('llm', 'board', ['question', 'contexte utile', 'profil local utile', 'résultats web']);
    }
    void onStart({
      question: confirmationSnapshot.question,
      context: confirmationSnapshot.context,
      mode: confirmationSnapshot.mode,
    });
  }

  const classeDuMode = (actif: boolean) =>
    `rounded-md border p-3 text-left text-sm ${actif ? 'border-domaine-prospects bg-domaine-prospects-tint' : 'border-border'}`;

  return (
    <div className="space-y-4" data-testid="board-new-form">
      <fieldset
        disabled={confirmationSnapshot !== null}
        onChangeCapture={() => setConfirmationSnapshot(null)}
        className="contents [&:disabled>*]:opacity-70"
        data-testid="board-form-fields"
      >
        <Carte as="section" className="space-y-3 p-4">
          <FormField label="Question stratégique" htmlFor="board-question">
            <Textarea
              id="board-question"
              aria-label="Question stratégique"
              aria-invalid={Boolean(error)}
              aria-describedby={error ? 'board-form-error' : undefined}
              value={question}
              onChange={(event) => { setQuestion(event.target.value); setError(null); }}
              placeholder="Quelle décision veux-tu éclairer ?"
              className="h-28 leading-6"
            />
          </FormField>
          <FormField label="Contexte utile, facultatif" htmlFor="board-context">
            <Textarea
              id="board-context"
              aria-label="Contexte du Board"
              value={context}
              onChange={(event) => setContext(event.target.value)}
              placeholder="Contraintes, hypothèses, chiffres ou échéance…"
              className="h-24 leading-5"
            />
          </FormField>
        </Carte>

        <Carte as="section" className="p-4">
          <h3 id="board-mode-label" className="text-sm font-bold text-text">Mode de délibération</h3>
          <div className="mt-3 grid grid-cols-2 gap-2" role="radiogroup" aria-labelledby="board-mode-label">
            <button
              type="button"
              role="radio"
              aria-checked={mode === 'cloud'}
              tabIndex={mode === 'cloud' ? 0 : -1}
              onKeyDown={(event) => handleRovingFocus(event, '[role="radio"]', 'horizontal')}
              onClick={() => setMode('cloud')}
              className={classeDuMode(mode === 'cloud')}
            >
              <Globe aria-hidden="true" className={`${ICONE} text-domaine-prospects`} />
              <strong className="mt-2 block text-sm text-text">Cloud</strong>
              <span className="mt-1 block text-sm leading-4 text-text-muted">Services d’IA configurés et recherche web.</span>
            </button>
            <button
              type="button"
              role="radio"
              aria-checked={mode === 'sovereign'}
              tabIndex={mode === 'sovereign' ? 0 : -1}
              onKeyDown={(event) => handleRovingFocus(event, '[role="radio"]', 'horizontal')}
              onClick={() => setMode('sovereign')}
              className={classeDuMode(mode === 'sovereign')}
            >
              <ShieldCheck aria-hidden="true" className={`${ICONE} text-domaine-prospects`} />
              <strong className="mt-2 block text-sm text-text">Souverain</strong>
              <span className="mt-1 block text-sm leading-4 text-text-muted">Ollama local, sans recherche web.</span>
            </button>
          </div>
        </Carte>

        <Carte as="section" className="p-4">
          <div className="flex items-center gap-2 text-sm font-bold text-text">
            <Users aria-hidden="true" className={`${ICONE} text-domaine-prospects`} />
            Conseillers réellement configurés
          </div>
          <div className="mt-3 grid grid-cols-5 gap-2">
            {advisorOrder.map((role) => {
              const advisor = advisors.find((item) => item.role === role);
              return (
                <div key={role} className="text-center">
                  <CharacterPortrait index={advisorPortraits[role]} className="mx-auto h-9 w-9 rounded-sm border border-text" />
                  <span className="mt-1 block truncate text-sm text-text-muted">{advisor?.name || role}</span>
                </div>
              );
            })}
          </div>
        </Carte>
      </fieldset>

      {error && <p id="board-form-error" className="text-sm font-semibold text-error" role="alert">{error}</p>}

      {confirmationSnapshot && (
        <div className="rounded-md border border-accent-cyan/30 bg-accent-tint p-3" data-testid="board-confirmation">
          <div className="flex items-start gap-2 text-sm text-accent">
            <ShieldCheck aria-hidden="true" className={`${ICONE} shrink-0`} />
            <div>
              <strong>Confirmer le lancement du Board</strong>
              <p className="mt-1 font-semibold">Question : {confirmationSnapshot.question}</p>
              {confirmationSnapshot.context && <p>Contexte : {confirmationSnapshot.context}</p>}
              <p>Mode : {confirmationSnapshot.mode === 'cloud' ? 'Cloud avec recherche web' : 'Souverain via Ollama local'}</p>
              <p>Conseillers : {confirmationSnapshot.advisorCount}</p>
              <p className="mt-1 font-semibold">
                Le mode cloud transmet la question, le contexte, le profil local utile et les résultats web aux fournisseurs configurés. Jusqu’à six appels au service d’IA peuvent consommer des crédits.
              </p>
              {confirmationSnapshot.mode === 'sovereign' && (
                <p className="mt-1 font-semibold">Ollama doit être disponible. Aucun repli cloud ne sera effectué.</p>
              )}
            </div>
          </div>
          <div className="mt-3 flex justify-end gap-2">
            <Button variant="secondary" size="md" onClick={() => setConfirmationSnapshot(null)}>Annuler</Button>
            {/* `disabled` pendant un run : le filet contre un second POST. */}
            <Button
              variant="primary"
              size="md"
              className="gap-1.5"
              disabled={run.status === 'running'}
              onClick={confirmStart}
            >
              <Play className={`${ICONE} fill-current`} />Confirmer et lancer
            </Button>
          </div>
        </div>
      )}

      {!confirmationSnapshot && (
        <div className="flex justify-end">
          <Button variant="primary" size="md" className="gap-1.5" onClick={requestConfirmation}>
            <Gavel className={ICONE} />Préparer la délibération
          </Button>
        </div>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Le détail d'une décision enregistrée
// ---------------------------------------------------------------------------

function DecisionDetail({ decision }: { decision: BoardDecisionDetail }) {
  return (
    <div className="space-y-4" data-testid="board-decision-detail">
      <CarteQuestion question={decision.question} contexte={decision.context} meta={metaDuDetail(decision)} />
      <CarteSynthese synthesis={decision.synthesis} />
      <div className={GRILLE_AVIS}>
        {decision.opinions.map((opinion) => (
          <CarteAvisSauvegarde key={opinion.role} opinion={opinion} />
        ))}
      </div>
      <Divergences synthesis={decision.synthesis} />

      {decision.web_sources && decision.web_sources.length > 0 && (
        <Carte as="section" className="p-4">
          <h4 className="text-sm font-bold text-text">Extraits du moteur de recherche</h4>
          <div className="mt-3 space-y-2">
            {decision.web_sources.map((source) => (
              <a
                key={source.url}
                href={source.url}
                target="_blank"
                rel="noreferrer"
                className="flex items-start gap-2 rounded-md bg-surface-2 p-3 text-sm text-text hover:text-domaine-prospects"
              >
                <ExternalLink aria-hidden="true" className={`${ICONE} mt-0.5 shrink-0`} />
                <span>
                  <strong className="block">{source.title || source.url}</strong>
                  {source.snippet && (
                    <span className="mt-1 block text-sm leading-5 text-text-muted">{source.snippet}</span>
                  )}
                </span>
              </a>
            ))}
          </div>
        </Carte>
      )}

      {decision.synthesis_usage && (decision.synthesis_usage.provider || decision.synthesis_usage.model) && (
        <div className="rounded-md border border-accent-cyan/30 bg-accent-tint px-3 py-2 text-sm text-accent">
          Synthèse : {decision.synthesis_usage.provider || 'provider inconnu'} · {decision.synthesis_usage.model || 'modèle non mesuré'}
          {typeof decision.synthesis_usage.cost_eur === 'number' ? ` · ${formaterCout(decision.synthesis_usage.cost_eur, 4)}` : ''}
        </div>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Le canevas
// ---------------------------------------------------------------------------

export function BoardWorkspaceCanvas({
  resource,
  decisionResource,
  run,
  target,
  onRetry,
  onRetryDecision,
  onStart,
  onCancel,
  onReset,
  onOpenClassic,
}: {
  resource: ReadResource<BoardWorkspaceData>;
  decisionResource: ReadResource<BoardDecisionDetail> | null;
  run: BoardRunState;
  target: BoardTarget;
  onRetry: () => void;
  onRetryDecision: () => void;
  onStart: (request: BoardRequest) => Promise<void>;
  onCancel: () => void;
  onReset: () => void;
  onOpenClassic: () => void;
}) {
  const advisors = resource.status === 'ready' ? resource.data.advisors : [];
  const showRun = run.status !== 'idle' && (target === 'current' || target === 'new-board');

  return (
    <div className="flex h-full flex-col">
      {/* `pr-16` : le bouton Fermer est en absolu à droite du bandeau. */}
      <div className="border-b border-border px-5 py-4 pr-16">
        {/* Pas de `mt-2` : il réservait l'écart au sur-titre, parti avec le lot. */}
        <h2 className="text-xl font-bold tracking-[-0.02em] text-text">Décision</h2>
        <p className="mt-1 text-sm text-text-muted">
          Cinq regards, leurs divergences et une synthèse sauvegardée dans l’historique local.
        </p>
      </div>

      <div className="min-h-0 flex-1 overflow-y-auto p-5">
        {resource.status === 'loading' ? (
          <ChargementDuCanevas texte="Chargement du Board…" />
        ) : resource.status === 'error' ? (
          <Alerte
            titre={resource.error ?? undefined}
            icone={<AlertCircle className={ICONE} />}
            action={<Button variant="secondary" size="md" onClick={onRetry}>Réessayer</Button>}
          />
        ) : showRun ? (
          <BoardRunView run={run} advisors={advisors} onCancel={onCancel} onReset={onReset} />
        ) : target === 'new-board' || target === 'current' ? (
          <NewBoardForm advisors={advisors} run={run} onStart={onStart} />
        ) : !decisionResource || decisionResource.status === 'loading' ? (
          <ChargementDuCanevas texte="Chargement de la décision…" />
        ) : decisionResource.status === 'error' ? (
          <Alerte
            titre={decisionResource.error ?? undefined}
            icone={<AlertCircle className={ICONE} />}
            action={<Button variant="secondary" size="md" onClick={onRetryDecision}>Réessayer</Button>}
          />
        ) : (
          <DecisionDetail decision={decisionResource.data} />
        )}
      </div>

      <div className="border-t border-border bg-surface p-4">
        <BoutonOuvrirLaVue vue="board" onOuvrir={onOpenClassic} className={CLASSE_BOUTON_VUE} />
      </div>
    </div>
  );
}
