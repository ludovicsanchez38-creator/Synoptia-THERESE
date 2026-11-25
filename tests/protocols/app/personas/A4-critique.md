# Protocole de test A4 · Nora, dirigeante de TPE

> Version 1.0 · THÉRÈSE 0.85.0 bêta · navigateur de bureau
>
> Banc isolé du cycle 5 · interface sur le port 1420 · moteur sur le port 17394.

## Profil

| Champ | Valeur |
|---|---|
| Nom | Nora Vidal, persona fictive |
| Métier | Dirigeante d’un atelier de signalétique de quatre personnes |
| Expérience | Utilise chaque jour une messagerie, un assistant IA payant et un logiciel de devis |
| Objectif | Préparer une relance, retrouver le contexte d’un client et produire un brouillon de devis |
| Matériel | Navigateur de bureau, fenêtre de 1280 × 840, français |
| Départ | Nouveau profil, stockage du navigateur purgé, moteur et dossier de travail jetables |

Nora découvre THÉRÈSE sans guide. Elle dispose de dix secondes pour lire
chaque écran et décider du prochain geste. Si elle ne sait plus où cliquer,
elle dit qu’elle partirait. Note le premier abandon et le geste qu’un
facilitateur doit donner pour poursuivre la visite. Ne présente pas cette
suite comme une navigation autonome.

Anthropic est préconfiguré dans le moteur par le lanceur du banc. Nora
doit quand même choisir le service et donner les consentements demandés.
Les montants et le client sont fictifs. Le courriel reste un texte à
copier et le devis reste un brouillon local.

## Parcours

### Étape 1 : Bienvenue

Ouvrir l’application et chercher à quoi elle sert.

**Résultat attendu** : Le premier bénéfice métier et la marche à suivre.

### Étape 2 : Profil

Renseigner Nora Vidal, Atelier Pivoine et dirigeante, si ces champs sont faciles à trouver.

**Résultat attendu** : Les champs indispensables et l’usage des informations.

### Étape 3 : Service d’IA

Choisir Claude Sonnet 5.5 dans le catalogue Anthropic et poursuivre.

**Résultat attendu** : Le lien entre son abonnement actuel, une clé API et le paiement à l’usage.

### Étape 4 : Confidentialité

Lire l’accord, décider puis continuer.

**Résultat attendu** : Ce qui sera envoyé et à qui.

### Étape 5 : Dossier et fin de mise en route

Continuer avec le dossier jetable proposé et ouvrir l’application.

**Résultat attendu** : L’endroit où seront stockés les fichiers du travail.

### Étape 6 : Premier échange

Demander une relance pour Atelier Azur, avec pose le 3 décembre et confirmation attendue le 30 novembre.

**Résultat attendu** : Le délai avant le premier texte et la possibilité de copier une réponse prête à relire.

### Étape 7 : Mémoire

Ouvrir la mémoire, chercher Atelier Azur et créer une fiche de démonstration si elle est absente.

**Résultat attendu** : Ce qui est mémorisé et ce qu’elle doit saisir elle-même.

### Étape 8 : Devis

Ouvrir la facturation et préparer un brouillon pour Atelier Azur, « Pose de signalétique », 480 EUR HT, quantité 1.

**Résultat attendu** : Le client, le montant et le statut du document avant toute émission.

### Étape 9 : Réglages

Revenir au service d’IA et retrouver la configuration active.

**Résultat attendu** : Le service et le modèle utilisés pour le prochain échange.

### Étape 10 : Coûts

Chercher combien a coûté l’essai et comparer avec l’écran du chat.

**Résultat attendu** : L’unité, la période et le lien entre activité et coût.

## Relevé

À chaque étape, noter le temps jusqu’au premier geste, l’écran, la
capture, le résultat métier et l’instant de la première hésitation.
Pour le chat, mesurer en plus le temps jusqu’au premier texte et
jusqu’à la fin du flux, lorsque ces événements surviennent.

Donner une note par écran sur cinq. **5** signifie que Nora agit seule
et comprend le résultat, **4** qu’elle agit seule après une hésitation,
**3** qu’elle agit avec un doute qui persiste, **2** qu’un indice extérieur
est nécessaire et **1** qu’elle abandonne ou ne peut pas avancer.

Écrire une phrase à la première personne par écran, telle que Nora la
dirait. Donner au plus une proposition concrète par écran. Classer chaque
remarque `bug_candidate`, `proposal` ou `observation` et joindre le geste
qui permet de la vérifier. Verser les propositions au registre pour
décision de Ludo.
