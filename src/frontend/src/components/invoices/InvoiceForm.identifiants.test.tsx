/**
 * Deux lignes de facture, deux identifiants distincts.
 *
 * Le correctif de nommage avait posé `id="invoiceform-quantite"` à
 * l'intérieur d'un `lines.map(...)` : avec deux lignes, deux éléments
 * portaient le même identifiant. Le DOM n'en accepte qu'un — le label de la
 * deuxième ligne renvoyait donc au champ de la PREMIÈRE, et un lecteur
 * d'écran annonçait deux champs indistincts.
 *
 * Trouvé par la revue. Un test de source ne pouvait pas l'attraper : il
 * fallait rendre le formulaire avec plusieurs lignes.
 */
import { render } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

vi.mock('../../services/api', async (importOriginal) => ({
  ...(await importOriginal<object>()),
  listContacts: vi.fn().mockResolvedValue([]),
  getUserProfile: vi.fn().mockResolvedValue(null),
}));

import { InvoiceForm } from './InvoiceForm';

const FACTURE = {
  id: 'f1',
  number: 'F-001',
  type: 'invoice',
  status: 'draft',
  contact_id: null,
  issue_date: '2026-08-27',
  due_date: '2026-09-27',
  lines: [
    { description: 'Prestation A', quantity: 1, unit_price: 100, vat_rate: 20 },
    { description: 'Prestation B', quantity: 2, unit_price: 50, vat_rate: 20 },
  ],
} as never;

describe('Les identifiants d’une liste de lignes restent uniques', () => {
  it('aucun identifiant n’est porté deux fois', () => {
    const { container } = render(
      <InvoiceForm invoice={FACTURE} onClose={vi.fn()} onSave={vi.fn()} />,
    );

    const ids = [...container.querySelectorAll('[id]')].map((n) => n.id);
    const doublons = ids.filter((id, i) => ids.indexOf(id) !== i);

    expect(doublons, `identifiants dupliqués : ${[...new Set(doublons)].join(', ')}`).toEqual([]);
  });

  it('chaque label renvoie à un champ qui existe vraiment', () => {
    const { container } = render(
      <InvoiceForm invoice={FACTURE} onClose={vi.fn()} onSave={vi.fn()} />,
    );

    const orphelins = [...container.querySelectorAll('label[for]')]
      .map((l) => l.getAttribute('for')!)
      .filter((cible) => !container.querySelector(`[id="${CSS.escape(cible)}"]`));

    expect(orphelins, `labels sans champ : ${orphelins.join(', ')}`).toEqual([]);
  });
});
