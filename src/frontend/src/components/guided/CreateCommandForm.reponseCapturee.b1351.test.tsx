/**
 * B-1351 (persona Claire, cycle 13) : « Sauvegarder comme raccourci » depuis
 * une réponse du chat.
 *
 * La description et l'aperçu « Réponse capturée » montraient le Markdown brut
 * (« **Compte rendu de séance** **Cliente :** … »), la case « Afficher sur la
 * page d'accueil » était cochée d'office alors que la réponse capturée était
 * un compte rendu confidentiel, et la catégorie s'affichait « General ».
 */
import { render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

import { CreateCommandForm } from './CreateCommandForm';

const reponse = '**Compte rendu de séance**\n\n**Cliente :** Hélène Ménard-Lefèvre\n\n- Objectif : `reconversion`\n\n## Suite\n\nProchaine séance le 2 octobre.';

function rendre(avecCapture: boolean) {
  render(
    <CreateCommandForm
      onSubmit={vi.fn()}
      onBack={vi.fn()}
      initialContent="Rédige le compte rendu"
      initialDescription={avecCapture ? reponse : undefined}
      capturedPreview={avecCapture ? reponse : undefined}
    />,
  );
}

describe('raccourci créé depuis une réponse (B-1351)', () => {
  it('la description et l’aperçu sont du texte, sans balises Markdown', () => {
    rendre(true);
    const description = screen.getByLabelText('Description') as HTMLInputElement;
    expect(description.value).toMatch(/^Compte rendu de séance Cliente : Hélène/);
    const apercu = screen.getByText(/Prochaine séance le 2 octobre/);
    for (const texte of [description.value, apercu.textContent ?? '']) {
      expect(texte).not.toMatch(/\*\*|`|##|^- /);
    }
  });

  it('une réponse capturée ne s’affiche pas sur l’Accueil par défaut', () => {
    rendre(true);
    expect(screen.getByLabelText("Afficher sur la page d'accueil")).not.toBeChecked();
  });

  it('un raccourci créé de toutes pièces reste proposé sur l’Accueil', () => {
    rendre(false);
    expect(screen.getByLabelText("Afficher sur la page d'accueil")).toBeChecked();
  });

  it('la catégorie par défaut s’écrit « Général »', () => {
    rendre(true);
    expect(screen.getByRole('option', { name: 'Général' })).toBeInTheDocument();
    expect(screen.queryByRole('option', { name: 'General' })).not.toBeInTheDocument();
  });
});
