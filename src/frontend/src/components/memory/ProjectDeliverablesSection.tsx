/**
 * P-153 : les livrables d'un projet, visibles et ajoutables depuis la
 * fenêtre du projet (il fallait passer par la capacité « Livrables et suivi
 * client »). Même création que la vue des livrables (P-048), statut « À
 * faire » ; en lecture seule (démo), la liste seule.
 */
import { useEffect, useState, type FormEvent } from 'react';
import { Package } from 'lucide-react';

import { createDeliverable, listDeliverables, type DeliverableResponse } from '../../services/api/crm-extended';
import { Button } from '../ui/Button';
import { Input } from '../ui/Input';

const LIBELLES_STATUT: Record<string, string> = {
  a_faire: 'À faire',
  en_cours: 'En cours',
  en_revision: 'En révision',
  valide: 'Validé',
};

export function ProjectDeliverablesSection({
  projectId,
  lectureSeule = false,
  masquer = (texte: string) => texte,
}: {
  projectId: string;
  lectureSeule?: boolean;
  masquer?: (texte: string) => string;
}) {
  const [livrables, setLivrables] = useState<DeliverableResponse[] | null>(null);
  const [erreur, setErreur] = useState<string | null>(null);
  const [titre, setTitre] = useState('');
  const [enCours, setEnCours] = useState(false);

  useEffect(() => {
    let vivant = true;
    listDeliverables({ project_id: projectId })
      .then((liste) => { if (vivant) setLivrables(liste); })
      .catch(() => { if (vivant) { setLivrables([]); setErreur('Les livrables n’ont pas pu être lus.'); } });
    return () => { vivant = false; };
  }, [projectId]);

  async function ajouter(e: FormEvent) {
    e.preventDefault();
    if (!titre.trim() || enCours) return;
    setEnCours(true);
    setErreur(null);
    try {
      const cree = await createDeliverable({ project_id: projectId, title: titre.trim(), status: 'a_faire' });
      setLivrables((courants) => [...(courants ?? []), cree]);
      setTitre('');
    } catch (reason) {
      setErreur(reason instanceof Error ? reason.message : 'Le livrable n’a pas pu être ajouté.');
    } finally {
      setEnCours(false);
    }
  }

  return (
    <div className="space-y-2">
      <p className="flex items-center gap-2 text-sm text-text-muted">
        <Package className="h-4 w-4" aria-hidden />
        Livrables
      </p>
      {livrables && livrables.length > 0 ? (
        <ul className="space-y-1">
          {livrables.map((livrable) => (
            <li key={livrable.id} className="flex items-center justify-between gap-2 rounded-md bg-surface px-3 py-2 text-sm">
              <span className="min-w-0 truncate text-text">{masquer(livrable.title)}</span>
              <span className="shrink-0 text-xs text-text-muted">{LIBELLES_STATUT[livrable.status] ?? livrable.status}</span>
            </li>
          ))}
        </ul>
      ) : livrables ? (
        <p className="text-sm text-text-muted">Aucun livrable pour ce projet.</p>
      ) : null}
      {erreur && <p role="alert" className="text-sm text-error">{erreur}</p>}
      {!lectureSeule && (
        <form onSubmit={ajouter} className="flex items-end gap-2">
          <div className="min-w-0 flex-1">
            <label htmlFor={`livrable-${projectId}`} className="sr-only">Nouveau livrable</label>
            <Input
              id={`livrable-${projectId}`}
              value={titre}
              onChange={(e) => setTitre(e.target.value)}
              placeholder="Nouveau livrable"
              maxLength={200}
            />
          </div>
          <Button type="submit" variant="secondary" size="md" disabled={!titre.trim() || enCours}>
            Ajouter le livrable
          </Button>
        </form>
      )}
    </div>
  );
}
