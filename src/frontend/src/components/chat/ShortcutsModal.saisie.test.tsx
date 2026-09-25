/**
 * B-1376 (persona Hugo, cycle 13) : ⌘B depuis le champ de message ne faisait
 * rien, alors que les deux listes de raccourcis l'annonçaient sans réserve ;
 * et ⌘M s'appelait « Mémoire » dans Paramètres, « Contacts » dans la fenêtre
 * des raccourcis et à l'écran.
 *
 * Le gestionnaire ignore volontairement la plupart des raccourcis dans un
 * champ de saisie (une frappe ne doit pas changer d'écran). Les listes le
 * disent désormais, et ce test le vérifie dans les deux sens, en frappant
 * chaque raccourci annoncé dans un vrai champ.
 */
import { render, renderHook, screen } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';

import { useKeyboardShortcuts } from '../../hooks/useKeyboardShortcuts';
import { AccessibilityTab } from '../settings/AccessibilityTab';
import { SHORTCUT_GROUPS } from '../../lib/raccourcisAnnonces';
import { ShortcutsModal } from './ShortcutsModal';

const CRENEAUX = [
  'onCommandPalette', 'onNewConversation', 'onShowShortcuts', 'onToggleMemoryPanel',
  'onToggleConversationSidebar', 'onToggleBoardPanel', 'onToggleEmailPanel',
  'onToggleCalendarPanel', 'onToggleTasksPanel', 'onToggleInvoicesPanel', 'onToggleCRMPanel',
  'onOpenSettings', 'onSearch', 'onOpenFile', 'onToggleDemoMode', 'onToggleAtelierPanel',
  'onOpenKatiaNewTask',
] as const;

const annonces = SHORTCUT_GROUPS.flatMap((g) => g.shortcuts).filter((s) => s.keys.includes('⌘'));

function frapperDansUnChamp(keys: string) {
  const touche = keys.split(' + ').pop() ?? '';
  const champ = document.createElement('textarea');
  document.body.appendChild(champ);
  champ.focus();
  champ.dispatchEvent(new KeyboardEvent('keydown', {
    key: touche.length === 1 ? touche.toLowerCase() : touche,
    metaKey: true,
    ctrlKey: true,
    shiftKey: keys.includes('⇧'),
    bubbles: true,
    cancelable: true,
  }));
  champ.remove();
}

afterEach(() => {
  document.body.innerHTML = '';
});

describe('B-1376 : les listes disent quels raccourcis marchent en écrivant', () => {
  it.each(annonces)('$keys ($description) : annoncé comme il se comporte dans un champ', ({ keys, pendantLaSaisie }) => {
    const handlers = Object.fromEntries(CRENEAUX.map((n) => [n, vi.fn()]));
    renderHook(() => useKeyboardShortcuts(handlers));

    frapperDansUnChamp(keys);

    const appele = Object.values(handlers).some((f) => f.mock.calls.length > 0);
    expect(appele, `${keys} dans un champ`).toBe(Boolean(pendantLaSaisie));
  });

  it('la fenêtre des raccourcis nomme ceux qui marchent en écrivant', () => {
    render(<ShortcutsModal isOpen onClose={() => {}} />);
    const note = screen.getByText(/En écrivant dans un champ/).textContent ?? '';
    const citees = note.split(' : ')[1].replace(/\.$/, '').split(' · ');
    const attendues = annonces.filter((s) => s.pendantLaSaisie).map((s) => s.keys.replace(/⌘/g, 'Ctrl'));
    expect(citees).toEqual(attendues);
  });

  it('Paramètres nomme ⌘M comme l’écran qu’il ouvre, et garde la réserve', () => {
    render(<AccessibilityTab />);
    expect(screen.queryByText(/\+M : Mémoire/)).not.toBeInTheDocument();
    expect(screen.getByText(/\+M : Contacts/)).toBeInTheDocument();
    expect(screen.getByText(/En écrivant dans un champ/)).toBeInTheDocument();
  });

  it('P-124 : Paramètres liste ⌘N « Nouvelle conversation »', () => {
    render(<AccessibilityTab />);
    expect(screen.getByText(/\+N : Nouvelle conversation/)).toBeInTheDocument();
  });
});
