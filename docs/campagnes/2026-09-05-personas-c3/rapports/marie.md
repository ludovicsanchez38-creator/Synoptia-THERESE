# Marie Exemple, artisane décoratrice (Atelier Exemple) : trace de la campagne

> THÉRÈSE 0.66.1, frontend Vite réel, backend jetable 17393, profil de démonstration.
> Thème clair, 1280×800, DPR 1, locale fr-FR, souris. Session du 05/09/2026.

## Mon impression

_(rédigée en fin de session, voir plus bas)_

## Parcours

### Accueil : comprendre ce qui m'attend et ouvrir un point d'attention

| Étape | Geste | Attendu | Observé | Capture | Classement |
|---|---|---|---|---|---|
| 1 | Arriver sur l'accueil (après purge du stockage et rechargement) | Un brief lisible, mes quatre points d'attention, les parcours proposés | « Bonjour Marie. » + carte « Ton attention aujourd'hui, 4 éléments issus de tes données » ; les quatre éléments sont bien les miens (facture Claire Roux en retard, relance Paul Durand, FACT-2026-002 à relancer, séance 2 Garage Benali). En revanche la rangée « Sources réelles » est à moitié recouverte par le composeur, et les cinq parcours (Écrire/Retrouver/Préparer/Facturer/Décider) sont entièrement cachés dessous : je ne sais pas qu'ils existent. | `01-accueil-arrivee.png` | bug_candidate (marie-01) |
| 2 | Ouvrir le tiroir « Conversations » | La liste de mes conversations | Une seule conversation, « Quelles sont mes tâches urgentes… », identique à `GET /api/chat/conversations` (contrôle d'environnement OK). Le focus part sur le champ de recherche. | `02-accueil-tiroir-conversations.png` | observation |
| 3 | Échap | Le tiroir se ferme, je reviens d'où je viens | Le tiroir se ferme et le focus revient sur le bouton « Conversations » du rail. Comportement juste. | `03-accueil-echap-tiroir-conversations.png` | observation |
| 4 | Basculer le variateur sur « le minimum » | Moins d'éléments, et savoir ce qui est masqué | Deux éléments + « Voir les 2 autres éléments, dont 1 en retard ». Rien n'est caché en douce, j'aime bien. Mais l'étiquette du variateur et les échéances sont en 12 px. | `04-accueil-brief-le-minimum.png` | observation |
| 5 | Faire défiler jusqu'en bas | Voir la fin de la page | Les cinq parcours apparaissent enfin, au-dessus du composeur. Ils existaient donc, mais rien ne me le disait à l'arrivée. | `05-accueil-defilement-bas-etabli-masque.png` | bug_candidate (marie-01) |
| 6 | Revenir sur « l'essentiel » | Les quatre éléments | Les quatre éléments reviennent immédiatement. | `06-accueil-brief-essentiel-4-elements.png` | observation |
| 7 | Cliquer « Claire Roux · FACT-2026-002 · À relancer · 1 440,00 € » | Ouvrir CETTE facture | Ouvre la liste complète « Devis et factures » (10 documents), pas la facture. FACT-2026-002 n'est même pas dans le premier écran : je dois la chercher. | `07-accueil-ouvrir-point-attention-facture.png` | bug_candidate (marie-02) |
| 8 | Échap depuis « Devis et factures » | Retour à l'accueil | Retour à « Bonjour Marie. ». Le focus retombe sur la racine du document, pas sur l'élément que j'avais cliqué. | `08-accueil-echap-retour-depuis-factures.png` | observation |

Arbre d'accessibilité : à l'ouverture du tiroir, focus sur « Rechercher une conversation », région nommée « Conversations » ; sur l'écran Devis et factures, focus sur le titre `heading "Devis et factures"`, mais **les dix cartes de documents sont des `generic [cursor=pointer]` sans rôle ni nom** : rien n'est atteignable au clavier dans la liste.

