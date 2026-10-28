import { useState } from 'react';
import { CircleHelp } from 'lucide-react';
import { open } from '@tauri-apps/plugin-shell';
import { ouvrirGuide, GUIDE_VERSION } from '../lib/pdfLocaux';
import { LIEN_SECURITE } from './onboarding/SecurityStep';
import { Button } from './ui/Button';
import { DialogShell } from './ui/DialogShell';

export function Aide({ compact = false }: { compact?: boolean }) {
  const [visible, setVisible] = useState(false);
  const [erreur, setErreur] = useState<string | null>(null);
  async function ouvrir(action: () => Promise<unknown>) {
    setErreur(null);
    try { await action(); }
    catch { setErreur('L’ouverture a échoué. Vérifie qu’un lecteur PDF et un navigateur sont installés, puis réessaie.'); }
  }
  return <>
    <Button variant="ghost" size={compact ? 'icon' : 'sm'} aria-label="Aide" title="Aide" onClick={() => setVisible(true)}>
      <CircleHelp className="h-[18px] w-[18px]" />{!compact && <span>Aide</span>}
    </Button>
    <DialogShell open={visible} onClose={() => setVisible(false)} ariaLabel="Aide" className="w-full max-w-lg rounded-lg border border-border bg-surface p-6 space-y-4">
      <h2 className="text-xl font-semibold text-text">Aide</h2>
      <p className="text-text-muted">Le guide de THÉRÈSE {GUIDE_VERSION} est inclus dans l’application et reste disponible sans connexion.</p>
      <Button onClick={() => void ouvrir(ouvrirGuide)}>Ouvrir le guide (PDF)</Button>
      <p><a href={LIEN_SECURITE} className="text-accent-cyan underline" onClick={(e) => { e.preventDefault(); void ouvrir(() => open(LIEN_SECURITE)); }}>Lire la page sécurité</a></p>
      {erreur && <p role="alert" className="text-error">{erreur}</p>}
      <Button variant="ghost" onClick={() => setVisible(false)}>Fermer l’aide</Button>
    </DialogShell>
  </>;
}
