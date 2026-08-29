# Campagne cinq personas — THÉRÈSE 0.55

> Briefs construits avec Grok le 29/08/2026, après les quatre lots du plan 0.55.
> Le protocole technique (harnais, interdictions) est celui du 28/08 :
> `docs/campagnes/2026-08-28-personas/protocole.md`, inchangé — il a bien tenu.

## Cadre commun (à coller au-dessus de chaque fiche)

**Quota.** 4 findings maximum. Un finding = un mécanisme, pas un écran. Au-delà, fusionne.

**Deux sections nouvelles, avant Findings :**

```
## Dette connue rencontrée
| Dette | Je l'ai vue | Une ligne de preuve |
| 501 à l'envoi de facture | oui/non | |
| TVA à 20 % par défaut | oui/non | |
| Notification après l'échéance | oui/non | |
| Pas de chemin pour un 2e calendrier | oui/non | |
| Cloison absente (recherche / fichiers / agenda / factures / mails) | oui/non | |
| Pas d'écran « cabinet » | oui/non | |

## Correctifs tenus (0.54 / 0.55)
Uniquement ce que TU as parcouru et qui a tenu. Une ligne par correctif. Ce n'est pas un finding.
```

**Tu n'as le droit de MESURER une dette connue que si c'est ton mandat.** Sinon : une case dans le tableau, zéro finding.

**Interdit de ficher :**
- « Je ne me reconnais pas dans l'accueil » / chantier métier (arbitrage de cap, pas un bug).
- Jargon déjà retiré (`canevas`, `profil émetteur`, `référentiel de contacts`).
- Confirmation générale, Centre de confiance, interrupteur web, crash de la recherche approfondie, addition des devises, nom et adresse client, bouton `Fermer` : **seulement si ça ment encore**.
- Lenteur, bavardage, hallucination de `qwen3:8b` → `limite_modele_local`, jamais `defaut_app`.
- Dictée / voix locale, extra manquant, 401, serveur mort → préfixe `HARNAIS ?` dans le titre, tu t'arrêtes, tu ne répares pas.

**Abandon.** Une seule ligne rouge. Pas une liste d'agacements.

**Source obligatoire.** API ou interface (`fichier:ligne`) ou les deux. Libellé exact. Sans source, le finding est void.

---

## Pourquoi ces cinq (et pas un bis des dix)

| # | Persona | Ce que les dix n'ont pas pu voir |
|---|---|---|
| 1 | Karim | La 0.55 **en usage** (CHF, arrondi, plus d'Accepté, Facturer absent puis présent, `Ouvrir <destination>`). Roux n'a facturé qu'en euros, sur un établi qui proposait déjà Facturer. |
| 2 | Inès | La cloison **sur les cinq domaines encore ouverts**, en un seul constat. L'avocat n'a vu que fichiers + fiches. Le formateur était en conversation libre, donc hors cloison. |
| 3 | Aude | Un chemin **sans propriétaire** (dossier, fichier par son nom, document). Méthode ci-dessous, pas une chasse libre. |
| 4 | Thomas | Les trois dettes restantes **comme un vrai travail du matin**, pas comme une checklist. Roux a su mettre 10 % ; personne n'a mesuré celui qui valide le défaut sans le lire. Personne n'a cherché le 2e calendrier. |
| 5 | Léa | Un livrable Office (xlsx/docx) **à rattacher demain matin**. Les dix n'ont jamais eu ça pour métier ; les bugs de fichiers de skill n'ont été vus que par des tests, pas par une personne pressée. |

**Comment Aude trouve de l'unlisté sans hasard.** Les défauts non listés de la 0.53 étaient tous de la même famille : un nom visible qui promet un geste. Les dix personas occupaient chacun une carte de l'accueil. Aude a un travail qui ne tient sur aucune carte, donc elle traverse trois surfaces qui n'ont pas eu de propriétaire (rattacher un dossier, chercher un fichier par son nom, produire un document). Consigne : chaque nom lu est un contrat, elle va au bout. Les X qu'on n'a pas encore lus, elle les rencontrera parce que le chemin les traverse, pas parce qu'elle fouille.

---

