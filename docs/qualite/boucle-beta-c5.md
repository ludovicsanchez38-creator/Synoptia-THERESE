# Boucle bêta, cycle 5

THÉRÈSE 0.85.0 est préparée sur `beta/c5-20261125`, à partir de
`25705d22c` (cycle 4). Les quatre personas ont utilisé la candidate dans
Chrome avec un moteur isolé et des données fictives. La version destinée
à la diffusion porte le nom `v0.85.0-beta`, choisi par Ludo.

## Campagne Anthropic

| Parcours | Étapes tentées | Principale preuve |
|---|---:|---|
| Sophie | 42/48 | Le modèle termine une réponse avec la fiche du contact et l’absence de devis, après deux appels d’outil. |
| Marc | 40/45 | Trois tours d’outil lisent le contact, retrouvent le devis local et traitent la recherche de fichier vide. |
| Léa | 51/60 | Le flux arrêté est repris dans la même conversation. L’effort Bas arrive comme `low`. Le nom du profil et le contact sont repris. L’injection est hors périmètre. |
| Nora | 10/10 | Abandon au service d’IA, puis reprise facilitée. Un brouillon à 480 € HT est créé. Les coûts se trouvent derrière le Mode Contributeur. |

Les étapes tentées incluent des gestes qui n’ont pas abouti. La matrice
détaillée et les captures distinguent les observations des écarts de
recette. Les 13 modèles du menu, Haiku 5.5 compris, répondent en HTTP 200
et appellent l’outil de recherche de factures. Sur cette sonde vide,
THÉRÈSE répond avec un état déterministe. Les reprises de modèle ont
été observées chez Sophie, Marc et Léa. L’essai Board à un conseiller
atteint Opus 5.5, puis le banc interrompt son attente à 110 secondes
avant l’avis complet. L’avis et la synthèse restent à valider
sur ce flux.

Les trames Messages distinguent jetons nouveaux, écritures et lectures
de cache. THÉRÈSE envoie des marqueurs sur le début stable du système
et en fin de catalogue d’outils. La part lue est de 66,9 % chez Sophie,
66,8 % chez Marc et 67,3 % chez Léa. Les montants sont estimés d’après
les tarifs publics et les champs d’usage des trames reçues. Les flux
interrompus gardent une dépense résiduelle inconnue.
[Tarifs Anthropic](https://platform.claude.com/docs/en/about-claude/pricing)

## Réparations

- **bc5-B-040**. Le traceur tarife la lecture et les deux durées d’écriture
  du cache Anthropic par appel. Il garde le total de jetons transmis
  pour l’affichage et le palier. Trois tests HTTP simulés couvrent le
  chat direct, le flux et la reprise d’outil.
- **bc5-B-041**. Le compteur inclut l’usage effectivement reçu de
  l’extraction automatique du chat, même sans entité retenue. Deux cas
  simulent le deuxième appel observé sur le banc. Les
  consentements et le service de conversation sont conservés.

Pour les deux sujets, les tests ont échoué d’abord sur l’écart mesuré,
puis sont passés après correction. Dix variantes supplémentaires par
sujet ont passé. Le retrait ciblé de chaque correctif a refait rougir ses
tests. Le protocole A4 porte son propre commit. Huit propositions A4
attendent la décision de Ludo.

Après correction, le second contrôle Sonnet 5.5 a produit la même
réponse. La bulle affiche 0,0264 $ pour le dialogue. Extraction
incluse, le compteur affiche 0,029604 $, le montant reconstitué à
partir des deux trames de l’API.

La première ronde a fait apparaître un espion de coût dépendant de l’ordre
d’exécution, une collision de nom avec la garde de devise et l’absence de
l’A4 dans l’index des protocoles. Les tests utilisent leur propre traceur,
la constante a été renommée et l’index compte les dix étapes de l’A4.

## Diffusion

Rejouer un Board complet sur des comptes autorisés, puis terminer les
essais natifs Tauri, Windows, macOS Seatbelt, signatures et mise à jour
0.84 vers 0.85. Produire le PDF du guide et essayer Synthetic, DeepSeek
avec outils, Perplexity et Infomaniak. Le rendu du cycle conserve les
résultats des portes locales, les limites de couverture et les preuves.
