# Boucle bêta, cycle 4

THÉRÈSE 0.85.0 est préparée sur `beta/c4-20261125`, à partir de `d1f132e57`, retenue par Ludo le 25 novembre à 8 h 22. Le nom de diffusion choisi est `v0.85.0-beta`. La candidate locale et les preuves sont remises dans le bundle et le rendu du cycle.

## Décisions et contrôles

| Sujet | Changement et preuve |
|---|---|
| OpenAI | GPT-6.2 Sol prend la tête du catalogue moteur, du repli d’interface et de la liste OpenAI des agents. La permutation vérifie que le moteur et le Board prennent ce défaut. Le chat relit un modèle GPT-6 Sol déjà enregistré. Les témoins de routage, de plafond et d’échantillonnage passent sans appeler le fournisseur. [Fiche GPT-6.2 Sol](https://developers.openai.com/api/docs/models/gpt-6.2-sol) · [Guide OpenAI](https://developers.openai.com/api/docs/guides/latest-model#update-api-and-model-parameters) |
| Messagerie | La commande Joindre est masquée dans le composeur. L’envoi et le brouillon sont accessibles. Vitest, Playwright desktop et dix variantes de rédaction vérifient le parcours. |
| Facturation | Lors du choix du dossier de travail, un refus connu de lien physique dans la sonde déclenche un avertissement. Il propose un dossier dédié sur le disque interne. La sonde Linux a créé un lien sur ext4 et les refus ont été simulés. Les écrans de mise en route et de paramètres retirent l’alerte après le choix d’un dossier où la sonde ne rencontre plus ce refus. La publication des PDF sur volume incompatible reste au stade du design B-2062. [Design hérité](../plans/2026-11-25-b2062-design.md) |
| Invariants | La politique associe le support des versions bêta 0.x à leurs limitations. Deux contrôles Kimi éprouvent séparément le rejeu du raisonnement et le budget de sortie. Deux contrôles de l’API d’interface éprouvent la sélection de Synthetic et l’omission de l’effort. |
| Guide | L’aide affiche la source du guide des testeurs 0.85 avec quatre captures du cycle 2, dans l’application hors connexion. Les contrôles couvrent l’ouverture, les images, les liens et la prise en compte de la facturation et de la messagerie. Syn produit le PDF à la charte avant diffusion. [Source](../USER_GUIDE_ALPHA.md) |

Le premier passage complet OpenAI a révélé une réponse simulée vieillie du catalogue Board. La réponse fictive listait l’ancienne tête et la sonde déclarait la nouvelle absente. Sa donnée a été actualisée dans le même commit. Le premier passage, ses JUnit et le rejeu sont conservés sous `c4/`.

La première ronde du guide a signalé l’espace horizontal asymétrique dans une zone défilante et une attente toujours liée au bouton PDF sur l’accueil. Les deux contrôles passent après leur correction dans le commit du guide.

## Ronde, registre et plateau

Les rondes des lots A et B puis de la facturation sont vertes. La ronde consacrée au guide a relevé deux régressions, corrigées et rejouées en ciblé. Le rejeu a ensuite signalé le diagnostic TypeScript d’un paramètre de test. La fermeture de la session a laissé le passage et son verrou aller à leur terme. Sa correction est incluse dans `a822773d3`. La porte de release rejoue la suite complète et les vérifications de fabrication sur la tête finale. Le temps restant impose de mutualiser ces contrôles dans ce passage.

Le calcul après arbitrage donne **0/2**. Les trois décisions sont enregistrées. Les 13 sauts Pytest, les doubles lectures manquantes et les cinq instruments sans étalonnage formel empêchent la validation.

Le registre porte un design de reprise durable pour B-2034/P-172, une entrée sur le rétablissement ou la suppression d’un profil illisible, et une proposition de conservation locale du raisonnement DeepSeek pour une version suivante. Ludo accepte pour la bêta le repli DeepSeek du cycle 3.

Le travail a été mené en une seule session Astra, avec des lectures, reproductions et contre-essais consignés, sans compte fournisseur réel. Les tests Linux utilisent un profil jetable. Le lien de mise à jour des installations existantes est `/therese/alpha/latest.json`. Le contrôle de release sur la tête finale est archivé dans le rendu C4.

## Essais avant diffusion

- Construire Tauri et vérifier les signatures. Essayer les installations Windows et macOS, Seatbelt, et la mise à jour native de la 0.84 vers la 0.85.
- Choisir des dossiers réels compatibles et incompatibles sous Linux, macOS et Windows. Les erreurs de liens sur un volume amovible ou réseau ont été simulées sur le banc.
- Essayer Synthetic, DeepSeek au deuxième message avec outil, Perplexity et Infomaniak sur les comptes de Ludo.
- Mettre en page le PDF 0.85 à partir du guide source.
