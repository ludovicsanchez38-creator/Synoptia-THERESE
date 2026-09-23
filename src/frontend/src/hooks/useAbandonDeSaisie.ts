/**
 * Question « Abandonner les modifications ? » des formulaires Tâche et
 * Rendez-vous (B-973, B-974, cycle 11, 23/09/2026).
 *
 * B-973 : Échap, le geste le plus naturel pour répondre à la question,
 * fermait toute la vue et jetait la saisie : le formulaire n'inscrivait rien
 * dans la pile d'Échap, et la cascade de la coque refermait la vue. Tant que
 * le formulaire est monté, Échap passe désormais par ici : question affichée,
 * il y répond « continuer la saisie » ; sinon il se comporte comme « Retour ».
 *
 * B-974 : la question était posée sur un formulaire vierge, où elle est
 * fausse. Elle ne l'est plus que si la saisie a changé ; tant que l'état de
 * référence est inconnu (fiche pas encore chargée), elle l'est toujours,
 * comme le voulait le choix fail-closed de B-872.
 */
import { useCallback, useEffect, useLayoutEffect, useRef, useState } from 'react';
import { pushEscapeHandler } from '../lib/escapeStack';

export function useAbandonDeSaisie({
  modifie,
  abandonner,
}: {
  /** La saisie diffère de son état de référence (ou celui-ci est inconnu). */
  modifie: boolean;
  /** Ferme le formulaire en jetant la saisie. */
  abandonner: () => void;
}) {
  const [abandonDemande, setAbandonDemande] = useState(false);
  const etat = useRef({ modifie, abandonDemande, abandonner });
  useLayoutEffect(() => {
    etat.current = { modifie, abandonDemande, abandonner };
  });

  const demanderAbandon = useCallback(() => {
    if (etat.current.modifie) setAbandonDemande(true);
    else etat.current.abandonner();
  }, []);

  const continuerSaisie = useCallback(() => setAbandonDemande(false), []);

  useEffect(
    () =>
      pushEscapeHandler(() => {
        if (etat.current.abandonDemande) setAbandonDemande(false);
        else demanderAbandon();
      }),
    [demanderAbandon],
  );

  return { abandonDemande, demanderAbandon, continuerSaisie };
}
