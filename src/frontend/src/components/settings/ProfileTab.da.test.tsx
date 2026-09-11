/**
 * DA « Application affinée », lot 9 : la rubrique Profil.
 *
 * Gardes mécaniques du design (version 6) : les treize identifiants, les
 * libellés portés par `FormField`, l'étoile unique du champ obligatoire, le
 * champ de contexte hors de la grille d'identité, l'interrupteur du mode
 * démo enfin nommé, et l'étiquette de statut qui accepte de revenir à la
 * ligne.
 */
import { render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import { ProfileTab, type ProfileFormData } from './ProfileTab';
import { useDemoStore } from '../../stores/demoStore';
import type { UserProfile } from '../../services/api';

const VIDE: ProfileFormData = {
  name: '',
  nickname: '',
  company: '',
  role: '',
  email: '',
  location: '',
  address: '',
  siren: '',
  tva_intra: '',
  siret: '',
  code_ape: '',
  nda: '',
  context: '',
};

/** Les treize champs du profil, dans l'ordre du design. */
const IDS_IDENTITE = [
  'settings-profile-name',
  'settings-profile-nickname',
  'settings-profile-company',
  'settings-profile-role',
  'settings-profile-email',
  'settings-profile-location',
];
const IDS_EMETTEUR = [
  'settings-profile-address',
  'settings-profile-siren',
  'settings-profile-tva',
  'settings-profile-siret',
  'settings-profile-ape',
  'settings-profile-nda',
];

function rendre(profil: UserProfile | null = null, form: Partial<ProfileFormData> = {}) {
  return render(
    <ProfileTab
      profileForm={{ ...VIDE, ...form }}
      setProfileForm={vi.fn()}
      profile={profil}
      saving={false}
      saved={false}
      setError={vi.fn()}
      onSave={vi.fn()}
      onImport={vi.fn()}
    />,
  );
}

beforeEach(() => {
  useDemoStore.setState({ enabled: false });
});

describe('lot 9, garde 6 : les champs du profil', () => {
  it('les treize identifiants existent, une seule fois chacun', () => {
    rendre();

    for (const id of [...IDS_IDENTITE, ...IDS_EMETTEUR, 'settings-profile-context']) {
      expect(document.querySelectorAll(`#${id}`), `${id} n’apparaît pas une seule fois`).toHaveLength(1);
    }
  });

  it('identité et émetteur vivent dans deux cartes distinctes', () => {
    rendre();

    const titreEmetteur = screen.getByRole('heading', { name: 'Profil émetteur des factures' });
    const carteEmetteur = titreEmetteur.closest('section, article');
    expect(carteEmetteur).not.toBeNull();

    // Les six champs de facturation sont dans la carte émetteur, aucun des
    // six champs d'identité n'y est.
    for (const id of IDS_EMETTEUR) {
      expect(carteEmetteur?.querySelector(`#${id}`), `${id} hors de la carte émetteur`).not.toBeNull();
    }
    for (const id of IDS_IDENTITE) {
      expect(carteEmetteur?.querySelector(`#${id}`), `${id} dans la carte émetteur`).toBeNull();
    }
  });

  it('chaque champ est relié à son label par `FormField` (htmlFor = id)', () => {
    rendre();

    for (const id of [...IDS_IDENTITE, ...IDS_EMETTEUR, 'settings-profile-context']) {
      const label = document.querySelector(`label[for="${id}"]`);
      expect(label, `aucun label ne pointe sur ${id}`).not.toBeNull();
      expect(label?.className, `le label de ${id} n’est pas celui de FormField`).toMatch(
        /font-semibold/,
      );
      expect(label?.className).toMatch(/text-sm/);
    }
  });

  it('« Nom complet » garde une seule étoile, celle de `FormField`', () => {
    rendre();

    const champ = screen.getByLabelText(/^Nom complet/);
    expect(champ).toHaveAttribute('id', 'settings-profile-name');

    const label = document.querySelector('label[for="settings-profile-name"]');
    expect(label?.textContent).toBe('Nom complet*');
    expect((label?.textContent?.match(/\*/g) ?? []).length).toBe(1);
  });

  it('les six libellés de la carte émetteur sont recopiés au caractère près', () => {
    rendre();

    const attendus: [string, string][] = [
      ['settings-profile-address', 'Adresse (facturation)'],
      ['settings-profile-siren', 'SIREN'],
      ['settings-profile-tva', 'TVA intracommunautaire'],
      ['settings-profile-siret', 'SIRET (requis pour facturer)'],
      ['settings-profile-ape', 'Code APE / NAF'],
      // Apostrophe DROITE : ce libellé est recopié du source (ProfileTab.tsx:372),
      // pas retapé. Le design dit « au caractère près ».
      ['settings-profile-nda', "N° de déclaration d'activité (organisme de formation)"],
    ];

    for (const [id, libelle] of attendus) {
      expect(document.querySelector(`label[for="${id}"]`)?.textContent).toBe(libelle);
    }
  });

  it('le champ de contexte est hors de la grille d’identité, en pleine largeur', () => {
    rendre();

    const contexte = document.getElementById('settings-profile-context');
    expect(contexte).not.toBeNull();

    const grille = document.querySelector('.grid-cols-1.min-\\[1024px\\]\\:grid-cols-2');
    expect(grille, 'la grille d’identité est introuvable').not.toBeNull();
    expect(grille?.contains(contexte)).toBe(false);
    expect(grille?.querySelectorAll('input')).toHaveLength(IDS_IDENTITE.length);
    expect(document.querySelector('label[for="settings-profile-context"]')?.textContent).toBe(
      'Ce que Thérèse doit savoir',
    );
  });

  // Revue du diff, point 3 : `gap-x-4` seul ne pose AUCUNE gouttière entre les
  // rangées, et `FormField` n'a pas de marge basse (`space-y-1.5` interne
  // seulement). Le libellé « Entreprise » collait au champ « Nom complet ».
  // La maquette obtient cet espace par `.champ{margin-bottom:var(--espace-3)}`
  // (`maquettes/da/base.css:135`), que `.grille-2` laisse exprès (`:140`).
  it('les deux grilles de champs ont une gouttière verticale', () => {
    rendre();

    const grilles = document.querySelectorAll('.grid-cols-1.min-\\[1024px\\]\\:grid-cols-2');
    expect(grilles, 'les deux grilles du profil ne sont pas là').toHaveLength(2);
    grilles.forEach((grille, i) => {
      expect(grille.className, `grille ${i + 1} sans gouttière verticale`).toMatch(/gap-y-4/);
      expect(grille.className).toMatch(/gap-x-4/);
    });
  });

  it('l’erreur de la coque n’est plus rendue ici : elle ne s’annonce qu’une fois', () => {
    rendre();
    // `ProfileTabProps` n'a plus de prop `error` : la coque la rend, seule.
    expect(screen.queryByRole('alert')).toBeNull();
  });
});

describe('lot 9, garde 6 : l’étiquette de statut du profil', () => {
  it('profil absent : pilule « attention » qui accepte de revenir à la ligne', () => {
    rendre(null);

    const pilule = screen.getByText('Profil non configuré - Configure ton identité');
    expect(pilule).toHaveAttribute('data-etiquette');
    expect(pilule.className).toMatch(/text-warning/);
    // 45 caractères dans une pilule `whitespace-nowrap` débordent en petite
    // largeur ou en grande taille de police (revue v5, point 9).
    expect(pilule.className).toMatch(/whitespace-normal/);
    expect(pilule.className).not.toMatch(/whitespace-nowrap/);
  });

  it('profil chargé : pilule « succès », même chaîne, même retour à la ligne', () => {
    rendre({ display_name: 'Marie-Charlotte de la Tour-Maubourg' } as UserProfile);

    const pilule = screen.getByText(/Profil configuré : Marie-Charlotte de la Tour-Maubourg/);
    expect(pilule).toHaveAttribute('data-etiquette');
    expect(pilule.className).toMatch(/text-success/);
    expect(pilule.className).toMatch(/whitespace-normal/);
    expect(pilule.className).not.toMatch(/whitespace-nowrap/);
  });
});

describe('lot 9, garde 6 : l’interrupteur du mode démo', () => {
  it('a un rôle, un nom et un état, au lieu d’être un bouton muet', () => {
    rendre();

    const interrupteur = screen.getByRole('switch', { name: 'Mode démo' });
    expect(interrupteur).toHaveAttribute('aria-checked', 'false');
    expect(interrupteur).toHaveAttribute('type', 'button');
    expect(screen.getByTestId('mode-demo-section')).toBeInTheDocument();
  });

  // Revue du diff, point 7 : avec « Profil » et « Profil émetteur des factures »
  // passés en h2 (`CarteTete`), un h3 laissé ici faisait du mode démo une
  // SOUS-section de la facturation pour qui navigue par titres. Le lot a
  // pourtant ajouté `niveau` à `CarteTete` exactement pour ce motif.
  it('vit dans une carte, titre de niveau 2 comme ses deux voisines', () => {
    rendre();

    const titre = screen.getByRole('heading', { name: 'Mode Démo', level: 2 });
    const carte = titre.closest('section, article');
    expect(carte).toBe(screen.getByTestId('mode-demo-section'));
    expect(carte?.className).toMatch(/shadow-sm/);
    // Aucun titre orphelin : le plan de la rubrique est h2, h2, h2.
    expect(screen.queryAllByRole('heading', { level: 3 })).toHaveLength(0);
  });

  it('son état suit le store', () => {
    useDemoStore.setState({ enabled: true });
    rendre();

    expect(screen.getByRole('switch', { name: 'Mode démo' })).toHaveAttribute(
      'aria-checked',
      'true',
    );
    expect(screen.getByRole('status')).toHaveTextContent('Mode démo actif');
  });
});
