/**
 * Un bouton qui ouvre une vue la nomme, avec le nom que cette vue porte.
 *
 * Le gate ne compare pas deux littéraux : il REND le bouton pour chaque vue et
 * lit ce qui s'affiche. Si quelqu'un renomme une vue dans `viewLabels`, le
 * bouton suit tout seul — et si quelqu'un écrit un libellé à la main à côté,
 * le second test le refuse.
 */
import { render, screen } from '@testing-library/react';
import { readFileSync, readdirSync } from 'node:fs';
import { join } from 'node:path';
import { describe, expect, it, vi } from 'vitest';

import { BoutonOuvrirLaVue } from './BoutonOuvrirLaVue';
import { viewLabels } from './PrototypeUnifiedViewCanvas';

describe('Le bouton nomme sa destination', () => {
  it.each(Object.entries(viewLabels))('« %s » affiche « Ouvrir %s »', (vue, nom) => {
    render(<BoutonOuvrirLaVue vue={vue as never} onOuvrir={vi.fn()} />);
    expect(screen.getByRole('button', { name: `Ouvrir ${nom}` })).toHaveTextContent(
      `Ouvrir ${nom}`,
    );
  });

  it("aucune carte ne réinvente son propre libellé d'ouverture", () => {
    const dossier = join(__dirname);
    const interdits = [
      /Vue compl[eè]te/i,
      /Facturation compl[eè]te/i,
      /Voir tout mon agenda/i,
      /G[ée]rer mes contacts/i,
      /Email complet/i,
      /G[ée]rer mes devis/i,
    ];
    const fautes: string[] = [];
    for (const fichier of readdirSync(dossier)) {
      // Le composant lui-même DOCUMENTE les libellés qu'il remplace : sa
      // prose cite les motifs que ce gate traque.
      if (!/\.tsx$/.test(fichier) || /\.test\./.test(fichier)) continue;
      if (fichier === 'BoutonOuvrirLaVue.tsx') continue;
      const texte = readFileSync(join(dossier, fichier), 'utf-8')
        .replace(/\{\/\*[\s\S]*?\*\/\}/g, '')
        .replace(/\/\*[\s\S]*?\*\//g, '')
        .replace(/^\s*\/\/.*$/gm, '');
      for (const motif of interdits) {
        if (motif.test(texte)) fautes.push(`${fichier} : ${motif.source}`);
      }
    }
    expect(fautes).toEqual([]);
  });
});
