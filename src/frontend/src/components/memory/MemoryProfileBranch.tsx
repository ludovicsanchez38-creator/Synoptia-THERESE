import { Button } from '../ui/Button';
import { useState } from 'react';
import { useDemoMask } from '../../hooks/useDemoMask';
import { gesteBloqueEnDemo } from '../../lib/gesteEnDemo';
import { SettingsModal } from '../settings/SettingsModal';

export function MemoryProfileBranch() {
  const [open, setOpen] = useState(false);
  const demo = useDemoMask();
  return <section aria-label="Ton profil et tes consignes" className="space-y-4">
    <p>Ton identité professionnelle et tes consignes THERESE.md se modifient dans le même éditeur que les Paramètres.</p>
    {demo.enabled && <p>Contenu masqué en démonstration</p>}
    <Button type="button" variant="secondary" size="md" disabled={demo.enabled}
      onClick={() => { if (!gesteBloqueEnDemo()) setOpen(true); }}>Modifier mon profil et mes consignes</Button>
    {open && !demo.enabled && <>
      <SettingsModal isOpen requestedTab="profile" profileOnly onClose={() => setOpen(false)} />
    </>}
  </section>;
}
