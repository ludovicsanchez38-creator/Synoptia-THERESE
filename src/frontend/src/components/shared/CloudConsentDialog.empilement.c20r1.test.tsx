import { useState } from 'react';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, expect, it, vi } from 'vitest';
import { compile } from 'tailwindcss';
import { CloudConsentDialog } from './CloudConsentDialog';
import { ConversationCanvasPrototype } from '../prototype/ConversationCanvasPrototype';
import { ProjectModal } from '../memory/ProjectModal';
import * as api from '../../services/api';
import { Z_LAYER } from '../../styles/z-layers';
import { _clearEscapeHandlers } from '../../lib/escapeStack';
import { useChatStore } from '../../stores/chatStore';
import { useNavigationStore } from '../../stores/navigationStore';
import { usePanelStore } from '../../stores/panelStore';
import { usePersonalisationStore } from '../../stores/personalisationStore';

let styles: HTMLStyleElement;
beforeEach(async () => {
  vi.clearAllMocks();
  _clearEscapeHandlers();
  useChatStore.setState({ conversations: [], currentConversationId: null, isStreaming: false });
  usePanelStore.setState(usePanelStore.getInitialState());
  useNavigationStore.setState(useNavigationStore.getInitialState());
  usePersonalisationStore.setState({ skipDashboard: false });
  // Les vraies classes Tailwind déterminent l'empilement, sans reproduire
  // leurs valeurs dans le test ni lancer un serveur ou un build de l'app.
  const css = await compile('@tailwind utilities;');
  styles = document.createElement('style');
  styles.textContent = css.build(['fixed', ...Object.values(Z_LAYER)]);
  document.head.append(styles);
});
afterEach(() => { styles.remove(); });

function Scenario({ accordRecu, busy, onConfirm }: { accordRecu: boolean; busy: boolean; onConfirm: () => void }) {
  const [annule, setAnnule] = useState(false);
  return <>
    <ConversationCanvasPrototype />
    {accordRecu && !annule && <CloudConsentDialog title="Autoriser les fiches mémoire ?"
      dataCategories={['tes fiches mémoire']} testId="accord-tardif" busy={busy}
      onCancel={() => setAnnule(true)} onConfirm={onConfirm} />}
  </>;
}

it.each([false, true])('R1.2 : l’accord tardif prend le premier plan devant la palette (occupé : %s)', (busy) => {
  const onConfirm = vi.fn();
  const vue = render(<Scenario accordRecu={false} busy={busy} onConfirm={onConfirm} />);
  const declencheur = screen.getByRole('button', { name: 'Projets' });
  declencheur.focus();
  fireEvent.keyDown(declencheur, { key: 'k', ctrlKey: true, metaKey: true });
  const palette = screen.getByRole('dialog', { name: 'Rechercher une commande, une capacité ou une donnée' });
  const recherche = screen.getByRole('combobox');
  expect(recherche).toHaveFocus();

  vue.rerender(<Scenario accordRecu busy={busy} onConfirm={onConfirm} />);
  const accord = screen.getByRole('alertdialog', { name: 'Autoriser les fiches mémoire ?' });
  const coucheAccord = Number(getComputedStyle(accord.parentElement!).zIndex);
  const couchePalette = Number(getComputedStyle(palette.parentElement!).zIndex);
  expect(coucheAccord).toBeGreaterThan(couchePalette);
  expect(palette.closest('[inert]')).not.toBeNull();
  expect(accord.closest('[inert]')).toBeNull();
  const annuler = screen.getByRole('button', { name: 'Annuler' });
  expect(annuler).toHaveFocus();
  fireEvent.keyDown(annuler, { key: 'Tab', shiftKey: true });
  expect(document.activeElement).toBe(busy ? annuler : screen.getByRole('button', { name: 'Autoriser et envoyer' }));
  fireEvent.keyDown(document.activeElement!, { key: 'Tab' });
  expect(annuler).toHaveFocus();
  fireEvent.keyDown(annuler, { key: 'Escape' });
  expect(screen.queryByRole('alertdialog')).not.toBeInTheDocument();
  expect(recherche).toHaveFocus();
  expect(palette.closest('[inert]')).toBeNull();
  expect(declencheur.closest('[inert]')).not.toBeNull();
  expect(onConfirm).not.toHaveBeenCalled();

  fireEvent.keyDown(recherche, { key: 'Escape' });
  expect(declencheur).toHaveFocus();
  expect(declencheur.closest('[inert]')).toBeNull();
});

it.each([false, true])('R3.4 : un projet ouvert après l’accord lui laisse le clavier (occupé : %s)', async busy => {
  vi.spyOn(api, 'listContacts').mockResolvedValue([]);
  const fermerProjet = vi.fn();
  const annulerAccord = vi.fn();
  const confirmer = vi.fn();
  function ProjetTardif({ ouvert }: { ouvert: boolean }) {
    return <>
      <CloudConsentDialog title="Autoriser les fiches mémoire ?" dataCategories={['tes fiches mémoire']}
        testId="accord-tardif" busy={busy} onCancel={annulerAccord} onConfirm={confirmer} />
      {ouvert && <ProjectModal isOpen onClose={fermerProjet} fermerSiIntact />}
    </>;
  }
  const vue = render(<ProjetTardif ouvert={false} />);
  const annuler = screen.getByRole('button', { name: 'Annuler' });
  expect(annuler).toHaveFocus();
  // Une lecture de projet déclenchée avant l'accord vient de terminer.
  vue.rerender(<ProjetTardif ouvert />);
  await waitFor(() => expect(api.listContacts).toHaveBeenCalled());
  const projet = screen.getByRole('dialog', { hidden: true });
  expect(projet.closest('[inert]')).not.toBeNull();
  expect(screen.getByRole('alertdialog').closest('[inert]')).toBeNull();
  expect(annuler).toHaveFocus();
  fireEvent.keyDown(annuler, { key: 'Tab', shiftKey: true });
  expect(document.activeElement).toBe(busy ? annuler : screen.getByRole('button', { name: 'Autoriser et envoyer' }));
  fireEvent.keyDown(document.activeElement!, { key: 'Tab' });
  expect(annuler).toHaveFocus();
  fireEvent.keyDown(annuler, { key: 'Escape' });
  expect(annulerAccord).toHaveBeenCalledTimes(1);
  expect(fermerProjet).not.toHaveBeenCalled();
  expect(confirmer).not.toHaveBeenCalled();
});
