# Préparation v0.48.1-alpha - « un panneau côte à côte n'est pas une modale »

> Branche `fix/0.48.1-panneaux-non-modaux`, 11 commits. **Prête, attend le GO
> de Ludo.** Point de départ : une capture d'écran de Ludo le 25/08 au soir -
> « quand une application est ouverte en onglet latéral, la fenêtre principale
> n'est plus réactive ni navigable ».

## Le bug signalé

Reproduit avant toute correction : à l'ouverture du canevas de contexte, la
colonne principale (le `<section>` de la conversation et ses 10 boutons)
recevait l'attribut `inert` - zéro clic, zéro scroll, zéro focus, alors
qu'elle reste visible à côté. Cause : `useDialogFocusTrap` posait
`isolateBackground` sur des panneaux qui ne couvrent l'écran qu'en petit
format. **Mécanisme préexistant** (commit `9f7bbebc`, 16/07, vague
accessibilité 0.40) - pas une régression de la 0.48.

## Ce que le correctif pose

- **`usePanneauCouvrant`** : l'isolation ne vaut que sous le seuil `xl`
  (1280 px, celui qu'utilisent déjà les classes des panneaux).
- **Aucun panneau ne se déclare modal** : le rail et l'en-tête restent
  volontairement actifs (`data-dialog-allow`), donc un panneau isole ce qu'il
  RECOUVRE, rien de plus - et ne pilote jamais le clavier.
- **Voile grisé** (exigence de Ludo) quand l'isolation s'applique : un fond
  mort sans signe se lit comme une application figée. Non cliquable (BUG-156).
- **Les six panneaux passent côte à côte au seuil xl** : plus aucun contrôle
  atteignable au clavier sous une surface opaque.
- **`useDialogFocusTrap` en quatre effets ordonnés** : capture du déclencheur
  puis focus initial / isolation (+ transfert de focus si la zone active vient
  d'être isolée) / restauration / clavier. L'ordre de déclaration est le
  contrat : React nettoie dans cet ordre, donc `inert` est retiré avant que le
  focus revienne au déclencheur.
- **Isolation fondée sur le z-order RÉEL** (z-index effectif d'un élément
  positionné, puis ordre du DOM) : ce qui est visuellement au-dessus n'est
  jamais isolé, ce qui est derrière l'est toujours.

## Ce que la revue a trouvé en plus (contrôle post-release 0.48.0)

- Un conseiller du Board qui terminait **sans rien dire** passait pour un avis
  valide, synthétisé et sauvegardé (`contenu_exploitable`).
- Un échec d'écriture du suivi faisait **perdre le message métier**
  (`_terminer_sans_masquer` : le suivi est un témoin, pas un acteur).
- Gemini : 5xx non compté au circuit breaker, 401/403/404 confondus,
  message brut du fournisseur à l'écran.
- **Les coûts affichés en euros étaient des dollars** (~9 % d'écart) :
  `formaterCout`/`UNITE_COUT`, contrat `/prices`, alertes du tracker.
- **Fuite de données** : OpenRouter et Ollama recopiaient le corps des
  réponses - un chemin local et un fragment de clé pouvaient s'afficher
  (5 sites fermés à la source).
- Le Board et l'Atelier **écrasaient les messages actionnables** des
  providers par des génériques.

## Revue - 8 passes, 29 défauts fermés (28 findings Soso + 1 auto-contrôle)

| Passe | Verdict | Findings | Nature |
|---|---|---|---|
| 1 | NO-GO | 7 | rail cliquable derrière une « modale », 3 panneaux recouvrants, Échap volé + les 4 findings du contrôle 0.48 |
| 2 | NO-GO | 6 | clavier encore piégé, avis « ... » accepté, clé Gemini non actionnable, devises à moitié migrées |
| 3 | NO-GO | 3 | **régression** : le resize volait le focus ; budget réinterprété ; 404 muet |
| 4 | NO-GO | 4 | **2 régressions** : focus laissé en zone inerte, restauration des modales cassée |
| 5 | NO-GO | 3 | **régression** : un panneau isolait une modale ouverte par-dessus |
| 6 | NO-GO | 3 | **régression** : l'exclusion ignorait l'ordre ; messages actionnables écrasés |
| 7 | NO-GO | 2 | **2 erreurs de raisonnement** : « ouverture = z-order » faux ; « contenu provider sûr » faux (fuite réelle) |
| 8 | **sans verdict** - crédits Codex épuisés | - | pistes reprises en auto-contrôle (1 défaut trouvé : z-index sur élément non positionné) |

Le motif « chaque remédiation cache sa régression » s'est confirmé **cinq
fois** sur ce seul hotfix. Les deux findings de la passe 7 étaient des
affirmations FAUSSES de ma part, prises pour des garanties.

## Gates au dernier commit

| Gate | Résultat |
|---|---|
| pytest (hors e2e) | 2261 verts, 0 échec |
| vitest | 890 verts |
| mypy fresh | 1001 (main 1002, baseline CI 1004) |
| ruff / tsc / eslint | propres (eslint 27/27) |

## Recommandation

**Releaser.** Le code de cette branche est strictement meilleur que ce qui
tourne chez les testeurs : il corrige un blocage d'usage quotidien, une fuite
de données, un affichage de coût faux et trois défauts du Board. Les passes
successives portaient sur des cas de plus en plus rares, mais la 7e a encore
trouvé du sérieux - une passe de contrôle post-release reste donc justifiée
dès que les crédits Codex reviennent, comme pour la 0.48.0.

## Dette actée
- Renommage `cost_eur` / `monthly_budget_eur` / `estimated_cost_eur` en USD
  côté API et base (les surfaces d'écran sont correctes ; les noms de champs
  restent historiques).
- Valeur du budget mensuel non convertie : elle est simplement dite en dollars
  sous le réglage (aucun taux de change inventé - décision de Ludo attendue
  s'il préfère un affichage en euros).
- Passe Soso de contrôle post-release (0.48.0 ET 0.48.1) à la recharge.
