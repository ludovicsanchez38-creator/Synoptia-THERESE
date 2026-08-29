#!/usr/bin/env node
/**
 * Génère l'index des noms de surfaces de THÉRÈSE.
 *
 * Demandé par Dr_logic-3D dans #discussion (29/08/2026) :
 *
 *   « on a besoin de s'y retrouver […] je ne peux pas deviner que "vue
 *     complète" pointe sur l'agenda […] en cas de bug, je ne sais pas à quoi
 *     m'attendre, ni comment y faire référence de manière explicite. »
 *
 * Katia avait produit un catalogue à la main. Il a vieilli en dix jours : le
 * chantier nommage a renommé des surfaces qu'il décrivait encore sous leur
 * ancien nom. D'où ce générateur - un index qu'un humain doit se souvenir de
 * mettre à jour est un mensonge en attente.
 *
 * Il LIT les tables du code, il ne les recopie pas. Renommer une surface
 * renomme sa ligne ici.
 *
 * Usage : node scripts/index-des-noms.mjs > docs/INDEX-DES-NOMS.md
 */
import { readFileSync, readdirSync } from 'node:fs';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const RACINE = join(dirname(fileURLToPath(import.meta.url)), '..');
const lire = (chemin) => readFileSync(join(RACINE, chemin), 'utf-8');

/** Extrait un objet littéral `NOM = { cle: 'valeur', … }` d'une source TS. */
function table(source, nom) {
  const i = source.indexOf(nom);
  if (i === -1) throw new Error(`table introuvable : ${nom}`);
  const bloc = source.slice(i, source.indexOf('};', i));
  return Object.fromEntries([...bloc.matchAll(/(\w+):\s*'([^']+)'/g)].map((m) => [m[1], m[2]]));
}

const etabli = lire('src/frontend/src/lib/etabli.ts');
const vues = lire('src/frontend/src/components/prototype/PrototypeUnifiedViewCanvas.tsx');
const centre = lire('src/frontend/src/components/prototype/CapabilityCenter.tsx');
const destinations = lire('src/frontend/src/lib/destinations.ts');

const titres = table(etabli, 'TITRES_ETABLI');
const libellesVues = table(vues, 'viewLabels');
const panneaux = table(destinations, 'NOMS_DES_PANNEAUX');
const verbes = Object.fromEntries(
  [...etabli.matchAll(/\{ id: '(\w+)', label: '([^']+)' \}/g)].map((m) => [m[1], m[2]]),
);
const groupes = Object.fromEntries(
  [...centre.matchAll(/id: '(\w+)',\s*\n\s*title: '([^']+)'/g)].map((m) => [m[1], m[2]]),
);
const capacites = [...centre.matchAll(/id: '([\w-]+)', group: '(\w+)', title: '([^']+)'/g)];

/**
 * Les ARÊTES : quel contrôle mène à quelle destination.
 *
 * Demandé par Dr_logic-3D le 29/08 : « à partir du moment où on nomme
 * distinctement chaque élément graphique du frontend, je peux faire une
 * représentation graphique des interactions, sous forme de graphe ».
 *
 * Il ne demande pas de la documentation : il demande la MATIÈRE pour en
 * produire lui-même. Les nœuds étaient déjà là ; voici les liens.
 *
 * Lues dans le code, pas recopiées : chaque carte déclare sa destination via
 * `<BoutonOuvrirLaVue vue="…">`, et le libellé du bouton dérive de la table
 * qui titre cette destination. Renommer une vue renomme le bouton ET cette
 * ligne.
 */
function aretes() {
  const dossier = join(RACINE, 'src/frontend/src/components/prototype');
  const liens = [];
  for (const fichier of readdirSync(dossier)) {
    if (!/\.tsx$/.test(fichier) || /\.test\./.test(fichier)) continue;
    const texte = readFileSync(join(dossier, fichier), 'utf-8');
    for (const m of texte.matchAll(/<BoutonOuvrirLaVue\s+vue="([\w-]+)"/g)) {
      liens.push({ depuis: fichier.replace(/\.tsx$/, ''), vers: m[1] });
    }
  }
  // Une carte peut porter plusieurs boutons vers la même vue : un seul lien.
  const vus = new Set();
  return liens.filter((l) => {
    const cle = `${l.depuis}->${l.vers}`;
    if (vus.has(cle)) return false;
    vus.add(cle);
    return true;
  });
}

const version = JSON.parse(lire('package.json')).version;

const nomsDeDestination = { ...libellesVues, ...panneaux };

const lignes = [];
lignes.push(`# Index des noms — THÉRÈSE ${version}`);
lignes.push('');
lignes.push('> **Généré depuis le code.** Ne pas modifier à la main : ce fichier est');
lignes.push('> réécrit par `node scripts/index-des-noms.mjs` à chaque version. Si un nom');
lignes.push('> change dans l\'application, il change ici.');
lignes.push('');
lignes.push('## Comment citer une surface dans un signalement');
lignes.push('');
lignes.push("L'identifiant d'un contrôle, c'est **le texte visible à l'écran**.");
lignes.push('');
lignes.push('- Si un contrôle n\'a pas de texte visible, c\'est un bug : signale-le.');
lignes.push('- Si deux contrôles portent le même texte au même moment, c\'est un bug aussi.');
lignes.push('- Pour distinguer la carte de la vue : « sur la carte Agenda » (dans la');
lignes.push('  conversation) et « dans la vue Agenda » (après avoir cliqué *Ouvrir Agenda*).');
lignes.push('');
lignes.push('## Les cinq verbes de l\'accueil');
lignes.push('');
lignes.push('| Verbe | Ouvre la surface |');
lignes.push('|---|---|');
for (const [id, verbe] of Object.entries(verbes)) {
  lignes.push(`| **${verbe}** | ${titres[id] ?? '—'} |`);
}
lignes.push('');
lignes.push('## Les vues complètes');
lignes.push('');
lignes.push('| Nom affiché | Identifiant interne |');
lignes.push('|---|---|');
for (const [id, nom] of Object.entries(libellesVues)) {
  lignes.push(`| **${nom}** | \`${id}\` |`);
}
for (const [id, nom] of Object.entries(panneaux)) {
  lignes.push(`| **${nom}** | \`${id}\` (panneau) |`);
}
lignes.push('');
lignes.push('## Le Centre de capacités');
lignes.push('');
lignes.push('Ce que l\'application appelle « aide » dans son rail est un **lanceur** : il');
lignes.push('ouvre les surfaces ci-dessus, il ne les documente pas.');
lignes.push('');
for (const [idGroupe, nomGroupe] of Object.entries(groupes)) {
  // c[1] = id, c[2] = groupe, c[3] = titre.
  const dedans = capacites.filter((c) => c[2] === idGroupe);
  if (!dedans.length) continue;
  lignes.push(`### ${nomGroupe}`);
  lignes.push('');
  lignes.push('| Capacité | Identifiant |');
  lignes.push('|---|---|');
  for (const c of dedans) lignes.push(`| ${c[3]} | \`${c[1]}\` |`);
  lignes.push('');
}

lignes.push('## Les liens entre surfaces');
lignes.push('');
lignes.push('Quelle carte de la conversation ouvre quelle vue complète. Le bouton');
lignes.push("porte toujours le nom de sa destination (« Ouvrir <nom> »).");
lignes.push('');
lignes.push('| Carte (dans la conversation) | Ouvre | Libellé du bouton |');
lignes.push('|---|---|---|');
for (const lien of aretes()) {
  const nom = nomsDeDestination[lien.vers] ?? lien.vers;
  lignes.push(`| \`${lien.depuis}\` | **${nom}** | Ouvrir ${nom} |`);
}
lignes.push('');
lignes.push('```mermaid');
lignes.push('graph LR');
for (const lien of aretes()) {
  const nom = nomsDeDestination[lien.vers] ?? lien.vers;
  lignes.push(`  ${lien.depuis} --> ${lien.vers}["${nom}"]`);
}
lignes.push('```');
lignes.push('');

process.stdout.write(lignes.join('\n') + '\n');
