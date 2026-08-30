# Les lots de correction confiés à Grok — 30/08/2026

> Ludo, le 30/08 au soir : « lance-le sur tous les correctifs, j'ai confiance,
> tu reliras ». Le stock des huit passes de revue fait environ 93 findings.
> Il est découpé en sept lots par FAMILLE de défaut, pas par fichier : un lot
> qu'on ne peut pas relire d'un bloc ne sert à rien.

**Règle de passage.** Un lot n'est lancé qu'après relecture du précédent :
diff lu en entier, cinq portes rejouées par moi, et sabotage de ses propres
tests. Sinon les erreurs se composent et on ne sait plus laquelle vient d'où.

| Lot | Famille | Origine | État |
|---|---|---|---|
| A | La chaîne de confiance : outils à confirmer, bac à sable, journaux | passe 4 | **en cours** |
| B | Les replis Office qui livrent un faux (XLSX vide, PPTX code et répétitions, DOCX, HTML) | main + passes 1 | à venir |
| C | Les états et compteurs qui mentent (« Envoyé », « Indexé », SLA, totaux) | passes 1 et 5 | à venir |
| D | La donnée dans la durée (prestations hors RGPD, facture sans copie client, id morts, export/import) | passe 2 | à venir |
| E | Le pluriel (deux comptes, deux agendas, deux devises, deux fournisseurs) | passe 6 | à venir |
| F | L'échelle (huit plafonds atteints en silence) | passe 8 | à venir |
| G | Concurrence et bords (upload non borné, sauvegardes homonymes, dates) | passe 3 | à venir |

**Hors lots, volontairement.** Le contenu tiers collé dans le prompt système
au même étage que la consigne (passe 4, finding 1). C'est un changement de
conception : il se discute avec Ludo avant de s'écrire, il ne se délègue pas.

## Soso

Hors jeu depuis le 30/08 au soir : deux ruptures de crédits, la seconde en
plein milieu de la passe 7 après 301 752 jetons. La passe « reprise et
annulation » reste donc **non couverte**.
