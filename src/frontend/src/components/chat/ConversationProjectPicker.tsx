import { useCallback, useEffect, useState } from 'react';
import { FolderTree } from 'lucide-react';

import { listProjects } from '../../services/api';
import {
  ConversationEphemereError,
  rattacherAUnProjet,
} from '../../lib/rattachementConversation';
import { useStatusStore } from '../../stores/statusStore';

interface ProjetAffichable {
  id: string;
  name: string;
}

/** Valeur du sélecteur pour « aucune cloison » — distincte de la chaîne vide,
 *  qui vaut « documents généraux uniquement ». */
const TOUS_LES_PROJETS = '__tous__';

interface ConversationProjectPickerProps {
  conversationId: string;
  projectId: string | null;
  memoryScope?: string;
  /**
   * Le troisième argument est l'identifiant que le SERVEUR connaît : il
   * change quand une conversation locale vient d'être persistée pour être
   * rattachée. Écrire sur l'ancien laisserait le store croire qu'aucun
   * projet n'est rattaché — un affichage qui ment sur la cloison.
   */
  onProjectChange?: (
    projectId: string | null,
    memoryScope: string,
    conversationId: string
  ) => void;
}

/**
 * Rattache la conversation courante à un projet — et le dit à l'utilisateur.
 *
 * Ce rattachement commande le cloisonnement du contexte documentaire : une
 * conversation rattachée ne consulte plus que les documents de son projet et
 * les documents globaux.
 *
 * Le libellé annonce ce que la conversation CONSULTE, pas un réglage abstrait :
 * une cloison invisible serait pire que pas de cloison du tout, l'utilisateur
 * verrait le contexte changer sans comprendre pourquoi.
 */
export function ConversationProjectPicker({
  conversationId,
  projectId,
  memoryScope = 'global',
  onProjectChange,
}: ConversationProjectPickerProps) {
  const [projets, setProjets] = useState<ProjetAffichable[]>([]);
  const valeurInitiale =
    projectId ?? (memoryScope === 'all' ? TOUS_LES_PROJETS : '');
  const [selection, setSelection] = useState<string>(valeurInitiale);
  const [enCours, setEnCours] = useState(false);
  // B-056 : une liste vide affirmait « aucun dossier où se rattacher ». Une
  // panne de lecture n'est pas une absence de dossiers, et l'utilisateur ne
  // pouvait pas faire la différence.
  const [listeIndisponible, setListeIndisponible] = useState(false);

  useEffect(() => {
    setSelection(projectId ?? (memoryScope === 'all' ? TOUS_LES_PROJETS : ''));
  }, [projectId, memoryScope]);

  useEffect(() => {
    let vivant = true;
    // Le backend peut être injoignable : le sélecteur reste affiché avec ses
    // options fixes plutôt que de faire tomber l'en-tête du chat.
    Promise.resolve(listProjects())
      .then((liste) => {
        if (vivant && Array.isArray(liste)) {
          setProjets(liste.map((p: ProjetAffichable) => ({ id: p.id, name: p.name })));
          setListeIndisponible(false);
        }
      })
      .catch(() => {
        if (vivant) {
          setProjets([]);
          setListeIndisponible(true);
        }
      });
    return () => {
      vivant = false;
    };
  }, []);

  const surChangement = useCallback(
    async (valeur: string) => {
      const transversal = valeur === TOUS_LES_PROJETS;
      const cible = transversal || !valeur ? null : valeur;
      const politique = transversal ? 'all' : cible ? 'project' : 'global';
      const precedent = selection;
      setSelection(valeur);
      setEnCours(true);
      try {
        // D6 : une conversation neuve n'existe qu'en local jusqu'à son premier
        // message. Rattacher un projet la persiste d'abord, au lieu de répondre
        // 404 au moment précis où l'on vient d'indexer un dossier.
        const identifiantServeur = await rattacherAUnProjet(
          conversationId,
          cible,
          politique
        );
        onProjectChange?.(cible, politique, identifiantServeur);
      } catch (erreur) {
        // Rétablir l'affichage : laisser une sélection que le serveur n'a pas
        // enregistrée ferait croire à un cloisonnement inexistant.
        setSelection(precedent);
        if (erreur instanceof ConversationEphemereError) {
          // Une conversation éphémère ne doit pas devenir une conversation
          // ordinaire dans le dos de l'utilisateur : on refuse en le disant.
          useStatusStore.getState().addNotification({
            type: 'warning',
            title: 'Conversation éphémère',
            message:
              'Une conversation éphémère n’est pas enregistrée : elle ne peut pas '
              + 'être rattachée à un projet. Ouvre une conversation ordinaire pour '
              + 'consulter les documents de ce dossier.',
          });
          return;
        }
        // D6 : le rétablissement était MUET. L'utilisateur voyait son choix
        // revenir tout seul à « Documents généraux » et n'apprenait jamais que
        // les documents de son projet restaient hors de portée. Une
        // conversation neuve n'existe en base qu'au premier message : c'est le
        // cas d'échec le plus fréquent, et le plus déroutant.
        useStatusStore.getState().addNotification({
          type: 'warning',
          title: 'Documents du projet non rattachés',
          message:
            'Le rattachement n’a pas été enregistré : cette conversation consulte '
            + 'toujours les documents généraux. Réessaie dans un instant.',
        });
      } finally {
        setEnCours(false);
      }
    },
    [conversationId, onProjectChange, selection]
  );

  return (
    <label className="flex min-w-0 items-center gap-1.5 text-xs text-text-muted">
      <FolderTree className="h-3.5 w-3.5 shrink-0" aria-hidden="true" />
      {/* C1, corrigé après relecture : « Dossier de cette conversation »
          promettait une étanchéité qui dépend d'un réglage éteint par défaut —
          un mensonge plus large que celui qu'il remplaçait. Le libellé dit ce
          qui est vrai dans les deux cas : les fichiers suivent le dossier, le
          carnet reste partagé tant que le mode cabinet n'est pas activé. */}
      <span className="sr-only">Dossier de cette conversation : fichiers rattachés, carnet partagé</span>
      <select
        aria-label="Dossier de cette conversation : fichiers rattachés, carnet partagé"
        value={selection}
        disabled={enCours}
        onChange={(e) => void surChangement(e.target.value)}
        className="min-w-0 max-w-[11rem] truncate rounded-sm border border-border bg-surface-2 px-1.5 py-0.5 text-sm text-text disabled:opacity-60"
      >
        {/* Libellés honnêtes : ils annoncent ce que la conversation CONSULTE.
            « Toute la mémoire » par défaut aurait menti — le défaut est
            désormais le moindre privilège. */}
        <option value="">Documents généraux</option>
        {projets.map((projet) => {
          const homonymes = projets.filter((p) => p.name === projet.name).length > 1;
          return (
            <option key={projet.id} value={projet.id}>
              {homonymes ? `${projet.name} · ${projet.id.slice(0, 8)}` : projet.name}
            </option>
          );
        })}
        <option value={TOUS_LES_PROJETS}>Tous les projets</option>
      </select>
      {listeIndisponible && (
        <span
          role="alert"
          className="shrink-0 text-xs text-warning"
          title="La liste des dossiers n’a pas pu être lue : ce menu est incomplet. Réessaie dans un instant."
        >
          Dossiers non lus
        </span>
      )}
    </label>
  );
}
