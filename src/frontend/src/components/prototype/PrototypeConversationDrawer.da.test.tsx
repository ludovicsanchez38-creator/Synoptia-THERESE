/**
 * DA « Application affinée », lot 3 : le tiroir des conversations
 * (`docs/plans/2026-09-11-da-lot3-tiroir-design.md`, § 5).
 * Mêmes données, mêmes états, mêmes destinations.
 */
import { readFileSync } from 'node:fs';
import { join } from 'node:path';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { fireEvent, render, screen, within } from '@testing-library/react';

import { useChatStore, type Conversation } from '../../stores/chatStore';
import { PrototypeConversationDrawer } from './PrototypeConversationDrawer';

vi.mock('../../hooks/useConversationSync', () => ({
  useConversationSync: vi.fn(() => ({ syncConversations: vi.fn(), loadConversationMessages: vi.fn() })),
}));

vi.mock('../../services/api/chat', () => ({
  renameConversation: vi.fn().mockResolvedValue({}),
  deleteConversation: vi.fn().mockResolvedValue(undefined),
  exportConversation: vi.fn().mockResolvedValue(undefined),
}));

const COULEUR_EN_DUR = /#[0-9A-Fa-f]{3,8}\b|(?<![A-Za-z])rgba?\(|(?<![A-Za-z])hsla?\(|\bcolor-mix\(/;
const COMMENTAIRE = /^\s*(\/\/|\*|\/\*)/;

function classesDUnNoeud(n: Element): string {
  const brut = (n as HTMLElement).className;
  if (typeof brut === 'string') return brut;
  const svg = (n as SVGElement).className;
  return typeof svg === 'object' && svg && 'baseVal' in svg ? svg.baseVal : '';
}

function interactifsSousLePlancher(racine: HTMLElement): string[] {
  const fautifs: string[] = [];
  for (const el of racine.querySelectorAll('button, input, select, textarea, a')) {
    const noeuds = [el, ...Array.from(el.querySelectorAll('*'))];
    for (const n of noeuds) {
      if (/\btext-xs\b/.test(classesDUnNoeud(n))) {
        fautifs.push(((el as HTMLElement).textContent ?? el.tagName).trim().slice(0, 48));
        break;
      }
    }
  }
  return fautifs;
}

function conversation(id: string, title: string, updatedAt: Date, extra: Partial<Conversation> = {}): Conversation {
  return {
    id,
    title,
    messages: [{ id: `m-${id}`, role: 'user', content: 'bonjour', timestamp: updatedAt }],
    createdAt: updatedAt,
    updatedAt,
    synced: true,
    ...extra,
  };
}

function poser(conversations: Conversation[], extra: Partial<Parameters<typeof PrototypeConversationDrawer>[0]> = {}) {
  useChatStore.setState({
    conversations,
    currentConversationId: extra.navigationLocked ? null : (conversations[0]?.id ?? null),
  });
  const onClose = extra.onClose ?? vi.fn();
  const onOpenChat = extra.onOpenChat ?? vi.fn();
  return {
    onClose,
    onOpenChat,
    ...render(
      <PrototypeConversationDrawer
        onClose={onClose}
        onOpenChat={onOpenChat}
        navigationLocked={extra.navigationLocked}
        surface={extra.surface}
      />,
    ),
  };
}

beforeEach(() => {
  vi.clearAllMocks();
  useChatStore.setState({ conversations: [], currentConversationId: null });
});

describe('Lot 3 DA : coque du tiroir', () => {
  it('le panneau fait 22 rem, le titre est un h2 text-base qui nomme la région', () => {
    poser([conversation('c1', 'Relance clients', new Date())]);
    const panneau = screen.getByTestId('prototype-conversation-drawer');
    expect(panneau.className).toMatch(/w-\[22rem\]/);
    expect(panneau.className).toMatch(/\bleft-16\b/);
    expect(panneau.className).not.toMatch(/\bleft-14\b/);
    const titre = screen.getByRole('heading', { level: 2, name: 'Conversations' });
    expect(titre.id).toBe('prototype-conversation-drawer-title');
    expect(titre.className).toMatch(/\btext-base\b/);
    expect(screen.getByRole('region', { name: 'Conversations' })).toBe(panneau);
  });

  it('« Nouvelle conversation » est le Button primary du pied, et surface=new lui donne le focus', () => {
    const { rerender } = poser([conversation('c1', 'Relance clients', new Date())], { surface: 'new' });
    const bouton = screen.getByRole('button', { name: 'Nouvelle conversation' });
    expect(bouton.className).toMatch(/\bbg-accent-fill\b/);
    expect(bouton.className).toMatch(/\bh-9\b/);
    expect(bouton.parentElement?.className).toMatch(/border-t/);
    expect(bouton).toHaveFocus();
    rerender(
      <PrototypeConversationDrawer onClose={vi.fn()} onOpenChat={vi.fn()} surface="search" />,
    );
    expect(screen.getByLabelText('Rechercher une conversation')).toHaveFocus();
  });
});

describe('Lot 3 DA : lignes de conversation', () => {
  it('une ligne courante porte aria-current et bg-accent-tint, le kebab 36 px muted, Entrée ouvre encore le chat', () => {
    const onOpenChat = vi.fn();
    useChatStore.setState({
      conversations: [conversation('c1', 'Relance clients', new Date())],
      currentConversationId: 'c1',
    });
    render(<PrototypeConversationDrawer onClose={vi.fn()} onOpenChat={onOpenChat} />);
    const ligne = screen.getByRole('button', { name: /^Relance clients/ });
    expect(ligne.tagName).toBe('BUTTON');
    expect(ligne).toHaveAttribute('aria-current', 'page');
    expect(ligne.className).toMatch(/bg-accent-tint/);
    const kebab = screen.getByRole('button', { name: 'Actions pour Relance clients' });
    expect(kebab.className).toMatch(/\bh-9\b/);
    expect(kebab.className).toMatch(/\bw-9\b/);
    expect(kebab.className).toMatch(/text-text-muted/);
    fireEvent.click(ligne);
    expect(onOpenChat).toHaveBeenCalledTimes(1);
  });

  it('updatedLabel : heure du jour civil, heure d’hier, jour de la semaine, puis jour et mois', () => {
    const maintenant = new Date();
    const aujourdhui = new Date(maintenant.getFullYear(), maintenant.getMonth(), maintenant.getDate(), 11, 42);
    const hier = new Date(maintenant.getFullYear(), maintenant.getMonth(), maintenant.getDate() - 1, 17, 12);
    const troisJours = new Date(maintenant.getFullYear(), maintenant.getMonth(), maintenant.getDate() - 3, 10, 0);
    const dixJours = new Date(maintenant.getFullYear(), maintenant.getMonth(), maintenant.getDate() - 10, 9, 0);
    useChatStore.setState({
      conversations: [
        conversation('c-auj', 'Aujourd’hui', aujourdhui),
        conversation('c-hier', 'Hier soir', hier),
        conversation('c-sem', 'Cette semaine', troisJours),
        conversation('c-loin', 'Plus loin', dixJours),
      ],
      currentConversationId: null,
    });
    render(<PrototypeConversationDrawer onClose={vi.fn()} onOpenChat={vi.fn()} />);
    const heureAuj = aujourdhui.toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' });
    const heureHier = hier.toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' });
    const jourSemaine = troisJours.toLocaleDateString('fr-FR', { weekday: 'short' });
    const jourMois = dixJours.toLocaleDateString('fr-FR', { day: 'numeric', month: 'short' });
    expect(screen.getByRole('button', { name: /^Aujourd’hui/ })).toHaveTextContent(heureAuj);
    expect(screen.getByRole('button', { name: /^Hier soir/ })).toHaveTextContent(heureHier);
    expect(screen.getByRole('button', { name: /^Cette semaine/ })).toHaveTextContent(jourSemaine);
    expect(screen.getByRole('button', { name: /^Plus loin/ })).toHaveTextContent(jourMois);
  });
});

describe('Lot 3 DA : états vides et erreurs', () => {
  it('vide sans requête : « Aucune conversation », pas « enregistrée » ; un seul geste au pied', () => {
    useChatStore.setState({ conversations: [], currentConversationId: null });
    render(<PrototypeConversationDrawer onClose={vi.fn()} onOpenChat={vi.fn()} />);
    expect(screen.getByRole('heading', { name: 'Aucune conversation' })).toBeInTheDocument();
    expect(screen.queryByText(/enregistrée/)).toBeNull();
    expect(screen.getByText('Ta première demande à Thérèse apparaîtra ici, avec ce qu’elle a produit.')).toBeInTheDocument();
    expect(screen.getAllByRole('button', { name: 'Nouvelle conversation' })).toHaveLength(1);
    expect(screen.getByRole('button', { name: 'Nouvelle conversation' }).parentElement?.className).toMatch(/border-t/);
  });

  it('vide avec requête : « Aucune conversation trouvée », le pied reste le seul geste', () => {
    useChatStore.setState({
      conversations: [conversation('c1', 'Relance clients', new Date())],
      currentConversationId: null,
    });
    render(<PrototypeConversationDrawer onClose={vi.fn()} onOpenChat={vi.fn()} />);
    fireEvent.change(screen.getByLabelText('Rechercher une conversation'), { target: { value: 'zzzzabsurde' } });
    expect(screen.getByRole('heading', { name: 'Aucune conversation trouvée' })).toBeInTheDocument();
    expect(screen.getAllByRole('button', { name: 'Nouvelle conversation' })).toHaveLength(1);
  });

  it('Alerte sur verrouillage, zéro Réessayer ; la confirmation de suppression n’est pas une alerte', () => {
    useChatStore.setState({
      conversations: [conversation('c1', 'Relance clients', new Date())],
      currentConversationId: null,
    });
    render(<PrototypeConversationDrawer navigationLocked onClose={vi.fn()} onOpenChat={vi.fn()} />);
    fireEvent.click(screen.getByRole('button', { name: /^Relance clients/ }));
    const tiroir = screen.getByTestId('prototype-conversation-drawer');
    expect(within(tiroir).getByRole('alert')).toHaveTextContent(
      'Arrête la réponse en cours avant de changer de conversation.',
    );
    expect(within(tiroir).queryByRole('button', { name: 'Réessayer' })).toBeNull();

    fireEvent.click(screen.getByRole('button', { name: 'Actions pour Relance clients' }));
    fireEvent.click(screen.getByRole('menuitem', { name: 'Supprimer' }));
    const confirmation = screen.getByTestId('conversation-delete-confirmation');
    expect(confirmation.getAttribute('role')).not.toBe('alert');
    expect(within(confirmation).getByRole('button', { name: 'Annuler' })).toBeInTheDocument();
    expect(within(confirmation).getByRole('button', { name: 'Confirmer la suppression' })).toBeInTheDocument();
  });
});

describe('Lot 3 DA : plancher typographique et jetons', () => {
  it('aucune classe text-xs sur un interactif ni dans son sous-arbre', () => {
    useChatStore.setState({
      conversations: [conversation('c1', 'Relance clients', new Date())],
      currentConversationId: 'c1',
    });
    render(<PrototypeConversationDrawer onClose={vi.fn()} onOpenChat={vi.fn()} />);
    const fautifs = interactifsSousLePlancher(screen.getByTestId('prototype-conversation-drawer'));
    expect(fautifs).toEqual([]);
  });

  it('aucune couleur en dur dans PrototypeConversationDrawer.tsx', () => {
    const contenu = readFileSync(join(__dirname, 'PrototypeConversationDrawer.tsx'), 'utf8');
    const fautifs: string[] = [];
    contenu.split('\n').forEach((ligne, i) => {
      if (COMMENTAIRE.test(ligne)) return;
      if (COULEUR_EN_DUR.test(ligne)) fautifs.push(`${i + 1}:${ligne.trim()}`);
    });
    expect(fautifs).toEqual([]);
  });
});
