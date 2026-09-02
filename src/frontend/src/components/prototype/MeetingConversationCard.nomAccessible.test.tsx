/**
 * B-263 : le nom accessible d'un champ doit contenir son libellé visible.
 *
 * WCAG 2.5.3 « Label in Name » (niveau A) : ce que l'utilisateur LIT doit
 * servir à désigner le champ. Le champ du lieu affiche « Lieu ou lien » et
 * portait un `aria-label="Lieu du rendez-vous"` qui écrase le texte du
 * `<label>` qui l'enveloppe : une commande vocale « Lieu ou lien », dictée
 * d'après l'écran, n'activait pas le champ.
 *
 * Le test interroge le RÔLE et le NOM accessible, pas le texte du `<label>` :
 * `getByLabelText` remonte l'input par le contenu de son label et passerait
 * donc même avec l'`aria-label` fautif. C'est `getByRole(..., { name })` qui
 * calcule le nom réellement exposé, celui que lisent lecteur d'écran et
 * commande vocale.
 */
import { render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import type { Calendar } from '../../services/api';
import { MeetingWorkspaceCanvas } from './MeetingConversationCard';
import type { MeetingWorkspaceData } from './usePrototypeMeetingData';

const calendar: Calendar = {
  id: 'cal-1', account_id: null, summary: 'Agenda local', description: null,
  timezone: 'Europe/Paris', primary: true, provider: 'local', synced_at: null,
};
const workspace: MeetingWorkspaceData = {
  calendars: [calendar], events: [], contacts: [], accounts: [], unavailableSources: [],
};

function rendreLeFormulaire() {
  render(<MeetingWorkspaceCanvas
    resource={{ status: 'ready', data: workspace, error: null }} eventResource={null}
    target="new-event" onRetry={vi.fn()} onRetryEvent={vi.fn()} onCreateEvent={vi.fn()}
    onCreateNote={vi.fn()} onAbandon={vi.fn()} onOpenClassic={vi.fn()} onEnsureCalendar={vi.fn()}
  />);
}

describe('B-263 : le champ du lieu se désigne par le libellé qu’on lit', () => {
  it('« Lieu ou lien » désigne le champ du lieu', () => {
    rendreLeFormulaire();
    expect(screen.getByRole('textbox', { name: 'Lieu ou lien' })).toBeInTheDocument();
  });

  it("aucun champ du formulaire ne cache son libellé visible derrière un autre nom", () => {
    rendreLeFormulaire();
    // Garantie de portée : le défaut se réintroduit d'un `aria-label` posé sur
    // n'importe lequel des champs, et une liste figée se périmerait au premier
    // champ ajouté. On balaie donc tout le formulaire.
    const formulaire = screen.getByTestId('meeting-new-event-form');
    const champs = Array.from(
      formulaire.querySelectorAll<HTMLElement>('input, textarea, select'),
    );
    expect(champs.length).toBeGreaterThan(0);

    const fautifs = champs
      .map((champ) => {
        const label = champ.closest('label');
        // Le libellé visible est le texte du `<label>` sans celui du champ.
        const visible = (label?.textContent ?? '').replace(champ.textContent ?? '', '').trim();
        const nom = champ.getAttribute('aria-label') ?? visible;
        return { visible, nom };
      })
      .filter(({ visible, nom }) => visible.length > 0 && !nom.includes(visible));

    expect(fautifs).toEqual([]);
  });
});
