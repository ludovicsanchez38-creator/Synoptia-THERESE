# Story E1-01 : Initialiser le projet Tauri + React

## Description

En tant que **développeur**,
Je veux **avoir un projet Tauri + React fonctionnel**,
Afin de **pouvoir développer l'interface THÉRÈSE**.

## Contexte technique

- **Composants impactés** : Tauri shell, React frontend
- **Dépendances** : Aucune (story fondatrice)
- **Fichiers concernés** :
  - `src/frontend/` (nouveau)
  - `src-tauri/` (nouveau)
  - `package.json` (màj)
  - `Makefile` (màj)

## Critères d'acceptation

- [ ] `npm create tauri-app` exécuté avec template React + TypeScript
- [ ] Structure `src/frontend` et `src-tauri` créée
- [ ] `npm run tauri dev` ouvre une fenêtre avec "Hello THÉRÈSE"
- [ ] TailwindCSS 4 configuré et fonctionnel
- [ ] Zustand installé pour state management
- [ ] ESLint + Prettier configurés
- [ ] Hot reload fonctionne (modification React → refresh)

## Notes techniques

### Commandes d'initialisation

```bash
# Créer le projet Tauri
npm create tauri-app@latest -- --template react-ts

# Installer Tailwind
npm install -D tailwindcss@next @tailwindcss/vite

# Installer Zustand
npm install zustand

# Installer dev tools
npm install -D eslint prettier eslint-config-prettier
```

### Configuration Tauri

```json
// src-tauri/tauri.conf.json
{
  "productName": "THERESE",
  "version": "0.1.0",
  "identifier": "fr.synoptia.therese",
  "build": {
    "frontendDist": "../src/frontend/dist"
  },
  "app": {
    "windows": [{
      "title": "THÉRÈSE",
      "width": 1200,
      "height": 800,
      "minWidth": 800,
      "minHeight": 600
    }]
  }
}
```

### Structure cible

```
src/
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── stores/
│   │   ├── App.tsx
│   │   ├── main.tsx
│   │   └── index.css
│   ├── index.html
│   ├── package.json
│   ├── tailwind.config.ts
│   ├── tsconfig.json
│   └── vite.config.ts
└── src-tauri/
    ├── src/
    │   └── main.rs
    ├── Cargo.toml
    └── tauri.conf.json
```

## Estimation

- **Complexité** : M
- **Points** : 5

## Maquette

```
┌─────────────────────────────────────────────────────────┐
│  THÉRÈSE                                    [_] [□] [X] │
├─────────────────────────────────────────────────────────┤
│                                                         │
│                                                         │
│                    🤖 THÉRÈSE v2                        │
│                                                         │
│               Stack initialisée avec succès             │
│                                                         │
│           Tauri 2.0 ✅  React 19 ✅  Tailwind ✅         │
│                                                         │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

## Definition of Done

- [ ] Code pushé sur main
- [ ] `make dev` lance l'app
- [ ] Aucune erreur console
- [ ] README mis à jour avec instructions setup

---

*Sprint : 1*
*Assigné : Agent Dev*
