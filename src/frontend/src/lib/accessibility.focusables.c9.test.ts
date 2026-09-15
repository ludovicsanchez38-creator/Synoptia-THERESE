/**
 * B-800 (cycle 9) : un bouton en tabindex="-1" était compté parmi les focalisables.
 */
import { describe, expect, it } from 'vitest';
import { getFocusableElements } from './accessibility';

describe('getFocusableElements - B-800, tabindex=-1 exclu partout', () => {
  it('ignore les boutons, liens et champs retirés de l’ordre de tabulation', () => {
    const conteneur = document.createElement('div');
    conteneur.innerHTML = `
      <button id="ok">Valider</button>
      <button id="hors" tabindex="-1">Interne</button>
      <a id="lien" href="#" tabindex="-1">Lien</a>
      <input id="champ" tabindex="-1" />
      <div id="editable" contenteditable="true" tabindex="-1"></div>
      <span id="span" tabindex="0">Focalisable</span>`;
    const ids = getFocusableElements(conteneur).map((el) => el.id);
    expect(ids).toEqual(['ok', 'span']);
  });
});
