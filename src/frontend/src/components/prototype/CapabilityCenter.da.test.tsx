/**
 * DA « Application affinée », lot 3 : le catalogue des capacités
 * (`docs/plans/2026-09-11-da-lot3-tiroir-design.md`, § 5).
 * Mêmes données, mêmes états, mêmes destinations.
 */
import { readFileSync } from 'node:fs';
import { join } from 'node:path';
import { describe, expect, it, vi } from 'vitest';
import { fireEvent, render, screen, within } from '@testing-library/react';

import { CapabilityCenter, capabilities } from './CapabilityCenter';
import { typeCapacite } from './typeCapacite';

const IDS_SCENARIO = [
  'daily-brief',
  'email',
  'calendar',
  'contacts-memory',
  'billing',
  'decision-board',
  'agents',
] as const;
const IDS_PROMPT = ['web-research', 'legal', 'skills-commands'] as const;
const COULEUR_EN_DUR = /#[0-9A-Fa-f]{3,8}\b|(?<![A-Za-z])rgba?\(|(?<![A-Za-z])hsla?\(|\bcolor-mix\(/;
const COMMENTAIRE = /^\s*(\/\/|\*|\/\*)/;

function sourceFonctionCapabilityCenter(): string {
  const contenu = readFileSync(join(__dirname, 'CapabilityCenter.tsx'), 'utf8');
  const debut = contenu.indexOf('export function CapabilityCenter');
  const fin = contenu.indexOf('\nfunction TrustRow', debut);
  return contenu.slice(debut, fin < 0 ? contenu.length : fin);
}

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

function ouvrir() {
  const onChoose = vi.fn();
  const onClose = vi.fn();
  const vue = render(<CapabilityCenter onClose={onClose} onChoose={onChoose} />);
  return { onChoose, onClose, ...vue };
}

describe('Lot 3 DA : titre et compte du catalogue', () => {
  it('le h2#capability-center-title dit Capacités ; le compte suit capabilities.length', () => {
    ouvrir();
    const titre = screen.getByRole('heading', { level: 2, name: 'Capacités' });
    expect(titre.id).toBe('capability-center-title');
    const dialogue = screen.getByRole('dialog');
    expect(dialogue).toHaveAttribute('aria-labelledby', 'capability-center-title');
    expect(dialogue).toHaveTextContent(`${capabilities.length} capacités`);
  });
});

describe('Lot 3 DA : typeCapacite', () => {
  it('classe prompts, actions, les 7 parcours et une vue ; un clic onChoose reste inchangé', () => {
    const parId = Object.fromEntries(capabilities.map((c) => [c.id, c]));
    for (const id of IDS_PROMPT) {
      expect(typeCapacite(parId[id]), id).toBe('Demande relue');
    }
    expect(typeCapacite(parId.attention)).toBe('Action');
    expect(typeCapacite(parId.office)).toBe('Action');
    for (const id of IDS_SCENARIO) {
      expect(typeCapacite(parId[id]), id).toBe('Parcours');
    }
    expect(typeCapacite(parId.tasks)).toBe('Vue');

    const { onChoose } = ouvrir();
    expect(screen.getByRole('button', { name: /^Tâches/ })).toHaveTextContent('Vue');
    expect(screen.getByRole('button', { name: /^Relances et alertes/ })).toHaveTextContent('Action');
    expect(screen.getByRole('button', { name: /^Brief du jour/ })).toHaveTextContent('Parcours');
    expect(screen.getByRole('button', { name: /^Email/ })).toHaveTextContent('Parcours');
    expect(screen.getByRole('button', { name: /^Agenda/ })).toHaveTextContent('Parcours');

    fireEvent.click(screen.getByRole('tab', { name: /Développer mon activité/ }));
    expect(screen.getByRole('button', { name: /^Contacts/ })).toHaveTextContent('Parcours');
    expect(screen.getByRole('button', { name: /^Facturer un client/ })).toHaveTextContent('Parcours');

    fireEvent.click(screen.getByRole('tab', { name: /Créer et produire/ }));
    expect(screen.getByRole('button', { name: /^Word, PowerPoint et Excel/ })).toHaveTextContent('Action');

    fireEvent.click(screen.getByRole('tab', { name: /Comprendre et décider/ }));
    expect(screen.getByRole('button', { name: /^Décision/ })).toHaveTextContent('Parcours');
    expect(screen.getByRole('button', { name: /^Recherche web/ })).toHaveTextContent('Demande relue');
    expect(screen.getByRole('button', { name: /^Références juridiques/ })).toHaveTextContent('Demande relue');

    fireEvent.click(screen.getByRole('tab', { name: /Automatiser et déléguer/ }));
    expect(screen.getByRole('button', { name: /^Améliorer THÉRÈSE/ })).toHaveTextContent('Parcours');
    expect(screen.getByRole('button', { name: /^Skills et commandes/ })).toHaveTextContent('Demande relue');

    fireEvent.click(screen.getByRole('tab', { name: /Organiser mon quotidien/ }));
    fireEvent.click(screen.getByRole('button', { name: /^Tâches/ }));
    expect(onChoose).toHaveBeenCalledTimes(1);
    expect(onChoose.mock.calls[0][0].id).toBe('tasks');
  });
});

describe('Lot 3 DA : focus, intentions, vide, pied', () => {
  it('un seul data-dialog-autofocus, le focus va au champ', () => {
    const { container } = ouvrir();
    const dialogue = container.querySelector('[role="dialog"]') as HTMLElement;
    expect(dialogue.querySelectorAll('[data-dialog-autofocus]')).toHaveLength(1);
    expect(document.activeElement).toBe(screen.getByLabelText('Rechercher une capacité'));
  });

  it('tablist Intentions, six onglets, premier groupe organize, plus de style backgroundColor', () => {
    ouvrir();
    const liste = screen.getByRole('tablist', { name: 'Intentions' });
    const onglets = within(liste).getAllByRole('tab');
    expect(onglets).toHaveLength(6);
    expect(onglets[0].id).toBe('capability-group-organize');
    expect(sourceFonctionCapabilityCenter()).not.toMatch(/style=\{\{/);
  });

  it('EtatVide « Aucune capacité trouvée » sur une requête absurde', () => {
    ouvrir();
    fireEvent.change(screen.getByLabelText('Rechercher une capacité'), { target: { value: 'xyzabc123' } });
    expect(screen.getByRole('heading', { name: 'Aucune capacité trouvée' })).toBeInTheDocument();
    expect(
      screen.getByText('Essaie avec le résultat souhaité, par exemple « devis » ou « analyser ».'),
    ).toBeInTheDocument();
  });

  it('le pied contient Demande relue et s’ouvre au clic', () => {
    ouvrir();
    const pied = screen.getByRole('dialog').querySelector('footer') as HTMLElement;
    expect(pied).toHaveTextContent('Demande relue');
    expect(pied).toHaveTextContent("s'ouvre au clic");
  });
});

describe('Lot 3 DA : plancher, translate et ombres du catalogue', () => {
  it('aucune classe text-xs sur un interactif ni dans son sous-arbre', () => {
    const { container } = ouvrir();
    const dialogue = container.querySelector('[role="dialog"]') as HTMLElement;
    expect(interactifsSousLePlancher(dialogue)).toEqual([]);
  });

  it('plus de hover:-translate-y ni d’ombre rgba sur le dialogue et les cartes', () => {
    const source = sourceFonctionCapabilityCenter();
    expect(source).not.toMatch(/hover:-translate-y/);
    const fautifs: string[] = [];
    source.split('\n').forEach((ligne, i) => {
      if (COMMENTAIRE.test(ligne)) return;
      if (COULEUR_EN_DUR.test(ligne)) fautifs.push(`${i + 1}:${ligne.trim()}`);
    });
    expect(fautifs).toEqual([]);
  });
});
