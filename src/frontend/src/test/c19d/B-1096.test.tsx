import { render, screen } from '@testing-library/react';
import { expect, it, vi } from 'vitest';
import { VueDEnsemble } from '../../components/ui/VueDEnsemble';
it.each([true, false])('B-1096 : le titre complet reste disponible (destination %s)', (destination) => {
  const libelle = 'Rénover la couverture du bâtiment principal et préparer tous les documents pour les artisans';
  render(<VueDEnsemble etat="pret" onReessayer={vi.fn()} messageDePanne="Panne" messageDeChargement="Chargement"
    familles={[{ cle: 'documents', libelle: 'Documents', total: 1, texteDuVide: 'Vide', elements: [{ id: '1', libelle, ...(destination ? { onOuvrir: vi.fn(), nomAccessible: libelle } : {}) }] }]} />);
  expect(screen.getByText(libelle)).toHaveAttribute('title', libelle);
});
