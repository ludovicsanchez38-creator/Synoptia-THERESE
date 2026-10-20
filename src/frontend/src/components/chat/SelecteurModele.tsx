import { useEffect, useRef, useState } from 'react';
import { createPortal } from 'react-dom';
import { pushEscapeHandler } from '../../lib/escapeStack';
import { decorer, DECORATIONS } from '../../lib/catalogueModeles';

/** Liste native défilante dans la fenêtre, sans popup natif hors écran. */
export function SelecteurModele({ modeles, modele, onChange, description }: {
  modeles: string[]; modele: string; onChange: (modele: string) => void; description?: string;
}) {
  const bouton = useRef<HTMLButtonElement>(null);
  const liste = useRef<HTMLSelectElement>(null);
  const clavier = useRef(false);
  const [choix, setChoix] = useState(modele);
  const [position, setPosition] = useState<{ left: number; bottom: number; maxHeight: number } | null>(null);
  const fermer = () => { setPosition(null); bouton.current?.focus(); };
  useEffect(() => {
    if (!position) return;
    liste.current?.focus();
    const depiler = pushEscapeHandler(() => { setPosition(null); bouton.current?.focus(); });
    const horsListe = (e: MouseEvent) => {
      if (!liste.current?.contains(e.target as Node) && !bouton.current?.contains(e.target as Node)) setPosition(null);
    };
    const redimensionner = () => { setPosition(null); bouton.current?.focus(); };
    document.addEventListener('mousedown', horsListe);
    window.addEventListener('resize', redimensionner);
    return () => {
      depiler(); document.removeEventListener('mousedown', horsListe);
      window.removeEventListener('resize', redimensionner);
    };
  }, [position]);
  return <>
    <button ref={bouton} type="button" aria-label="Modèle de conversation" aria-describedby={description}
      aria-expanded={position !== null} aria-haspopup="listbox" className="min-h-9 max-w-[60vw] truncate text-sm font-medium text-text"
      onClick={() => {
        if (position) { fermer(); return; }
        setChoix(modele); clavier.current = false;
        const rect = bouton.current!.getBoundingClientRect();
        setPosition({ left: Math.max(8, Math.min(rect.left, window.innerWidth - 328)), bottom: window.innerHeight - rect.top + 4, maxHeight: Math.max(60, rect.top - 16) });
      }}>{decorer([modele])[0].name} ▾</button>
    {position && createPortal(<select ref={liste} aria-label="Choisir le modèle" value={choix}
      size={Math.min(8, modeles.length)}
      className="fixed z-50 w-80 max-w-[calc(100vw-16px)] overflow-y-auto rounded-md border border-border bg-surface p-2 text-sm text-text shadow-lg"
      style={{ left: position.left, bottom: position.bottom, maxHeight: Math.min(288, position.maxHeight) }}
      onMouseDown={() => { clavier.current = false; }}
      onBlur={(e) => {
        if (e.relatedTarget !== bouton.current) setPosition(null);
      }}
      onChange={(e) => {
        setChoix(e.target.value);
        if (!clavier.current) { onChange(e.target.value); fermer(); }
      }}
      onKeyDown={(e) => {
        if (['ArrowDown', 'ArrowUp', 'Home', 'End', 'PageDown', 'PageUp'].includes(e.key) || e.key.length === 1) clavier.current = true;
        if (e.key === 'Enter') { e.preventDefault(); onChange(e.currentTarget.value); fermer(); }
        if (e.key === 'Escape') { e.preventDefault(); e.stopPropagation(); fermer(); }
        if (e.key === 'Tab') fermer();
      }}>
      {modeles.map((m) => <option key={m} value={m} className="px-2 py-2">{decorer([m])[0].name}{DECORATIONS[m]?.badge === 'Préversion' ? ' (préversion)' : ''}</option>)}
    </select>, document.body)}
  </>;
}
