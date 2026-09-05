import { useEffect, useState, type RefObject } from 'react';
import { ChevronDown } from 'lucide-react';

const MARGE = 24;

/**
 * B-562 (05/09/2026) : le composeur flotte au-dessus du fil et couvre le bas
 * de la fenêtre. À l'arrivée, la rangée des sources et des parcours tombait
 * dessous sans qu'aucun signe ne dise qu'il reste du contenu : cet indice
 * s'affiche tant que le fil n'est pas au bout, et y mène d'un clic.
 */
export function IndiceDeDefilement({ cible }: { cible: RefObject<HTMLDivElement | null> }) {
  const [resteDuContenu, setResteDuContenu] = useState(false);

  useEffect(() => {
    const zone = cible.current;
    if (!zone) return;
    const mesurer = () => {
      setResteDuContenu(zone.scrollHeight - zone.scrollTop - zone.clientHeight > MARGE);
    };
    mesurer();
    zone.addEventListener('scroll', mesurer, { passive: true });
    const observateur = typeof ResizeObserver === 'undefined' ? null : new ResizeObserver(mesurer);
    observateur?.observe(zone);
    if (zone.firstElementChild) observateur?.observe(zone.firstElementChild);
    return () => {
      zone.removeEventListener('scroll', mesurer);
      observateur?.disconnect();
    };
  }, [cible]);

  if (!resteDuContenu) return null;
  return (
    <div className="pointer-events-none flex justify-center pb-2">
      <button
        type="button"
        onClick={() => cible.current?.scrollTo({ top: cible.current.scrollHeight, behavior: 'smooth' })}
        className="pointer-events-auto inline-flex items-center gap-1 rounded-full border border-border bg-surface px-3 py-1 text-sm font-medium text-text-muted shadow-sm hover:text-text"
      >
        <ChevronDown className="h-3.5 w-3.5" aria-hidden="true" />
        Voir la suite
      </button>
    </div>
  );
}
