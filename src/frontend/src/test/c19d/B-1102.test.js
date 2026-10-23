import { expect, it } from 'vitest';
import { readFileSync } from 'node:fs';
// Le module CLI importe Playwright depuis la racine, où node_modules est
// absent. Exécuter sa fonction réelle, extraite sans charger sa CLI.
const source = readFileSync('../../tests/couverture/couverture-ecran.mjs', 'utf8');
const fonction = source.slice(source.indexOf('export async function lesInteractifs('), source.indexOf('export async function relocaliserInteractif(')).replace('export ', '');
const lesInteractifs = new Function('ROLES_INTERACTIFS', 'zoneGlobalePourNoeud', 'ATTRIBUTS_IDENTITE', `${fonction}; return lesInteractifs;`)(['button'], () => null, ['data-testid', 'data-id', 'id']);
const choix = source.slice(source.indexOf('export function choisirGestes('), source.indexOf('export function memoriserGesteExerce(')).replace('export ', '');
const choisirGestes = new Function('PLAFOND_GESTES_PAR_ECRAN', 'cleGesteGlobal', `${choix}; return choisirGestes;`)(Infinity, () => null);

function pageFactice(nom, html, snapshot) {
  const bouton = document.createElement('button');
  bouton.innerHTML = html;
  const locator = {
    isVisible: async () => true, isEnabled: async () => true,
    boundingBox: async () => ({ width: 50, height: 30 }),
    evaluate: async (fn) => fn(bouton),
    ariaSnapshot: async () => snapshot ?? `- button${nom ? ' ' + JSON.stringify(nom) : ''}`,
    getAttribute: async () => null,
  };
  return { locator: () => ({ count: async () => 0 }),
    getByRole: (role) => ({ count: async () => role === 'button' ? 1 : 0, nth: () => locator }) };
}
it.each([
  ['Fermer', '<img alt="Fermer">'], ['Supprimer', '<svg><title>Supprimer</title></svg>'], ['', ''],
])('B-1102 : le nom du snapshot est retenu (%s)', async (nom, html) => {
  const interactifs = await lesInteractifs(pageFactice(nom, html));
  expect(interactifs[0].nom).toBe(nom);
  expect(choisirGestes(interactifs, new Set())).toHaveLength(nom ? 1 : 0);
});

it.each(['Ouvrir Léa', 'Fermer « Projet »', 'Revenir à l’accueil', 'Sauver le devis', 'Lire une note', 'Copier un lien', 'Nom avec "guillemets"', 'Nom avec \\ barre', 'Accès à l’Agenda', 'Choix à deux lignes\nSuite'])('Rejeu B-1102 : %s', async (nom) => {
  const [controle] = await lesInteractifs(pageFactice(nom, '<img alt="Nom alternatif">'));
  expect(controle.nom).toBe(nom);
});


it.each([
  ['- button "Ouvrir"', 'Ouvrir'],
  [`- 'button "Supprimer : Facture"'`, 'Supprimer : Facture'],
  [`- 'button "Supprimer : Facture d''acompte"'`, "Supprimer : Facture d'acompte"],
  ['- ' + JSON.stringify('button "Lire : le devis"'), 'Lire : le devis'],
])('B-1102 : formes YAML simples et citées (%s)', async (snapshot, nom) => {
  expect((await lesInteractifs(pageFactice('', '', snapshot)))[0].nom).toBe(nom);
});
