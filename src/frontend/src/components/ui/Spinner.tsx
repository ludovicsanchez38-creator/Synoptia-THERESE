/**
 * L'indicateur d'attente, en un seul exemplaire.
 *
 * Avant lui : 133 occurrences dans 67 fichiers, écrites de 38 façons
 * différentes, et 7 seulement annonçaient quelque chose à un lecteur
 * d'écran — l'attente était invisible pour qui n'a pas l'image.
 *
 * Les tailles portent le nom de leur USAGE et non leur mesure : on choisit
 * en pensant à l'endroit où l'on est, pas en comparant des pixels. C'est ce
 * qui empêche la prolifération de recommencer.
 */
import { Loader2 } from 'lucide-react';
import { cn } from '../../lib/utils';

export type TailleSpinner = 'ligne' | 'bouton' | 'zone';

const TAILLES: Record<TailleSpinner, string> = {
  /** Dans un texte ou une puce : discret, il ne doit pas pousser la ligne. */
  ligne: 'h-3.5 w-3.5',
  /** Dans un bouton ou un champ : la taille d'une icône d'action. */
  bouton: 'h-4 w-4',
  /** Seul au milieu d'une zone vide : il est le seul contenu, il se voit. */
  zone: 'h-6 w-6',
};

interface SpinnerProps {
  taille?: TailleSpinner;
  /**
   * Ce qu'on attend, dit à voix haute. À ne fournir QUE si rien d'autre ne
   * l'annonce déjà.
   *
   * Le premier jet annonçait « Chargement » par défaut, ce qui paraissait
   * généreux. La migration a montré le contraire : beaucoup de ces
   * indicateurs vivent DANS une zone déjà annoncée (un bouton dont le texte
   * dit « Envoi… », une région `aria-live`). Le défaut produisait alors deux
   * annonces pour un seul événement — le bruit qu'on voulait éviter. Annoncer
   * est donc un choix, pas un réflexe.
   */
  annonce?: string;
  className?: string;
  /** Pour les rares indicateurs qu'un test doit pouvoir désigner. */
  'data-testid'?: string;
}

export function Spinner({
  taille = 'bouton',
  annonce,
  className,
  'data-testid': testId,
}: SpinnerProps) {
  /* La couleur vient du texte alentour : un spinner n'a pas de couleur propre,
     il a celle de ce qu'il fait attendre. `className` reste là pour les rares
     cas qui doivent en imposer une. */
  const roue = (
    <Loader2
      aria-hidden="true"
      data-testid={testId}
      className={cn(TAILLES[taille], 'animate-spin', className)}
    />
  );
  if (!annonce) return roue;
  return (
    <span role="status" aria-label={annonce} className="inline-flex">
      {roue}
    </span>
  );
}
