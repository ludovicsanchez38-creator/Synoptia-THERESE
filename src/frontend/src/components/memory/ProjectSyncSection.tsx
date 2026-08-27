/**
 * project.sync (0.45) - la section « Dossier synchronisé » d'une fiche projet.
 *
 * Le contrat produit, tel que challengé : rien ne se fait sans un plan
 * MONTRÉ puis APPLIQUÉ explicitement. Un montage débranché affiche une
 * erreur, jamais un plan de retrait massif. Les conflits (fichiers possédés
 * par un autre périmètre) sont montrés, jamais exécutés.
 */
import { useCallback, useEffect, useRef, useState } from 'react';
import { FolderSync, Play, RefreshCw, Unlink } from 'lucide-react';

import * as api from '../../services/api';
import { Button } from '../ui/Button';
import { Spinner } from '../ui/Spinner';

interface Props {
  projectId: string;
}

/**
 * Ce que l'écran dit d'un échec (D4, D5).
 *
 * Le composant affichait `e.message` brut : « Délai de 30000 ms dépassé » est
 * du jargon, il ne dit ni ce qui s'est passé ni quoi faire. Les refus du
 * serveur, eux, portent des messages écrits pour l'utilisateur (« cette racine
 * appartient déjà à un autre projet ») : ceux-là passent tels quels.
 *
 * On lit le NOM de l'erreur, jamais son texte : parser une chaîne pour deviner
 * une cause casse à la première reformulation.
 */
function messageDEchec(e: unknown, action: string): string {
  const nom = (e as { name?: string } | null)?.name;
  if (nom === 'TimeoutError') {
    return (
      'Le dossier met trop de temps à répondre. Cela arrive sur un disque '
      + 'réseau ou quand un antivirus analyse le dossier. Vérifie que le '
      + 'dossier est accessible, puis réessaie : si le serveur a fini entre '
      + 'temps, l’état ci-dessus est déjà à jour.'
    );
  }
  if (nom === 'AbortError') return 'Opération interrompue.';
  return e instanceof Error ? e.message : action;
}

export function ProjectSyncSection({ projectId }: Props) {
  const [etat, setEtat] = useState<api.SyncEtat | null>(null);
  const [plan, setPlan] = useState<api.SyncPlan | null>(null);
  const [chemin, setChemin] = useState('');
  const [occupe, setOccupe] = useState<string | null>(null);
  const [erreur, setErreur] = useState<string | null>(null);
  const [journal, setJournal] = useState<api.SyncOperation[]>([]);
  const sondage = useRef<ReturnType<typeof setInterval> | null>(null);

  const charger = useCallback(async () => {
    try {
      const e = await api.etatSync(projectId);
      setEtat(e);
      return e;
    } catch {
      return null;
    }
  }, [projectId]);

  useEffect(() => {
    void charger();
    return () => {
      if (sondage.current) clearInterval(sondage.current);
    };
  }, [charger]);

  const attacher = async () => {
    setOccupe('racine');
    setErreur(null);
    try {
      await api.definirRacineSync(projectId, chemin.trim());
      setChemin('');
      await charger();
    } catch (e) {
      setErreur(messageDEchec(e, "Impossible d'attacher ce dossier"));
      // Quand le client abandonne, le serveur poursuit : la racine peut être
      // posée alors qu'on affiche un échec. On relit l'état plutôt que de
      // laisser l'écran mentir.
      await charger().catch(() => undefined);
    } finally {
      setOccupe(null);
    }
  };

  const delier = async () => {
    setOccupe('racine');
    setErreur(null);
    try {
      await api.retirerRacineSync(projectId);
      setPlan(null);
      await charger();
    } catch (e) {
      // D4 : sans catch, l'échec partait en promesse rejetée et l'écran
      // gardait un dossier que le serveur n'avait pas délié.
      setErreur(messageDEchec(e, 'Impossible de délier ce dossier'));
      await charger().catch(() => undefined);
    } finally {
      setOccupe(null);
    }
  };

  const preparer = async () => {
    setOccupe('plan');
    setErreur(null);
    setPlan(null);
    try {
      const p = await api.preparerPlanSync(projectId);
      setPlan(p);
      await charger();
    } catch (e) {
      setErreur(
        messageDEchec(e, 'Aucun plan produit, réessaie.'),
      );
    } finally {
      setOccupe(null);
    }
  };

  const appliquer = async () => {
    if (!plan) return;
    setOccupe('apply');
    setErreur(null);
    try {
      await api.appliquerPlanSync(projectId, plan.id);
      // 202 : suivre l'avancement par l'état - sondage BORNÉ (revue jalon,
      // B7) : cinq erreurs consécutives ou vingt minutes arrêtent la boucle
      // avec un message, jamais un spinner éternel.
      let erreursConsecutives = 0;
      let ticks = 0;
      sondage.current = setInterval(async () => {
        ticks += 1;
        let e: api.SyncEtat | null = null;
        try {
          e = await api.etatSync(projectId);
          setEtat(e);
          erreursConsecutives = 0;
        } catch {
          erreursConsecutives += 1;
        }
        const etatPlan = e?.dernier_plan?.etat;
        const termine = etatPlan && etatPlan !== 'propose' && etatPlan !== 'en_cours';
        const aBout = erreursConsecutives >= 5 || ticks >= 1200;
        if (termine || aBout) {
          if (sondage.current) clearInterval(sondage.current);
          setOccupe(null);
          setPlan(null);
          if (aBout && !termine) {
            setErreur(
              "Impossible de suivre la synchronisation - vérifie l'état du projet.",
            );
          } else {
            void chargerJournal();
          }
        }
      }, 1000);
    } catch (e) {
      setOccupe(null);
      setErreur(e instanceof Error ? e.message : "L'application a échoué");
    }
  };

  const chargerJournal = async () => {
    try {
      const j = await api.journalSync(projectId);
      setJournal(j.operations.slice(0, 10));
    } catch {
      // le journal est un confort : son échec ne masque pas le résultat
    }
  };

  const dernier = etat?.dernier_plan;

  return (
    <div className="space-y-3 p-3 rounded-[6px] border-[1.5px] border-border bg-surface">
      <div className="flex items-center gap-2">
        <FolderSync className="w-4 h-4 text-accent" />
        <h4 className="text-sm font-medium text-text">Dossier synchronisé</h4>
      </div>

      {!etat?.racine ? (
        <div className="space-y-2">
          <p className="text-xs text-text-muted">
            Attache un dossier local : THÉRÈSE proposera un plan d'indexation à
            chaque synchronisation, et n'appliquera jamais rien sans ton accord.
          </p>
          <div className="flex gap-2">
            <input
              aria-label="Chemin du dossier à synchroniser"
              type="text"
              value={chemin}
              onChange={(e) => setChemin(e.target.value)}
              placeholder="/Users/toi/Documents/mon-projet"
              className="flex-1 px-3 py-2 text-sm rounded-[6px] border-[1.5px] border-border bg-background text-text placeholder:text-text-muted focus:outline-none focus:border-accent"
            />
            <Button
              size="sm"
              onClick={() => void attacher()}
              disabled={occupe !== null || !chemin.trim()}
            >
              {occupe === 'racine' ? <Spinner taille="bouton" /> : 'Attacher'}
            </Button>
          </div>
        </div>
      ) : (
        <div className="space-y-2">
          <div className="flex items-center justify-between gap-2">
            <code className="text-xs text-text-muted truncate">{etat.racine}</code>
            <button
              type="button"
              onClick={() => void delier()}
              disabled={occupe !== null}
              className="text-text-muted hover:text-error disabled:opacity-40 disabled:pointer-events-none"
              aria-label="Délier le dossier"
              title="Délier (ne retire rien de l'index)"
            >
              <Unlink className="w-4 h-4" />
            </button>
          </div>

          <div className="flex gap-2">
            <Button
              size="sm"
              variant="secondary"
              onClick={() => void preparer()}
              disabled={occupe !== null}
            >
              {occupe === 'plan'
                ? <Spinner taille="bouton" />
                : <><RefreshCw className="w-4 h-4 mr-1" />Préparer la synchronisation</>}
            </Button>
            {plan && plan.etat === 'propose' && (
              <Button
                size="sm"
                onClick={() => void appliquer()}
                disabled={occupe !== null}
              >
                {occupe === 'apply'
                  ? <Spinner taille="bouton" />
                  : <><Play className="w-4 h-4 mr-1" />Appliquer</>}
              </Button>
            )}
          </div>

          {plan && (
            <div className="text-xs text-text-muted space-y-1" data-testid="sync-plan">
              <p>
                {plan.nb_indexer} à indexer, {plan.nb_reindexer} à réindexer,{' '}
                {plan.nb_retirer} à retirer, {plan.nb_inchanges} inchangés
                {plan.nb_conflits > 0 && (
                  <span className="text-error"> - {plan.nb_conflits} en conflit (non exécutés)</span>
                )}
              </p>
              {plan.operations && plan.operations.length > 0 && (
                <ul className="max-h-32 overflow-y-auto space-y-0.5">
                  {plan.operations.slice(0, 50).map((o) => (
                    <li key={o.id} className="truncate">
                      <span className="uppercase text-[10px] mr-1">{o.type}</span>
                      {o.chemin.split('/').pop()}
                    </li>
                  ))}
                </ul>
              )}
            </div>
          )}

          {occupe === 'apply' && (
            <p className="text-xs text-text-muted" role="status">
              Synchronisation en cours…
              {etat?.run?.progression != null && (
                <> {Math.round(etat.run.progression * 100)} %</>
              )}
            </p>
          )}

          {journal.length > 0 && occupe === null && (
            <div className="text-xs text-text-muted space-y-0.5" data-testid="sync-journal">
              <p className="font-medium">Dernières opérations :</p>
              <ul className="max-h-24 overflow-y-auto">
                {journal.map((o) => (
                  <li key={o.id} className="truncate">
                    <span className="uppercase text-[10px] mr-1">{o.type}</span>
                    {o.chemin.split('/').pop()}
                    <span className="ml-1">({o.etat}{o.erreur ? ` - ${o.erreur}` : ''})</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {dernier && !plan && occupe !== 'apply' && (
            <p className="text-xs text-text-muted">
              Dernière synchronisation : {dernier.etat === 'applique'
                ? 'appliquée'
                : dernier.etat === 'applique_partiel'
                  ? 'partielle (des éléments restent à traiter)'
                  : dernier.etat}
            </p>
          )}
        </div>
      )}

      {erreur && (
        <p className="text-xs text-error" role="alert">{erreur}</p>
      )}
    </div>
  );
}
