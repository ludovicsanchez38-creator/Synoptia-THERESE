import { useEffect, useRef, useState } from 'react';
import { ToolConfirmationCard } from '../chat/ToolConfirmationCard';
import { useToolConfirmationStore } from '../../stores/toolConfirmationStore';
import { Z_LAYER } from '../../styles/z-layers';

/**
 * Couche commune aux interfaces classique et 0.40.
 *
 * Une confirmation sensible ne doit jamais disparaître parce qu'un canevas,
 * un panneau guidé ou une autre interface remplace le contenu principal.
 *
 * B-248 : ce calque est en position fixe et au-dessus du contenu, ce qui
 * recouvrait la fin du message qu'il demande de valider. Le déplacer dans le
 * fil casserait l'exigence ci-dessus ; il publie donc sa hauteur réelle, et
 * c'est le fil qui réserve la bande correspondante.
 */
export function CommonToolConfirmationLayer() {
  const pending = useToolConfirmationStore((state) => state.pending);
  const setHauteurCalque = useToolConfirmationStore((state) => state.setHauteurCalque);
  const carteRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const carte = carteRef.current;
    if (!carte || pending.length === 0) {
      setHauteurCalque(0);
      return;
    }
    const mesurer = () => setHauteurCalque(carte.getBoundingClientRect().height);
    mesurer();
    // Le corps d'un e-mail long fait grandir la carte après coup. jsdom
    // n'implémente pas ResizeObserver : la mesure au changement d'attente y
    // suffit, faute de mise en page à observer.
    if (typeof ResizeObserver === 'undefined') return;
    const observateur = new ResizeObserver(mesurer);
    observateur.observe(carte);
    return () => observateur.disconnect();
  }, [pending, setHauteurCalque]);

  // B-1437 : fixée à 96 px du bas, la carte recouvrait de 14 à 27 px le
  // composeur, plus haut. Elle se pose 8 px au-dessus de son bord haut réel,
  // suivi au redimensionnement ; sans composeur, le repli reste 96 px.
  const [basDuCalque, setBasDuCalque] = useState<number | null>(null);
  useEffect(() => {
    if (pending.length === 0) return;
    const composeur = document.querySelector<HTMLElement>('[data-zone-composeur]');
    if (!composeur) {
      setBasDuCalque(null);
      return;
    }
    const placer = () =>
      setBasDuCalque(Math.max(0, window.innerHeight - composeur.getBoundingClientRect().top + 8));
    placer();
    window.addEventListener('resize', placer);
    const observateur = typeof ResizeObserver === 'undefined' ? null : new ResizeObserver(placer);
    observateur?.observe(composeur);
    return () => {
      window.removeEventListener('resize', placer);
      observateur?.disconnect();
    };
  }, [pending]);

  return (
    <div
      className={`pointer-events-none fixed inset-x-0 bottom-24 ${Z_LAYER.WIZARD} flex justify-center px-4`}
      style={basDuCalque === null ? undefined : { bottom: `${basDuCalque}px` }}
      data-testid="common-tool-confirmation-layer"
    >
      <div ref={carteRef} className="pointer-events-auto w-full max-w-2xl">
        <ToolConfirmationCard />
      </div>
    </div>
  );
}
