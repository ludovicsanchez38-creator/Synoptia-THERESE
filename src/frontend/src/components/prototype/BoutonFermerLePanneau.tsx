import { PanelRightClose } from 'lucide-react';

/**
 * La sortie du panneau de travail, nommée à l'écran.
 *
 * Campagne dix personas, persona 08 : « des petits dessins sans nom […] je
 * cherche Annuler : il n'y est pas ». Le contrôle existait en icône seule,
 * avec un `aria-label` — utile au lecteur d'écran, invisible pour qui
 * regarde. Le mot est donc affiché, et l'icône devient l'accompagnement.
 *
 * Extrait en composant pour qu'un test puisse le RENDRE plutôt que relire un
 * attribut dans la coque de 1800 lignes.
 */
export function BoutonFermerLePanneau({ onClose }: { onClose: () => void }) {
  return (
    <button
      type="button"
      onClick={onClose}
      aria-label="Fermer ce panneau"
      title="Fermer ce panneau"
      className="absolute right-4 top-3.5 z-30 inline-flex items-center gap-1.5 rounded-[9px] border border-border bg-surface px-2.5 py-2 text-xs font-semibold text-text-muted shadow-sm hover:text-text focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent"
    >
      <PanelRightClose className="h-4 w-4" />
      <span>Fermer</span>
    </button>
  );
}
