/**
 * Un champ dit son erreur à qui ne voit pas l'écran.
 *
 * `FormField` calculait `errorId` et `descId`… sans jamais les poser :
 * `aria-describedby` n'apparaissait nulle part. Un lecteur d'écran
 * annonçait le champ et son label, mais ni l'explication ni le message
 * d'erreur — le rouge sous le champ n'existait que pour l'œil.
 *
 * La primitive censée standardiser l'accessibilité des formulaires avait
 * donc elle-même le défaut, ce qui explique peut-être qu'elle soit restée
 * inutilisée : elle n'apportait pas assez pour valoir la migration.
 */
import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';

import { FormField } from './FormField';
import { Input } from './Input';

describe('FormField', () => {
  it('lie le label au champ', () => {
    render(
      <FormField label="Nom du projet" htmlFor="nom">
        <Input id="nom" />
      </FormField>,
    );

    expect(screen.getByLabelText('Nom du projet')).toBeInTheDocument();
  });

  it('rattache l’erreur au champ, pas seulement à l’écran', () => {
    render(
      <FormField label="Budget" htmlFor="budget" error="Le budget doit être un nombre">
        <Input id="budget" />
      </FormField>,
    );

    const champ = screen.getByLabelText('Budget');
    const decrit = (champ.getAttribute('aria-describedby') || '').split(' ');
    const message = screen.getByRole('alert');

    expect(decrit).toContain(message.id);
    expect(message).toHaveTextContent('Le budget doit être un nombre');
  });

  it('rattache aussi l’explication', () => {
    render(
      <FormField label="Taux" htmlFor="taux" description="En pourcentage, sans le signe">
        <Input id="taux" />
      </FormField>,
    );

    const champ = screen.getByLabelText('Taux');
    const decrit = champ.getAttribute('aria-describedby') || '';

    expect(decrit).toContain('taux-desc');
  });

  it('marque le champ invalide quand il l’est', () => {
    render(
      <FormField label="Courriel" htmlFor="mail" error="Adresse invalide">
        <Input id="mail" />
      </FormField>,
    );

    expect(screen.getByLabelText('Courriel')).toHaveAttribute('aria-invalid', 'true');
  });

  it('sans erreur ni description, n’invente aucun rattachement', () => {
    render(
      <FormField label="Titre" htmlFor="titre">
        <Input id="titre" />
      </FormField>,
    );

    expect(screen.getByLabelText('Titre')).not.toHaveAttribute('aria-describedby');
  });
});
