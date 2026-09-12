/**
 * THÉRÈSE v2 - PistesPanel (Atelier documentaire, D4)
 *
 * Volet droit repliable de l'atelier : pistes détectées pendant la rédaction
 * (bloc PISTES du backend, B3). V1 volontairement minimal - capturer, puis
 * explorer ou ignorer, RIEN de plus (pas de réglages de relance, pas
 * d'édition du texte de la piste - hors périmètre D4).
 *
 * Composant présentationnel (props uniquement, aucun accès direct au store)
 * - même découplage que OutlineTree/SectionEditor ; le pont avec
 * `documentStore` (updatePiste + sélection de la section d'origine +
 * préremplissage de l'instruction) est fait par `DocumentWorkspace`.
 *
 * Badge compteur : rond (dette DA connue - seuls les tags de STATUT sont des
 * carrés `rounded-sm`, les compteurs restent ronds, cf. le badge cloche de
 * `NotificationCenter.tsx`) mais en tokens sémantiques (bg-accent-fill /
 * text-accent-ink), jamais la couleur brute Tailwind que porte ce précédent.
 *
 * Pistes explorées/ignorées : conservées (jamais supprimées), reléguées dans
 * une sous-liste repliée par défaut « Pistes traitées » pour ne pas polluer
 * la liste active.
 */
import { useEffect, useRef, useState } from 'react';
import { ChevronDown, ChevronRight, Compass, Lightbulb, PanelRightClose, PanelRightOpen, X } from 'lucide-react';
import { Button } from '../ui/Button';
import { Carte } from '../ui/Carte';
import { EtatVide } from '../ui/EtatVide';
import { Etiquette } from '../ui/Etiquette';
import type { DocumentPiste, PisteStatus } from '../../services/api/documents';

// =============================================================================
// STATUTS (tags carrés theme-aware, même famille que OutlineTree/SectionEditor)
// =============================================================================

const STATUS_META: Record<PisteStatus, { label: string; ton: 'info' | 'succes' | 'neutre' }> = {
  nouvelle: { label: 'Nouvelle', ton: 'info' },
  exploree: { label: 'Explorée', ton: 'succes' },
  ignoree: { label: 'Ignorée', ton: 'neutre' },
};

function StatusTag({ status }: { status: PisteStatus }) {
  const meta = STATUS_META[status];
  return (
    <Etiquette ton={meta.ton}>
      {meta.label}
    </Etiquette>
  );
}

function CounterBadge({ count }: { count: number }) {
  if (count === 0) return null;
  return (
    <span
      className="min-w-[18px] h-[18px] flex items-center justify-center text-xs font-bold rounded-full px-1 bg-accent-fill text-accent-ink"
      aria-label={`${count} nouvelle${count > 1 ? 's' : ''} piste${count > 1 ? 's' : ''}`}
    >
      {count > 99 ? '99+' : count}
    </span>
  );
}

// =============================================================================
// PROPS
// =============================================================================

export interface PistesPanelProps {
  pistes: DocumentPiste[];
  onExplore: (piste: DocumentPiste) => void;
  onIgnore: (piste: DocumentPiste) => void;
}

// =============================================================================
// COMPOSANT
// =============================================================================

export function PistesPanel({ pistes, onExplore, onIgnore }: PistesPanelProps) {
  const [collapsed, setCollapsed] = useState(false);
  const [showTraitees, setShowTraitees] = useState(false);
  const boutonDeplierRef = useRef<HTMLButtonElement>(null);
  const boutonReplierRef = useRef<HTMLButtonElement>(null);
  const premierRendu = useRef(true);

  // B-288 : le bouton qui bascule le volet se démonte avec lui. Sans ce
  // transfert, le focus retombait sur <body> et la tabulation suivante
  // repartait du haut de la page (RULES-DESIGN §9.2, WCAG 2.4.3). On ne
  // reprend le focus que s'il a été PERDU - jamais s'il est déjà posé
  // ailleurs par l'utilisateur.
  useEffect(() => {
    if (premierRendu.current) {
      premierRendu.current = false;
      return;
    }
    const actif = document.activeElement;
    if (actif && actif !== document.body) return;
    (collapsed ? boutonDeplierRef : boutonReplierRef).current?.focus();
  }, [collapsed]);

  const nouvelles = pistes.filter((p) => p.status === 'nouvelle');
  const traitees = pistes.filter((p) => p.status !== 'nouvelle');

  if (collapsed) {
    return (
      <div
        className="w-12 shrink-0 border-l border-border/40 flex flex-col items-center py-3"
        data-testid="pistes-panel-collapsed"
      >
        <Button
          variant="ghost"
          size="icon"
          ref={boutonDeplierRef}
          onClick={() => setCollapsed(false)}
          className="relative"
          aria-label="Déplier le volet Pistes"
          title="Pistes"
        >
          <PanelRightOpen className="w-4 h-4 text-text-muted" />
          <span className="absolute -top-1 -right-1">
            <CounterBadge count={nouvelles.length} />
          </span>
        </Button>
      </div>
    );
  }

  return (
    <div className="w-72 shrink-0 border-l border-border/40 flex flex-col overflow-y-auto" data-testid="pistes-panel">
      <div className="flex items-center justify-between gap-2 px-3 py-2.5 border-b border-border/40 shrink-0">
        <div className="flex items-center gap-2 min-w-0">
          <Lightbulb className="w-4 h-4 text-text-muted shrink-0" />
          <h2 className="text-sm font-semibold uppercase tracking-wide text-text-muted">Pistes</h2>
          <CounterBadge count={nouvelles.length} />
        </div>
        <Button
          variant="ghost"
          size="icon"
          ref={boutonReplierRef}
          onClick={() => setCollapsed(true)}
          aria-label="Replier le volet Pistes"
          title="Replier"
        >
          <PanelRightClose className="w-4 h-4" />
        </Button>
      </div>

      <div className="flex-1 py-1">
        {nouvelles.length === 0 ? (
          <EtatVide titre="Aucune piste pour l'instant" className="px-3 py-6">
            Elles apparaissent pendant la rédaction des sections.
          </EtatVide>
        ) : (
          <ul className="space-y-2 px-3 py-2">
            {nouvelles.map((piste) => (
              <li key={piste.id} data-testid="piste-item">
                <Carte as="section" className="p-2.5 space-y-2">
                  <p className="text-sm text-text leading-snug">{piste.texte}</p>
                  <div className="flex flex-wrap items-center gap-1.5">
                    <Button variant="secondary" size="sm" onClick={() => onExplore(piste)} className="flex-1">
                      <Compass className="w-3.5 h-3.5 mr-1.5" />
                      Explorer
                    </Button>
                    <Button variant="ghost" size="sm" onClick={() => onIgnore(piste)}>
                      <X className="w-3.5 h-3.5 mr-1.5" />
                      Ignorer
                    </Button>
                  </div>
                </Carte>
              </li>
            ))}
          </ul>
        )}

        {traitees.length > 0 && (
          <div className="border-t border-border/30 mt-1 pt-1">
            <Button
              variant="ghost"
              size="md"
              onClick={() => setShowTraitees((v) => !v)}
              className="w-full justify-start"
              aria-expanded={showTraitees}
            >
              {showTraitees ? <ChevronDown className="w-3.5 h-3.5" /> : <ChevronRight className="w-3.5 h-3.5" />}
              Pistes traitées ({traitees.length})
            </Button>
            {showTraitees && (
              <ul className="space-y-1.5 px-3 pb-2">
                {traitees.map((piste) => (
                  <li
                    key={piste.id}
                    className="rounded-md border border-border/30 bg-surface/30 p-2 flex items-start justify-between gap-2"
                    data-testid="piste-item-traitee"
                  >
                    <p className="text-sm text-text-muted leading-snug flex-1 min-w-0">{piste.texte}</p>
                    <StatusTag status={piste.status} />
                  </li>
                ))}
              </ul>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
