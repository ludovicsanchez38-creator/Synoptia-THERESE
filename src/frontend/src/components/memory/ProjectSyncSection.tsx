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
import { MARQUEUR_DELAI } from '../../services/api/core';
import { useDemoMask } from '../../hooks/useDemoMask';
import { useDemoStore } from '../../stores/demoStore';
import { Button } from '../ui/Button';
import { Spinner } from '../ui/Spinner';
import { Alerte } from '../ui/Alerte';
import { Carte } from '../ui/Carte';
import { Input } from '../ui/Input';

interface Props {
  projectId: string;
  /** Masque local du parent, notamment avant le peuplement du store démo. */
  maskDisplayText?: (text: string) => string;
}

interface ContexteSync { projectId: string }

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
  const texte = e instanceof Error ? e.message : '';
  // Un délai peut remonter sous le nom générique `AbortError` selon le moteur.
  // On le reconnaît alors à NOTRE propre message, jamais à une chaîne devinée.
  const estUnDelai = nom === 'TimeoutError' || texte.startsWith(MARQUEUR_DELAI);
  if (estUnDelai) {
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

export function ProjectSyncSection({ projectId, maskDisplayText }: Props) {
  const { enabled: modeDemo, maskText: masqueGlobal } = useDemoMask();
  const maskText = maskDisplayText ?? masqueGlobal;
  const [etat, setEtat] = useState<api.SyncEtat | null>(null);
  const [chargement, setChargement] = useState(true);
  const [erreurLecture, setErreurLecture] = useState<string | null>(null);
  const [plan, setPlan] = useState<api.SyncPlan | null>(null);
  const [chemin, setChemin] = useState('');
  const [occupe, setOccupe] = useState<string | null>(null);
  const [erreur, setErreur] = useState<string | null>(null);
  // P-027 : délier ne retire rien de l'index, c'est un choix ; on le dit.
  const [info, setInfo] = useState<string | null>(null);
  const [journal, setJournal] = useState<api.SyncOperation[]>([]);
  const sondage = useRef<ReturnType<typeof setInterval> | null>(null);
  const lectureCourante = useRef(0);
  const contexteCourant = useRef<ContexteSync | null>(null);
  const contexteDuPlan = useRef<ContexteSync | null>(null);
  const estCourant = useCallback((contexte: ContexteSync | null) => (
    contexte !== null && contexteCourant.current === contexte
  ), []);

  const charger = useCallback(async (contexte = contexteCourant.current) => {
    if (!contexte || !estCourant(contexte)) return null;
    const lecture = ++lectureCourante.current;
    setChargement(true);
    setErreurLecture(null);
    try {
      const e = await api.etatSync(contexte.projectId);
      if (!estCourant(contexte) || lecture !== lectureCourante.current) return null;
      setEtat(e);
      return e;
    } catch (e) {
      if (estCourant(contexte) && lecture === lectureCourante.current) {
        setErreurLecture(messageDEchec(e, 'Impossible de lire le dossier synchronisé.'));
      }
      return null;
    } finally {
      if (estCourant(contexte) && lecture === lectureCourante.current) setChargement(false);
    }
  }, [estCourant]);

  useEffect(() => {
    // L'identité du contexte distingue aussi A -> B -> A : aucun retour de
    // la première ouverture de A ne peut piloter la seconde.
    const contexte = { projectId };
    contexteCourant.current = contexte;
    contexteDuPlan.current = null;
    setEtat(null);
    setPlan(null);
    setJournal([]);
    setChemin('');
    setInfo(null);
    setErreur(null);
    setOccupe(null);
    void charger(contexte);
    return () => {
      contexteCourant.current = null;
      lectureCourante.current += 1;
      if (sondage.current) clearInterval(sondage.current);
      sondage.current = null;
    };
  }, [projectId, charger]);

  const attacher = async () => {
    const contexte = contexteCourant.current;
    if (useDemoStore.getState().enabled || !contexte || contexte.projectId !== projectId) return;
    setOccupe('racine');
    setErreur(null);
    setInfo(null);
    try {
      await api.definirRacineSync(projectId, chemin.trim());
      if (!estCourant(contexte)) return;
      setChemin('');
      await charger(contexte);
    } catch (e) {
      if (!estCourant(contexte)) return;
      setErreur(messageDEchec(e, "Impossible d'attacher ce dossier"));
      // Quand le client abandonne, le serveur poursuit : la racine peut être
      // posée alors qu'on affiche un échec. On relit l'état plutôt que de
      // laisser l'écran mentir.
      await charger(contexte);
    } finally {
      if (estCourant(contexte)) setOccupe(null);
    }
  };

  const delier = async () => {
    const contexte = contexteCourant.current;
    if (useDemoStore.getState().enabled || !contexte || contexte.projectId !== projectId) return;
    setOccupe('racine');
    setErreur(null);
    setInfo(null);
    try {
      await api.retirerRacineSync(projectId);
      if (!estCourant(contexte)) return;
      contexteDuPlan.current = null;
      setPlan(null);
      // Audit 0.74 : nommer le geste qui existe (la liste des fichiers de la fiche du projet), pas une « purge » introuvable.
      setInfo('Dossier délié. Les documents déjà indexés restent consultables dans la mémoire ; pour les retirer, supprime-les depuis la fiche du projet.');
      await charger(contexte);
    } catch (e) {
      if (!estCourant(contexte)) return;
      // D4 : sans catch, l'échec partait en promesse rejetée et l'écran
      // gardait un dossier que le serveur n'avait pas délié.
      setErreur(messageDEchec(e, 'Impossible de délier ce dossier'));
      await charger(contexte);
    } finally {
      if (estCourant(contexte)) setOccupe(null);
    }
  };

  const preparer = async () => {
    const contexte = contexteCourant.current;
    if (useDemoStore.getState().enabled || !contexte || contexte.projectId !== projectId) return;
    setOccupe('plan');
    setErreur(null);
    setInfo(null);
    contexteDuPlan.current = null;
    setPlan(null);
    try {
      const p = await api.preparerPlanSync(projectId);
      if (!estCourant(contexte)) return;
      contexteDuPlan.current = contexte;
      setPlan(p);
      await charger(contexte);
    } catch (e) {
      if (!estCourant(contexte)) return;
      setErreur(
        messageDEchec(e, 'Aucun plan produit, réessaie.'),
      );
    } finally {
      if (estCourant(contexte)) setOccupe(null);
    }
  };

  const appliquer = async () => {
    const contexte = contexteCourant.current;
    if (useDemoStore.getState().enabled || !plan || !contexte
      || contexte.projectId !== projectId || contexteDuPlan.current !== contexte) return;
    setOccupe('apply');
    setErreur(null);
    setInfo(null);
    try {
      await api.appliquerPlanSync(projectId, plan.id);
      if (!estCourant(contexte)) return;
      // 202 : suivre l'avancement par l'état - sondage BORNÉ (revue jalon,
      // B7) : cinq erreurs consécutives ou vingt minutes arrêtent la boucle
      // avec un message, jamais un spinner éternel.
      let erreursConsecutives = 0;
      let ticks = 0;
      let lectureEnCours = false;
      const timer = setInterval(async () => {
        if (!estCourant(contexte)) return;
        ticks += 1;
        if (lectureEnCours) return;
        lectureEnCours = true;
        const lecture = ++lectureCourante.current;
        let e: api.SyncEtat | null = null;
        try {
          e = await api.etatSync(projectId);
          if (!estCourant(contexte) || lecture !== lectureCourante.current) return;
          setEtat(e);
          erreursConsecutives = 0;
        } catch {
          if (!estCourant(contexte) || lecture !== lectureCourante.current) return;
          erreursConsecutives += 1;
        } finally {
          lectureEnCours = false;
        }
        const etatPlan = e?.dernier_plan?.etat;
        const termine = etatPlan && etatPlan !== 'propose' && etatPlan !== 'en_cours';
        const aBout = erreursConsecutives >= 5 || ticks >= 1200;
        if (termine || aBout) {
          clearInterval(timer);
          if (sondage.current === timer) sondage.current = null;
          setOccupe(null);
          contexteDuPlan.current = null;
          setPlan(null);
          if (aBout && !termine) {
            setErreur(
              "Impossible de suivre la synchronisation - vérifie l'état du projet.",
            );
          } else {
            void chargerJournal(contexte);
          }
        }
      }, 1000);
      sondage.current = timer;
    } catch (e) {
      if (!estCourant(contexte)) return;
      setOccupe(null);
      setErreur(e instanceof Error ? e.message : "L'application a échoué");
    }
  };

  const chargerJournal = async (contexte: ContexteSync) => {
    if (!estCourant(contexte)) return;
    try {
      const j = await api.journalSync(contexte.projectId);
      if (!estCourant(contexte)) return;
      setJournal(j.operations.slice(0, 10));
    } catch {
      // le journal est un confort : son échec ne masque pas le résultat
    }
  };

  const dernier = etat?.dernier_plan;

  return (
    <Carte as="section" className="space-y-3 p-3">
      <div className="flex items-center gap-2">
        <FolderSync className="w-4 h-4 text-accent" />
        <h4 className="text-sm font-medium text-text">Dossier synchronisé</h4>
      </div>

      {modeDemo && (
        <p className="text-sm text-text-muted">
          Dossier en lecture seule. Désactive le mode démo pour le modifier.
        </p>
      )}

      {erreurLecture && (
        <Alerte
          titre="Dossier synchronisé indisponible"
          action={<Button variant="secondary" size="sm" onClick={() => void charger()} disabled={chargement}>Réessayer</Button>}
        >
          {maskText(erreurLecture)}
        </Alerte>
      )}

      {etat === null ? (
        chargement && <p role="status" className="flex items-center gap-2 text-sm text-text-muted"><Spinner taille="ligne" />Chargement du dossier synchronisé…</p>
      ) : !etat.racine ? (
        <div className="space-y-2">
          <p className="text-sm text-text-muted">
            Attache un dossier local : THÉRÈSE proposera un plan d'indexation à
            chaque synchronisation, et n'appliquera jamais rien sans ton accord.
          </p>
          <div className="flex flex-wrap gap-2">
            <div className="min-w-0 flex-1 max-[840px]:basis-full">
              <Input
                aria-label="Chemin du dossier à synchroniser"
                type="text"
                value={maskText(chemin)}
                disabled={modeDemo}
                onChange={(e) => setChemin(e.target.value)}
                placeholder="/Users/toi/Documents/mon-projet"
              />
            </div>
            <Button
              size="sm"
              onClick={() => void attacher()}
              disabled={modeDemo || occupe !== null || !chemin.trim()}
            >
              {occupe === 'racine' ? <Spinner taille="bouton" /> : 'Attacher'}
            </Button>
          </div>
        </div>
      ) : (
        <div className="space-y-2">
          <div className="flex items-center justify-between gap-2">
            <code className="text-sm text-text-muted truncate">{maskText(etat.racine)}</code>
            <Button
              type="button"
              variant="ghost"
              size="icon"
              onClick={() => void delier()}
              disabled={modeDemo || occupe !== null}
              className="text-text-muted hover:text-error"
              aria-label="Délier le dossier"
              title="Délier (ne retire rien de l'index)"
            >
              <Unlink className="w-4 h-4" />
            </Button>
          </div>

          <div className="flex flex-wrap gap-2">
            <Button
              size="sm"
              variant="secondary"
              onClick={() => void preparer()}
              disabled={modeDemo || occupe !== null}
            >
              {occupe === 'plan'
                ? <Spinner taille="bouton" />
                : <><RefreshCw className="w-4 h-4 mr-1" />Préparer la synchronisation</>}
            </Button>
            {plan && plan.etat === 'propose' && (
              <Button
                size="sm"
                onClick={() => void appliquer()}
                disabled={modeDemo || occupe !== null}
              >
                {occupe === 'apply'
                  ? <Spinner taille="bouton" />
                  : <><Play className="w-4 h-4 mr-1" />Appliquer</>}
              </Button>
            )}
          </div>

          {plan && (
            <div className="text-sm text-text-muted space-y-1" data-testid="sync-plan">
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
                      <span className="uppercase text-xs mr-1">{o.type}</span>
                      {maskText(o.chemin.split('/').pop() ?? '')}
                    </li>
                  ))}
                </ul>
              )}
            </div>
          )}

          {occupe === 'apply' && (
            <p className="text-sm text-text-muted" role="status">
              Synchronisation en cours…
              {etat?.run?.progression != null && (
                <> {Math.round(etat.run.progression * 100)} %</>
              )}
            </p>
          )}

          {journal.length > 0 && occupe === null && (
            <div className="text-sm text-text-muted space-y-0.5" data-testid="sync-journal">
              <p className="font-medium">Dernières opérations :</p>
              <ul className="max-h-24 overflow-y-auto">
                {journal.map((o) => (
                  <li key={o.id} className="truncate">
                    <span className="uppercase text-xs mr-1">{o.type}</span>
                    {maskText(o.chemin.split('/').pop() ?? '')}
                    <span className="ml-1">({o.etat}{o.erreur ? ` - ${maskText(o.erreur)}` : ''})</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {dernier && !plan && occupe !== 'apply' && (
            <p className="text-sm text-text-muted">
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
        <Alerte>{maskText(erreur)}</Alerte>
      )}
      {info && (
        <p className="text-sm text-text-muted" role="status" data-testid="sync-info">{info}</p>
      )}
    </Carte>
  );
}
