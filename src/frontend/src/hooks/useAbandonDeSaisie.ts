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
 *
 * B-978 : le formulaire s'inscrit aussi dans le registre des saisies en
 * cours, que la coque consulte avant toute autre sortie de la vue.
 *
 * B-980 : tant qu'une surface de la coque (Réglages, fiche, palette, centre…)
 * recouvre le formulaire, son Échap décline pour que la coque ferme cette
 * surface. Le formulaire expose `racineSaisie` pour reconnaître la modale qui
 * l'héberge (panneau Tâches ou Agenda) d'une modale posée par-dessus.
 *
 * B-995 : la question s'annonce (`role="alert"` porté par le formulaire) et
 * prend le focus sur « Continuer la saisie » ; répondre « continuer » rend le
 * focus là où il était.
 *
 * B-996 : à la fermeture du formulaire (abandon, retour, enregistrement), le
 * focus qui tombait sur la page revient au déclencheur (« Nouvelle tâche »,
 * « Nouveau rendez-vous ») ou, s'il a disparu, au premier contrôle du
 * panneau qui hébergeait le formulaire.
 */
import { useCallback, useEffect, useLayoutEffect, useRef, useState } from 'react';
import { pushEscapeHandler } from '../lib/escapeStack';
import { uneModaleDistincteEstOuverte, uneSurfaceDeLaCoqueEstOuverte } from '../lib/surfacesDeLaCoque';
import { inscrireSaisieEnCours } from '../lib/saisieEnCours';

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
  const racineSaisie = useRef<HTMLDivElement | null>(null);
  const questionRef = useRef<HTMLDivElement | null>(null);
  const retourFocusRef = useRef<HTMLElement | null>(null);
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
        if (uneSurfaceDeLaCoqueEstOuverte() || uneModaleDistincteEstOuverte(racineSaisie.current)) return false;
        if (etat.current.abandonDemande) setAbandonDemande(false);
        else demanderAbandon();
      }),
    [demanderAbandon],
  );

  // B-978 : les autres sorties de la vue (Retour d'en-tête, rail, palette)
  // consultent ce registre avant de démonter le formulaire.
  useEffect(
    () =>
      inscrireSaisieEnCours(() => {
        if (!etat.current.modifie) return false;
        setAbandonDemande(true);
        return true;
      }),
    [],
  );

  // B-995 : focus sur la question à son apparition, retour à sa disparition.
  useEffect(() => {
    if (abandonDemande) {
      const actif = document.activeElement;
      retourFocusRef.current = actif instanceof HTMLElement && actif !== document.body ? actif : null;
      questionRef.current?.querySelector<HTMLElement>('button')?.focus();
      return;
    }
    const retour = retourFocusRef.current;
    retourFocusRef.current = null;
    if (retour?.isConnected) retour.focus();
  }, [abandonDemande]);

  // B-996 : le déclencheur est l'élément focalisé à l'ouverture du formulaire.
  // B-1009 : `monte` écarte le faux démontage du double montage de StrictMode,
  // qui déplaçait le focus sur le premier contrôle du panneau.
  const monte = useRef(false);
  useEffect(() => {
    monte.current = true;
    const actif = document.activeElement;
    const declencheur = actif instanceof HTMLElement && actif !== document.body ? actif : null;
    const panneau = racineSaisie.current?.parentElement?.closest<HTMLElement>(
      '[role="dialog"], [data-testid="tasks-panel"], [data-testid="calendar-panel"], [data-embedded-view]',
    ) ?? null;
    return () => {
      monte.current = false;
      setTimeout(() => {
        if (monte.current) return;
        const perdu = !document.activeElement || document.activeElement === document.body;
        if (!perdu) return;
        if (declencheur?.isConnected) { declencheur.focus(); return; }
        if (panneau?.isConnected) {
          panneau.querySelector<HTMLElement>('button:not([disabled]), [href], input:not([disabled]), [tabindex]:not([tabindex="-1"])')?.focus();
        }
      }, 0);
    };
  }, []);

  return { abandonDemande, demanderAbandon, continuerSaisie, racineSaisie, questionRef };
}
