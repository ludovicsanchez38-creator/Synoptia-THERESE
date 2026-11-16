import { useState } from 'react';
import { fireEvent, render, screen } from '@testing-library/react';
import { expect, it, vi } from 'vitest';
import { CloudConsentDialog } from './CloudConsentDialog';

function Scenario({ onCancel, onConfirm, busy = false }: {
  onCancel: () => void;
  onConfirm: () => void;
  busy?: boolean;
}) {
  const [visible, setVisible] = useState(false);
  return <>
    <button onClick={() => setVisible(true)}>Envoyer la demande</button>
    {visible && <CloudConsentDialog title="Autoriser cet envoi ?"
      dataCategories={['message saisi']} testId="accord" busy={busy}
      onCancel={() => { onCancel(); setVisible(false); }} onConfirm={onConfirm} />}
  </>;
}

function ouvrir(busy = false) {
  const onCancel = vi.fn();
  const onConfirm = vi.fn();
  const vue = render(<Scenario onCancel={onCancel} onConfirm={onConfirm} busy={busy} />);
  const declencheur = screen.getByRole('button', { name: 'Envoyer la demande' });
  declencheur.focus();
  fireEvent.click(declencheur);
  return { ...vue, declencheur, onCancel, onConfirm };
}

it('B-2020 : place le focus sur Annuler et isole le fond du dialogue modal', () => {
  const { declencheur } = ouvrir();
  expect(screen.getByRole('button', { name: 'Annuler' })).toHaveFocus();
  expect(screen.getByRole('alertdialog', { name: 'Autoriser cet envoi ?' })).toHaveAttribute('aria-modal', 'true');
  expect(declencheur.closest('[inert]')).not.toBeNull();
  expect(declencheur.closest('[aria-hidden="true"]')).not.toBeNull();
});

it('B-2020 : boucle Tab et Maj+Tab, y compris pendant l’enregistrement', () => {
  const { rerender, onCancel, onConfirm } = ouvrir();
  const annuler = screen.getByRole('button', { name: 'Annuler' });
  const autoriser = screen.getByRole('button', { name: 'Autoriser et envoyer' });
  autoriser.focus();
  fireEvent.keyDown(autoriser, { key: 'Tab' });
  expect(annuler).toHaveFocus();
  fireEvent.keyDown(annuler, { key: 'Tab', shiftKey: true });
  expect(autoriser).toHaveFocus();

  rerender(<Scenario onCancel={onCancel} onConfirm={onConfirm} busy />);
  expect(autoriser).toBeDisabled();
  annuler.focus();
  const tabulation = new KeyboardEvent('keydown', { key: 'Tab', bubbles: true, cancelable: true });
  fireEvent(annuler, tabulation);
  expect(tabulation.defaultPrevented).toBe(true);
  expect(annuler).toHaveFocus();
  expect(onConfirm).not.toHaveBeenCalled();
});

it.each([false, true])('B-2020 : Échap annule sans envoi et rend le focus au déclencheur (occupé : %s)', (busy) => {
  const { declencheur, onCancel, onConfirm } = ouvrir(busy);
  fireEvent.keyDown(screen.getByRole('button', { name: 'Annuler' }), { key: 'Escape' });
  expect(onCancel).toHaveBeenCalledTimes(1);
  expect(onConfirm).not.toHaveBeenCalled();
  expect(screen.queryByRole('alertdialog')).not.toBeInTheDocument();
  expect(declencheur).toHaveFocus();
  expect(declencheur.closest('[inert]')).toBeNull();
  expect(declencheur.closest('[aria-hidden="true"]')).toBeNull();
});
