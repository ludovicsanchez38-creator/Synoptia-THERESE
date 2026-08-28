/**
 * Chantier A-texte (28/08) : l'écran ne doit plus affirmer ce que
 * l'application ne fait pas.
 *
 * Ces quatre assertions viennent de la campagne dix personas. Trois personas
 * sur dix sont partis sur ce motif, et pour deux d'entre eux (avocat, médecin)
 * c'était une ligne rouge professionnelle. La magistrate, elle, était venue
 * chercher exactement ces écarts : « toute phrase de l'interface qui affirme
 * plus que ce que l'application fait réellement ».
 *
 * On teste le TEXTE SOURCE, pas un rendu : ces phrases sont des données
 * (tables de conservation, infobulles), et c'est leur contenu qui ment.
 */
import { readFileSync } from 'node:fs';
import { join } from 'node:path';
import { describe, expect, it } from 'vitest';

const RACINE = join(__dirname, '..', '..', '..');

/**
 * Lit le source SANS ses commentaires.
 *
 * Nécessaire : le correctif laisse derrière lui un commentaire qui CITE la
 * phrase fautive pour expliquer pourquoi elle est partie. Un test qui cherche
 * dans le fichier brut la retrouverait là et resterait rouge à jamais — ou,
 * pire, deviendrait vert le jour où quelqu'un supprime le commentaire en
 * laissant la phrase. On teste ce que l'utilisateur peut lire à l'écran.
 */
function lire(chemin: string): string {
  return readFileSync(join(RACINE, 'src', chemin), 'utf-8')
    .replace(/\{\/\*[\s\S]*?\*\/\}/g, '')   // commentaires JSX
    .replace(/\/\*[\s\S]*?\*\//g, '')         // commentaires de bloc
    .replace(/^\s*\/\/.*$/gm, '');             // commentaires de ligne
}

describe('L’écran ne promet plus ce que l’application ne tient pas', () => {
  it('ne dit plus qu’aucune donnée n’est envoyée à un serveur externe', () => {
    const texte = lire('components/settings/PrivacyTab.tsx');

    // Faux : la recherche web part chez DuckDuckGo sans confirmation, la
    // vérification de mise à jour interroge synoptia.fr, et les modèles se
    // téléchargent depuis HuggingFace — y compris en modèle 100 % local.
    expect(texte).not.toContain("Aucune donnée n'est\n            envoyée à un serveur externe");
    expect(texte).not.toMatch(/Aucune donnée n'est\s+envoyée à un serveur externe/);
  });

  it('ne justifie plus la conservation illimitée par « pas de données personnelles tierces »', () => {
    const texte = lire('components/settings/PrivacyTab.tsx');

    // Le médecin a mis un nom de patiente dans le chat en trente secondes.
    expect(texte).not.toContain('Pas de données personnelles tierces');
  });

  it('ne dit plus que seules les métadonnées des fichiers sont conservées', () => {
    const texte = lire('components/settings/PrivacyTab.tsx');

    // Qdrant stocke le TEXTE extrait, découpé en fragments — pas une
    // métadonnée. Trouvé par la relecture de design, pas par la campagne.
    expect(texte).not.toContain('pas les fichiers eux-mêmes');
  });

  it('n’annonce plus un score « de 0 à 100 » que le calcul ne borne pas', () => {
    const texte = lire('components/crm/PipelineView.tsx');

    // scoring.py ne borne qu'en bas (`max(0, score)`) ; le maximum théorique
    // est 170, et 4 contacts sur 8 ont dépassé 100 pendant la campagne.
    // On corrige le LIBELLÉ, pas le calcul : borner écraserait la
    // comparabilité (relecture Grok + Soso, convergentes).
    expect(texte).not.toContain('de 0 à 100');
  });
});
