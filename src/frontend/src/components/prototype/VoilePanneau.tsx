/**
 * Le voile grisé d'un panneau devenu modal (petit écran, hotfix 0.48.1).
 *
 * Exigence de Ludo : si le fond est isolé, il doit se VOIR - un fond
 * simplement mort, sans signe, se lit comme une application figée. Le voile
 * n'est pas un bouton de fermeture (BUG-156 : la fermeture au clic sur le
 * fond avait été refusée par les testeurs) ; il porte `data-dialog-backdrop`
 * pour que le focus trap ne l'isole pas avec le reste.
 */
export function VoilePanneau() {
  return (
    <div
      data-testid="panneau-voile"
      data-dialog-backdrop
      aria-hidden="true"
      className="absolute inset-0 z-[15] bg-text/35 backdrop-blur-[2px]"
    />
  );
}
