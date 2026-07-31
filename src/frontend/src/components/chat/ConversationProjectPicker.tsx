import { useCallback, useEffect, useState } from 'react';
import { FolderTree } from 'lucide-react';

import { listProjects, setConversationProject } from '../../services/api';

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
  onProjectChange?: (projectId: string | null, memoryScope: string) => void;
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
        }
      })
      .catch(() => {
        if (vivant) setProjets([]);
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
        await setConversationProject(conversationId, cible, politique);
        onProjectChange?.(cible, politique);
      } catch {
        // Rétablir l'affichage : laisser une sélection que le serveur n'a pas
        // enregistrée ferait croire à un cloisonnement inexistant.
        setSelection(precedent);
      } finally {
        setEnCours(false);
      }
    },
    [conversationId, onProjectChange, selection]
  );

  return (
    <label className="flex min-w-0 items-center gap-1.5 text-xs text-text-muted">
      <FolderTree className="h-3.5 w-3.5 shrink-0" aria-hidden="true" />
      <span className="sr-only">Documents consultés par cette conversation</span>
      <select
        aria-label="Documents consultés par cette conversation"
        value={selection}
        disabled={enCours}
        onChange={(e) => void surChangement(e.target.value)}
        className="min-w-0 max-w-[11rem] truncate rounded-[6px] border border-border bg-surface-2 px-1.5 py-0.5 text-xs text-text disabled:opacity-60"
      >
        {/* Libellés honnêtes : ils annoncent ce que la conversation CONSULTE.
            « Toute la mémoire » par défaut aurait menti — le défaut est
            désormais le moindre privilège. */}
        <option value="">Documents généraux</option>
        {projets.map((projet) => (
          <option key={projet.id} value={projet.id}>
            {projet.name}
          </option>
        ))}
        <option value={TOUS_LES_PROJETS}>Tous les projets</option>
      </select>
    </label>
  );
}
