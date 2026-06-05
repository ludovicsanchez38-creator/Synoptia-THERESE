# Arbitrage : garder la Mémoire (A) ou la dissoudre (B)

**Date** : 2026-06-05 · **Méthode** : workflow (cadrage + 2 experts + avocat du diable + arbitre, 5 agents). **Demandé par Ludo** : « fais trancher par un expert et avocat du diable ». **Statut** : décision, certitude forte.

## Question
- **A** — garder la « Mémoire » comme surface dédiée (vue plein écran, onglets Contacts + Fichiers), état actuel livré au Lot 6 et validé par Syn.
- **B** — dissoudre : fusionner Contacts dans le CRM (filtre Tout/Pipeline), sortir Fichiers en vue « Indexation », glance via la pastille.

## Tendance des experts → retournée par l'avocat du diable
Les 2 experts penchaient B (marque : B fort ; archi : hybride ≈ B en étapes). L'avocat du diable a **ouvert le code** et trouvé 3 faits porteurs qui cassent B :

1. **Filtres orthogonaux.** Le CRM filtre sur `!!c.source` (axe commercial). La Mémoire et la pastille filtrent sur `scope === 'conversation'` (axe contextuel). Un contact capté en conversation a un `scope` mais **pas forcément** de `source` → visible en Mémoire, **invisible en CRM**. « Fusionner Contacts → CRM » ne déplace pas une vue, il **supprime l'accès à une population entière** et **casse la cible de la pastille** (clic « N contacts liés » → CRM en montre zéro).
2. **RGPD orphelin.** ~102 lignes RGPD (export Art.20, anonymisation Art.17, consentement, expiration, cascade) vivent **uniquement** dans `MemoryPanel`, **zéro** dans `CRMPanel`. Sur un produit « RGPD-first, 100 % local », rendre la conformité sans-domicile = pire régression.
3. **Recherche perdue.** `searchContacts` (la preuve vivante « elle se souvient », moitié sémantique réparée `d1a4463`) est Memory-only ; le CRM n'a aucune barre de recherche.

**Angle mort commun des 2 experts** : « Contacts = CRM moins le filtre source ». Faux et inversé : la **Mémoire est le sur-ensemble**, le CRM le sous-ensemble (`source`). On ne loge pas un sur-ensemble dans un sous-ensemble sans perdre des éléments.

## Décision de l'arbitre (certitude forte)
**Garder A** (Mémoire-vue, déjà livrée + validée). **Prendre uniquement le morceau mûr de B** : sortir l'onglet **Fichiers** vers une **vue « Indexation » autonome** (FileBrowser = indexeur FS OS Tauri, `@tauri-apps/plugin-fs`, zéro lien `useContactsStore` → gain de cohérence, risque quasi nul). **Rejeter la fusion Contacts→CRM** telle que cadrée. Le cap « unifier Mémoire/CRM » reste valide mais doit s'exécuter dans l'**autre sens** : le CRM = une vue de la Mémoire, pas la Mémoire dissoute dans le CRM. À traiter dans une spec séparée qui aborde d'abord scope + RGPD + recherche.

## Plan retenu
1. Garder la Mémoire en l'état (ne rien démolir de Contacts / RGPD / recherche).
2. Extraire `FileBrowser` de l'onglet Fichiers → **vue `files` (Indexation)** dans le routeur, atteignable par ⌘K.
3. Retirer l'onglet `files` de `MemoryPanel` (type `Tab` : `'contacts' | 'files'` → `'contacts'`).
4. Ne pas toucher au CRM ni à la pastille (`setView('memory')` reste valide).
5. Reporter la fusion Contacts/CRM à une spec dédiée (scope + RGPD + recherche d'abord).
6. Tracer la dette réelle non réglée par A ni B : virtualisation liste contacts + `searchResults` non capé.

## Risques résiduels
- Différenciateur UX « Split View Contacts | Chat » : toute unification future devra être assumée explicitement (la présence vit dans les réponses RAG).
- Scalabilité (liste non virtualisée) : vrai mur, indépendant du contenant, à traiter à part.
- Round-trip `scope`/`scope_id` (Lot 9) historiquement fragile : tout futur toucher CRM/pastille doit embarquer son test de non-régression.
