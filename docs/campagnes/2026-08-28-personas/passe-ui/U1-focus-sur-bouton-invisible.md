# U1 - Au clavier, le focus se pose sur un bouton « Supprimer » invisible

**Trouvé par la passe navigateur.** Aucun persona ne pouvait le voir : il faut
un vrai moteur de rendu pour lire une opacité calculée.

- **Gravité** : majeur (accessibilité), **pas** bloquant
- **Nature** : defaut_app
- **Source** : `components/invoices/InvoicesPanel.tsx` (~324), écran
  *Devis et factures*

## Mesuré dans le navigateur

Les actions de ligne (télécharger le PDF, supprimer) vivent dans un conteneur :

```
class="flex items-center gap-2 opacity-0 group-hover:opacity-100 transition-opacity"
```

Elles n'apparaissent qu'au **survol de la souris**. Or les boutons restent dans
le flux de tabulation. Focus posé au clavier sur le bouton de la ligne non
survolée :

```json
{
  "focusEstSurLeBouton": true,
  "labelFocalise": "Supprimer",
  "focusVisible": true,
  "opaciteDuConteneur": "0"
}
```

`:focus-visible` est actif — le navigateur veut afficher l'anneau de focus — et
**l'opacité du conteneur est 0**. L'anneau est donc invisible avec le bouton.

Il manque simplement `group-focus-within:opacity-100` à côté de
`group-hover:opacity-100`.

## Ce que ça donne pour un utilisateur au clavier

Il tabule dans la liste et arrive sur un contrôle qu'il ne voit pas. S'il
appuie sur Entrée, il déclenche **Supprimer**.

## La nuance qui empêche d'en faire un bloquant

Le clic n'efface rien : il ouvre une modale de confirmation
(`InvoicesPanel.tsx:361`, « La facture **FACT-2026-001** sera définitivement
supprimée »). L'utilisateur voit donc quelque chose avant que ça parte — une
modale qui, elle, est visible.

C'est un manquement de visibilité du focus (WCAG 2.4.7), pas une perte de
données silencieuse.

## Vérifié au passage : deux bons points

- L'onboarding est correctement piégé : `aria-modal="true"`, le focus cycle à
  l'intérieur (10 Tab consécutifs restent dans la modale), et Échap ne l'esquive
  pas — ce qui est le bon comportement pour une configuration initiale.
- Un lien « Aller au contenu principal » existe en tête de tabulation.

## Confirmé de visu : le finding F5 de l'artisan

La capture de l'écran *Devis et factures* montre `FACT-2026-002`, le statut, les
deux dates et le montant. **Aucun nom de client.** L'artisan disait : « je ne
retiens pas les numéros DEV-2026-001, je retiens Moreau ».
