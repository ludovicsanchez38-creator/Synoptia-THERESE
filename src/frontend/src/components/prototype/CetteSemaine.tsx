/**
 * P-135 (persona Nathalie, cycle 13) : l'Accueil ne regardait qu'aujourd'hui.
 * Sa relance de jeudi n'apparaissait que jeudi, et ni l'encaissé ni le
 * pipeline n'y figuraient. « Cette semaine » montre ce qui vient sur sept
 * jours (relances datées, échéances de tâches) et deux chiffres, chacun avec
 * ce qu'il compte. Rien n'est inventé : un bloc illisible se dit tel quel.
 */
import { useEffect, useState } from 'react';
import { ChevronRight } from 'lucide-react';
import { fetchSemaineDashboard, type ElementDeLaSemaine, type SemaineDashboard } from '../../services/api/dashboard';
import { useDemoMask } from '../../hooks/useDemoMask';
import { PIPELINE_ETAPES } from '../crm/pipelineEtapes';

function jourDe(element: ElementDeLaSemaine): string {
  if (!element.date) return '';
  // B-1430 : un rendez-vous sur la journée arrive en « AAAA-MM-JJ », que
  // `new Date` lirait à minuit UTC (la veille à l'ouest de Greenwich).
  const civile = /^(\d{4})-(\d{2})-(\d{2})$/.exec(element.date);
  const jour = civile
    ? new Date(Number(civile[1]), Number(civile[2]) - 1, Number(civile[3]))
    : new Date(element.date);
  if (Number.isNaN(jour.getTime())) return '';
  return jour.toLocaleDateString('fr-FR', { weekday: 'long', day: 'numeric', month: 'short' });
}

function nomDuMois(mois: string): string {
  const [annee, numero] = mois.split('-').map(Number);
  if (!annee || !numero) return 'ce mois-ci';
  return new Date(annee, numero - 1, 1).toLocaleDateString('fr-FR', { month: 'long' });
}

function montant(valeur: number, devise: string): string {
  try {
    return new Intl.NumberFormat('fr-FR', { style: 'currency', currency: devise }).format(valeur);
  } catch {
    return `${valeur.toFixed(2)} ${devise}`;
  }
}

export function CetteSemaine({
  onOpenContact,
  onOpenTasks,
  onOpenAgenda,
}: {
  onOpenContact: (contactId: string) => void;
  onOpenTasks: () => void;
  /** B-1430 : un rendez-vous ouvre l'Agenda. */
  onOpenAgenda?: () => void;
}) {
  const [semaine, setSemaine] = useState<SemaineDashboard | null>(null);
  const [illisible, setIllisible] = useState(false);
  const { maskText } = useDemoMask();

  useEffect(() => {
    let vivant = true;
    fetchSemaineDashboard()
      .then((donnees) => { if (vivant) setSemaine(donnees); })
      .catch(() => { if (vivant) setIllisible(true); });
    return () => { vivant = false; };
  }, []);

  if (illisible) {
    return (
      <section aria-label="Cette semaine" className="mt-4 rounded-md border border-border bg-surface px-4 py-3">
        <h3 className="text-sm font-semibold text-text">Cette semaine</h3>
        <p className="mt-1 text-sm text-text-muted">La semaine n’a pas pu être lue.</p>
      </section>
    );
  }
  if (!semaine) return null;

  const pannes = new Set(semaine.indisponibles);
  const devises = Object.entries(semaine.encaisse_du_mois);
  // P-132 : le moteur décide seul de ce qui est un prospect en cours
  // (`ETAPES_DE_PROSPECT`, dashboard.py) ; l'écran range ce qu'il reçoit dans
  // l'ordre du pipeline. Une clé inconnue n'est ni affichée ni comptée : elle
  // n'aurait pas de libellé.
  const etapes = PIPELINE_ETAPES.filter((etape) => (semaine.prospects_par_etape[etape.id] ?? 0) > 0);
  const totalProspects = etapes.reduce((total, etape) => total + (semaine.prospects_par_etape[etape.id] ?? 0), 0);

  return (
    <section aria-label="Cette semaine" className="mt-4 rounded-md border border-border bg-surface px-4 py-3">
      <h3 className="text-sm font-semibold text-text">Cette semaine</h3>

      {pannes.has('semaine') ? (
        <p className="mt-1 text-sm text-text-muted">Les relances, rendez-vous et échéances à venir n’ont pas pu être lus.</p>
      ) : semaine.a_venir.length === 0 ? (
        <p className="mt-1 text-sm text-text-muted">Rien de daté dans les sept prochains jours.</p>
      ) : (
        <ul className="mt-2 grid gap-1">
          {semaine.a_venir.map((element) => (
            <li key={`${element.kind}-${element.id}`}>
              <button
                type="button"
                onClick={() => {
                  if (element.kind === 'rdv') onOpenAgenda?.();
                  else if (element.contact_id) onOpenContact(element.contact_id);
                  else onOpenTasks();
                }}
                className="flex w-full items-center gap-2 rounded-sm px-2 py-1.5 text-left text-sm hover:bg-surface-2 focus:outline-none focus-visible:ring-2 focus-visible:ring-ring"
              >
                <span className="min-w-0 flex-1">
                  <span className="font-medium text-text">{maskText(element.titre)}</span>
                  <span className="text-text-muted"> · {jourDe(element)}</span>
                </span>
                <ChevronRight className="h-4 w-4 shrink-0 text-text-muted" aria-hidden="true" />
              </button>
            </li>
          ))}
        </ul>
      )}

      <dl className="mt-3 grid gap-2 border-t border-border pt-3 text-sm sm:grid-cols-2">
        <div>
          <dt className="font-medium text-text">Encaissé en {nomDuMois(semaine.mois)}</dt>
          <dd className="text-text-muted">
            {pannes.has('encaisse')
              ? 'L’encaissé n’a pas pu être lu.'
              : devises.length === 0
                ? 'Aucune facture payée ce mois-ci.'
                : devises.map(([devise, valeur]) => montant(valeur, devise)).join(' · ')}
            {!pannes.has('encaisse') && devises.length > 0 && (
              <span className="block">Source : factures payées ce mois-ci, avoirs non déduits.</span>
            )}
          </dd>
        </div>
        <div>
          <dt className="font-medium text-text">Prospects en cours : {pannes.has('pipeline') ? '?' : totalProspects}</dt>
          <dd className="text-text-muted">
            {pannes.has('pipeline')
              ? 'Le pipeline n’a pas pu être lu.'
              : totalProspects === 0
                ? 'Aucune fiche aux étapes de prospect.'
                : etapes.map((etape) => `${etape.label} ${semaine.prospects_par_etape[etape.id]}`).join(', ')}
            {!pannes.has('pipeline') && totalProspects > 0 && (
              <span className="block">Source : fiches du pipeline, avant l’étape Livraison.</span>
            )}
          </dd>
        </div>
      </dl>
    </section>
  );
}
