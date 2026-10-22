// Recette de l'écran réel sur des objets fictifs, par interception intégrale.
// À lancer avec scripts/recette_r5_hors_reseau.py : aucun serveur ni connexion.
import { build } from 'vite';
import { mkdirSync, copyFileSync } from 'node:fs';
import react from '@vitejs/plugin-react';
import tailwindcss from '@tailwindcss/vite';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../../..');
const fixture = path.join(root, '.recette-r5/ui');
mkdirSync(fixture, { recursive: true });
for (const nom of ['entry.tsx', 'index.html', 'style.css']) copyFileSync(path.join(root, 'src/frontend/scripts-recette/r5-memoire-fixture', nom), path.join(fixture, nom));
const dist = path.join(root, '.recette-r5/ui-dist');
await build({ configFile: false, root: fixture, envDir: fixture,
  plugins: [react(), tailwindcss()], resolve: { dedupe: ['react', 'react-dom'], alias: {
    react: path.join(root, 'src/frontend/node_modules/react'),
    'react-dom': path.join(root, 'src/frontend/node_modules/react-dom'),
  } }, build: { outDir: dist, emptyOutDir: false, chunkSizeWarningLimit: 2000 } });
