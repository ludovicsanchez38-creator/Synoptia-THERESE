/**
 * « Abandonner les modifications ? » pour une modale de saisie (B-1392).
 *
 * Zoé (cycle 13) : Échap, la croix ou un clic sur le fond jetaient la saisie
 * des formulaires Contact, Projet et Devis, alors que Tâche et Rendez-vous
 * posent déjà la question (B-973, `useAbandonDeSaisie`, pensé pour un
 * formulaire hébergé dans un panneau). Ici la modale est une surface de la
 * coque : Échap passe par la pile d'Échap avant la cascade de la coque, donc
 * la modale y répond la première.
 *
 * La question n'est posée que si la saisie a changé ; un formulaire intact se
 * ferme comme avant : le gestionnaire d'Échap décline et la coque ferme, ou,
 * avec `fermerSiIntact`, il ferme lui-même (modale hors du panelStore, B-228).
 */
import { useCallback, useEffect, useLayoutEffect, useRef, useState } from 'react';
import { pushEscapeHandler } from '../lib/escapeStack';

export function useQuestionDAbandonDeModale({
  actif,
  modifie,
  fermer,
  fermerSiIntact = false,
}: {
  /** La modale est ouverte. */
  actif: boolean;
  /** La saisie diffère de ce qui était chargé. */
  modifie: boolean;
  /** Ferme la modale en jetant la saisie. */
  fermer: () => void;
  /** Échap sur une saisie intacte ferme la modale ici, au lieu de décliner. */
  fermerSiIntact?: boolean;
}) {
  const [abandonDemande, setAbandonDemande] = useState(false);
  const etat = useRef({ modifie, abandonDemande, fermer, fermerSiIntact });
  useLayoutEffect(() => {
    etat.current = { modifie, abandonDemande, fermer, fermerSiIntact };
  });

  useEffect(() => {
    if (!actif) setAbandonDemande(false);
  }, [actif]);

  const demanderFermeture = useCallback(() => {
    if (etat.current.modifie) setAbandonDemande(true);
    else etat.current.fermer();
  }, []);

  const continuerSaisie = useCallback(() => setAbandonDemande(false), []);

  const abandonner = useCallback(() => {
    setAbandonDemande(false);
    etat.current.fermer();
  }, []);

  useEffect(() => {
    if (!actif) return;
    return pushEscapeHandler(() => {
      if (etat.current.abandonDemande) {
        setAbandonDemande(false);
        return true;
      }
      if (etat.current.modifie) {
        setAbandonDemande(true);
        return true;
      }
      if (etat.current.fermerSiIntact) {
        etat.current.fermer();
        return true;
      }
      return false;
    });
  }, [actif]);

  return { abandonDemande, demanderFermeture, continuerSaisie, abandonner };
}
