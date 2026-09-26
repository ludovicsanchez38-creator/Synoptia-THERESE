/**
 * P-148, lot 4 : la confirmation de suppression d'un projet, une seule.
 *
 * Constat 8 de la revue : la fenêtre du projet et la vue Projets (bouton
 * « Supprimer » d'une carte) avaient chacune la leur, avec deux messages
 * différents pour la même suppression. Les deux hôtes gardent leur conteneur
 * (bandeau en ligne dans la fenêtre, dialogue dans la vue) ; le texte, la
 * lecture des totaux et les boutons vivent ici.
 *
 * La phrase des conséquences vient de la route d'ensemble, lue à la demande
 * de suppression (le compte du moment : un livrable a pu être ajouté depuis
 * l'ouverture). Elle arrive après la question et le focus : elle s'annonce
 * dans une région `role="status"` (constat 17). Illisible, elle se tait et
 * la mise en garde générale reste, jamais un « 0 tâche » inventé.
 */
import { useEffect, useState } from 'react';
import { AlertCircle } from 'lucide-react';

import { lireLEnsembleDuProjet } from '../../services/api';
import { consequencesDeLaSuppression } from '../../lib/consequencesDeLaSuppression';
import { Button } from '../ui/Button';
import { Spinner } from '../ui/Spinner';

type Lecture = { etat: 'lecture' } | { etat: 'lue'; phrases: string[] } | { etat: 'illisible' };

export function ConfirmationSuppressionProjet({
  projetId,
  nom,
  variante,
  titreId,
  onAnnuler,
  onConfirmer,
  enCours = false,
  desactive = false,
}: {
  projetId: string;
  /** Le nom tel que l'écran le montre (masqué en démonstration). */
  nom: string;
  /** « en-ligne » : bandeau dans la fenêtre du projet ; « dialogue » : dialogue de la vue Projets. */
  variante: 'en-ligne' | 'dialogue';
  /** L'identifiant du titre, qui nomme le dialogue de l'hôte. */
  titreId?: string;
  onAnnuler: () => void;
  onConfirmer: () => void;
  enCours?: boolean;
  desactive?: boolean;
}) {
  const [lecture, setLecture] = useState<Lecture>({ etat: 'lecture' });

  useEffect(() => {
    let vivante = true;
    setLecture({ etat: 'lecture' });
    const lire = async () => {
      try {
        const ensemble = await lireLEnsembleDuProjet(projetId, 1);
        if (!vivante) return;
        const phrases = consequencesDeLaSuppression(ensemble);
        setLecture(phrases ? { etat: 'lue', phrases } : { etat: 'illisible' });
      } catch {
        if (vivante) setLecture({ etat: 'illisible' });
      }
    };
    void lire();
    return () => { vivante = false; };
  }, [projetId]);

  const annonce = lecture.etat === 'lecture'
    ? 'Lecture de ce que la suppression emporte…'
    : lecture.etat === 'lue' ? lecture.phrases.join(' ') : '';
  const phraseDuNom = `« ${nom} » sera supprimé. Cette action est irréversible.`;

  if (variante === 'dialogue') {
    return (
      <>
        <h2 id={titreId} className="text-base font-semibold text-text">Supprimer ce projet ?</h2>
        <p className="text-sm text-text-muted mt-2">{phraseDuNom}</p>
        <p role="status" className="text-sm text-text-muted mt-2">{annonce}</p>
        <div className="flex flex-wrap justify-end gap-2 mt-5">
          {/* B-975 : `data-dialog-autofocus` et non `autoFocus` (piège B-278 :
              posé avant la capture du déclencheur, Échap rendait le focus à BODY). */}
          <Button variant="ghost" size="md" data-dialog-autofocus onClick={onAnnuler}>
            Annuler
          </Button>
          <Button variant="danger" size="md" onClick={onConfirmer} disabled={enCours || desactive}>
            Supprimer
          </Button>
        </div>
      </>
    );
  }

  return (
    <>
      <AlertCircle className="w-4 h-4 text-error shrink-0" />
      <div className="flex-1">
        <p className="text-sm text-error font-medium">Supprimer ce projet ?</p>
        <p className="text-sm text-error">{phraseDuNom}</p>
        <p role="status" className="text-sm text-error">{annonce}</p>
      </div>
      <div className="flex flex-wrap gap-2">
        <Button variant="ghost" size="sm" onClick={onAnnuler}>
          Annuler
        </Button>
        <Button variant="danger" size="sm" onClick={onConfirmer} disabled={enCours || desactive}>
          {enCours ? <Spinner taille="bouton" /> : 'Supprimer'}
        </Button>
      </div>
    </>
  );
}
