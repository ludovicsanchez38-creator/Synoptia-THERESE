import { useId, useState, type MouseEvent } from 'react';
import { CircleHelp } from 'lucide-react';
import { open } from '@tauri-apps/plugin-shell';
import ReactMarkdown, { type Components } from 'react-markdown';
import remarkGfm from 'remark-gfm';
import guide from '../../../../docs/USER_GUIDE_ALPHA.md?raw';
import aPropos from '../../../../docs/guide-0.85/a-propos.png';
import demarrage from '../../../../docs/guide-0.85/demarrage.png';
import reglagesSynthetic from '../../../../docs/guide-0.85/reglages-synthetic.png';
import selecteurModeles from '../../../../docs/guide-0.85/selecteur-modeles.png';
import { LIEN_SECURITE } from './onboarding/SecurityStep';
import { Button } from './ui/Button';
import { DialogShell } from './ui/DialogShell';

const captures: Record<string, string> = {
  'guide-0.85/a-propos.png': aPropos,
  'guide-0.85/demarrage.png': demarrage,
  'guide-0.85/reglages-synthetic.png': reglagesSynthetic,
  'guide-0.85/selecteur-modeles.png': selecteurModeles,
};

const composantsGuide: Components = {
  img: ({ src, alt }) => typeof src === 'string' && captures[src] ? (
    <img src={captures[src]} alt={alt ?? ''} className="my-3 max-w-full rounded-sm" />
  ) : null,
};

export function Aide({ compact = false }: { compact?: boolean }) {
  const [visible, setVisible] = useState(false);
  const [guideVisible, setGuideVisible] = useState(false);
  const [erreur, setErreur] = useState<string | null>(null);
  const guideId = useId();

  function fermer() {
    setVisible(false);
    setGuideVisible(false);
    setErreur(null);
  }

  async function ouvrirLien(e: MouseEvent<HTMLElement>) {
    const lien = e.target instanceof Element ? e.target.closest('a[href]') : null;
    if (!(lien instanceof HTMLAnchorElement)) return;
    e.preventDefault();
    setErreur(null);
    try {
      await open(lien.href);
    } catch {
      setErreur('L’ouverture de la page a échoué. Vérifie qu’un navigateur est installé, puis réessaie.');
    }
  }

  return <>
    <Button variant="ghost" size={compact ? 'icon' : 'sm'} aria-label="Aide" title="Aide" onClick={() => setVisible(true)}>
      <CircleHelp className="h-[18px] w-[18px]" />{!compact && <span>Aide</span>}
    </Button>
    <DialogShell open={visible} onClose={fermer} ariaLabel="Aide" className={`w-full ${guideVisible ? 'max-w-3xl' : 'max-w-lg'} rounded-md border border-border bg-surface p-6 space-y-4`}>
      <h2 className="text-xl font-semibold text-text">Aide</h2>
      {!guideVisible && <p className="text-text-muted">Le guide des testeurs est disponible hors connexion.</p>}
      <Button aria-expanded={guideVisible} aria-controls={guideId} onClick={() => setGuideVisible(!guideVisible)}>
        {guideVisible ? 'Masquer le guide' : 'Ouvrir le guide'}
      </Button>
      <article
        id={guideId}
        hidden={!guideVisible}
        tabIndex={0}
        aria-label="Guide des testeurs"
        onClick={e => void ouvrirLien(e)}
        className="max-h-[50vh] overflow-auto overscroll-contain break-words px-3 text-sm leading-relaxed
          [&_a]:text-accent-cyan-ink [&_a]:underline [&_blockquote]:text-text-muted
          [&_h1]:mb-3 [&_h1]:text-xl [&_h1]:font-semibold
          [&_h2]:my-3 [&_h2]:text-lg [&_h2]:font-semibold
          [&_h3]:my-2 [&_h3]:text-base [&_h3]:font-semibold [&_h4]:my-2 [&_h4]:font-semibold
          [&_p]:mb-2 [&_pre]:overflow-x-auto [&_pre]:rounded-sm [&_pre]:bg-surface-2 [&_pre]:p-3
          [&_ol]:mb-2 [&_ol]:list-decimal [&_ol]:pl-5 [&_ul]:mb-2 [&_ul]:list-disc [&_ul]:pl-5
          [&_td]:border [&_td]:border-border [&_td]:p-2
          [&_th]:border [&_th]:border-border [&_th]:p-2 [&_th]:text-left"
      >
        {guideVisible && (
          <ReactMarkdown
            remarkPlugins={[remarkGfm]}
            components={composantsGuide}
          >
            {guide}
          </ReactMarkdown>
        )}
      </article>
      <p><a href={LIEN_SECURITE} className="text-accent-cyan-ink underline" onClick={e => void ouvrirLien(e)}>Lire la page sécurité</a></p>
      {erreur && <p role="alert" className="text-error">{erreur}</p>}
      <Button variant="ghost" onClick={fermer}>Fermer l’aide</Button>
    </DialogShell>
  </>;
}
