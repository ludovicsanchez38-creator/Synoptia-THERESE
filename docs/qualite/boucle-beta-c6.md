# Boucle bêta, cycle 6

THÉRÈSE 0.85.0 est préparée sur `beta/c6-20261125` à partir de
`0ddefd1a3`. Le nom public choisi par Ludo reste `v0.85.0-beta`.

## Changements vérifiés

| Proposition | Comportement | Commit |
|---|---|---|
| P-003 | Le service et le modèle configurés se lisent avant la procédure repliée. | `fd8ba4a35` |
| P-005 | Continuer sans dossier est l’unique action de poursuite sans dossier choisi. | `79b5ceab3` |
| P-006 | L’accueil propose de préparer une relance de devis. | `8e42d4327` |
| P-007 | L’import de profil est visible sous un choix secondaire, replié au départ. | `64bd4d0ee` |
| P-009 | Le filtre de la Mémoire explique dans quelles conversations les fiches sont disponibles. | `e5f71e271` |
| P-004 | Les réglages standard donnent le coût estimé en dollars et le détail du jour et du mois. | `a9abef814` |
| P-008 | L’écran d’accord Claude donne l’exemple du premier « Bonjour » vérifié auprès d’Anthropic. | `15c2f14cc` |
| P-010 | Le bouton PDF du brouillon porte les mentions émetteur ou destinataire manquantes dans sa description accessible. | `ea1beb6f4` |

Chaque correctif a un test rouge, un passage vert et une vérification par
retrait temporaire du correctif. Pour l’exemple Claude, le premier « Bonjour »
a été joué avant et après sur deux profils vierges. La requête relevée
contient le message, deux blocs d’instructions et de contexte, la
description des outils et les paramètres du modèle et du flux. Elle arrive
avant tout résultat d’outil. L’accord et son mécanisme sont conservés.

## Recette par persona

| Persona | Conforme | Écart de l’application | Écart du protocole | Non jouable sur le banc | Non tentée |
|---|---:|---:|---:|---:|---:|
| Sophie | 31 | 0 | 16 | 1 | 0 |
| Marc | 29 | 0 | 15 | 1 | 0 |
| Léa | 27 | 1 | 27 | 5 | 0 |
| Nora | 9 | 1 | 0 | 0 | 0 |

Les matrices du rendu de cycle donnent une capture et un constat à chacune
des 163 étapes. Les trois protocoles historiques ont été alignés sur les
gestes observés, avec les préconditions des parcours natifs.

- Chez Marc, le devis à 2 880 € TTC a été converti en facture brouillon.
  Le PDF a été produit. Le contrôle de panne du Pipeline affiche une erreur
  et retrouve la fiche lorsque le transport revient.
- Chez Léa, la facture FACT-2026-001 à 996 € TTC passe en Envoyée sans
  expédition de message. Le test de réseau et celui de clé refusée
  reproduisent l’erreur avec un transport simulé. Le brief signale
  l’échec total ou partiel et l’agenda conserve les rendez-vous lus.
  Les deux fichiers Office se génèrent après confirmation et leurs
  contenus sont vérifiés. L’enregistrement par le bouton passe par Tauri.
  L’étape d’exploitation d’une injection est exclue par la consigne.
- Nora parcourt les dix écrans sans aide. Elle s’arrêtait au troisième
  écran au cycle 5. Le modèle ajoute encore une phrase qui engage à
  proposer un autre créneau, alors que la consigne demandait seulement
  de recueillir la confirmation. Le cas B-044 reste à reproduire hors
  modèle avant une correction.
- B-042 concerne le lien vers Mémoire avec l’ouverture directe du chat
  activée. Le défaut a été reproduit hors modèle quand le montage de la
  vue se rejoue. Dix vues passent, et le rejeu navigateur ouvre Mémoire.
  B-043 corrige le chemin de réglages indiqué par le refus du Board.
  B-045 aligne l’aide sur l’effort avec les modèles proposés au catalogue.

## Mesures Anthropic

| Contrôle | Jetons relus | Coût THÉRÈSE (USD) | Usage reconstitué (USD) |
|---|---:|---:|---:|
| Sonnet 5.5, trois échanges | 25 572 | 0,030220 | 0,030220 |
| Fable 5.2, trois échanges | 17 646 | 0,199647 | 0,199647 |
| Board, avis puis synthèse | 0 | 0,187912 | 0,187912 |

La dépense totale estimée d’après les trames reçues est de 1,224639 $.
Le compteur THÉRÈSE cumule 1,183071 $. Le relevé des flux interrompus
reste partiel.

Les deux vérifications du cache incluent les appels d’extraction
automatique dont l’usage est arrivé. Le prix de lecture représente 5 %
de l’entrée ordinaire sur Sonnet 5.5 et 2,5 % sur Fable 5.2. Les écritures
coûtent 1,25 fois l’entrée pour cinq minutes et deux fois pour une heure.
[Tarifs Anthropic](https://platform.claude.com/docs/en/about-claude/pricing)

Le Board à cinq signale OpenAI indisponible et ne démarre aucun appel.
Le comportement date du retrait des replis automatiques pour protéger
la confidentialité. L’essai à un conseiller, lancé par l’API du banc,
produit l’avis d’Opus 5.5 et la synthèse de Sonnet 5.5. L’historique
les affiche. La provision de 3,06 $ a été évaluée avant le lancement.

L’arrêt manuel du premier échange laisse le compteur à 0,0000 $.
La trame de début donne 2 996 jetons d’entrée, 7 926 écrits en cache
cinq minutes et deux jetons de sortie. L’usage de départ vaut 0,025827 $
au tarif public. Le flux s’interrompt avant la trame d’usage finale.
Le montant facturé par le compte reste indéterminé.

## Diffusion

Le [guide des testeurs de novembre 2026](../USER_GUIDE_ALPHA.md) reste
dans l’aide. Le brouillon décrit l’ouverture sur macOS et le coût estimé.
La diffusion de la bêta se fait pendant l’attente de la signature Apple,
conformément à la décision de Ludo. Restent les essais d’installation
et de mise à jour natives, le trousseau, l’enregistrement Office,
les volumes pour les PDF et les essais des connecteurs avec les comptes
de Ludo. Le PDF de diffusion se prépare à partir de la source actualisée.
Les résumés exacts des portes accompagnent le bundle local dans le rendu.
