# Marquage des contenus produits avec l’IA

Implémentation du lot confidentialité du 29 octobre 2026, livrée avec la 0.83.0. Ce document décrit les champs techniques ; il ne constitue pas une déclaration de conformité juridique.

## Champs

| Champ | Valeur |
|---|---|
| `ia_generee` | `oui` |
| `systeme` | `THÉRÈSE <version de l’application>` |
| `fournisseur_modele` | Identifiants du fournisseur et du modèle utilisés, séparés par `/` |
| `date` | Date de génération en ISO 8601, avec fuseau horaire |

Les champs ne contiennent ni prompt, ni contenu du document, ni nom de client, ni adresse mail, ni clé. Les identifiants de modèles personnalisés viennent du modèle choisi : évite d’y mettre des informations personnelles. Un export assemblant plusieurs générations liste les couples fournisseur/modèle, séparés par une virgule. Les anciennes productions ne sont pas réécrites rétroactivement.

## Emplacement et lecture

- **DOCX, XLSX et PPTX** : propriétés personnalisées `therese:ia_generee`, `therese:systeme`, `therese:fournisseur_modele` et `therese:date`, dans `docProps/custom.xml` du fichier ZIP Office. Les autres propriétés personnalisées sont conservées. Les relations et types de contenu OOXML sont ajoutés si nécessaire.
- **PDF** : entrée `/ThereseIA` du dictionnaire d’information, contenant les quatre champs en JSON ; flux XMP `/Metadata` du catalogue PDF. Les pages et leur contenu ne sont pas rédigés de nouveau.
- **Images PNG, JPEG et WebP sans marque IA d’origine** : bloc XMP, espace de noms `https://synoptia.fr/ns/therese/ia/1.0/`. Cette URI est un identifiant : l’application ne la consulte pas sur Internet. Insertion dans un chunk PNG `iTXt` (`XML:com.adobe.xmp`), un segment JPEG APP1 XMP ou un chunk WebP `XMP `. Les données de pixels compressées ne sont pas réencodées.
- **Mails et brouillons rédigés par l’IA** : en-tête MIME `X-Therese-IA`. Exemple : `genere; ia_generee=oui; systeme=THERESE/0.83.0; fournisseur_modele=openai/modele; date=2026-10-29T10:00:00+00:00`. Le système est écrit en ASCII dans cet en-tête. Le corps et la signature ne reçoivent aucune mention visible supplémentaire.

Le XMP ajoute également `Iptc4xmpExt:DigitalSourceType`, avec la valeur `http://cv.iptc.org/newscodes/digitalsourcetype/trainedAlgorithmicMedia`. Voir le [vocabulaire officiel IPTC](https://cv.iptc.org/newscodes/digitalsourcetype/trainedAlgorithmicMedia).

## Origine et conservation

Le moteur pose les propriétés après l’exécution du générateur de documents, y compris lorsque le modèle produit du code Python. La provenance vient du service ayant réalisé la génération. Les confirmations d’envoi de mail et de génération de document conservent cette provenance, même si le fournisseur choisi change avant la confirmation.

Les brouillons de réponse générés reçoivent un identifiant local de provenance. L’interface le conserve lors des retouches, de l’enregistrement et de la réouverture depuis les brouillons locaux ; le moteur vérifie son appartenance au compte avant de poser l’en-tête. Un mail écrit manuellement et une facture saisie au formulaire ne sont pas marqués. Les conversions de texte humain et les outils de simple correction de texte ne créent pas de marque de génération.

La table locale `ai_generations` conserve le fournisseur, le modèle, la date et la provenance des images, des brouillons de mail et des sections de l’Atelier. Ces données suivent l’export global et l’effacement des données métier. Elles permettent de retrouver le fournisseur des images après un redémarrage.

Les pieds déjà présents dans les documents produits deviennent « Rédigé avec l’IA de THÉRÈSE », conformément à la proposition de la note du 29 octobre. Aucun autre contenu visible n’est ajouté.

## Images déjà marquées et limites

Une image contenant un marqueur C2PA (`caBX`, `c2pa` ou `C2PA`) ou un type de source IA IPTC est conservée **octet pour octet**. Ce contrôle est conservateur : il ne vérifie ni la validité ni la signature du manifeste. Un faux marqueur peut donc empêcher l’ajout local. Les emplacements normatifs sont décrits par la [spécification C2PA](https://spec.c2pa.org/specifications/specifications/2.3/specs/C2PA_Specification.html). Le modèle et le fournisseur restent conservés dans la base locale même lorsque l’image originale n’est pas modifiée.

Le marquage local est non signé. Il ne constitue ni une authentification de l’auteur ni un filigrane résistant aux transformations. Un export par un autre logiciel, une capture, un copier-coller ou un transfert de mail peut supprimer les métadonnées. Aucun manifeste C2PA n’est fabriqué par THÉRÈSE. Les formats d’image autres que PNG, JPEG et WebP sont refusés si aucun marquage d’origine n’est reconnu.

Restent à faire valider hors du code : la portée juridique du marquage, les exceptions retenues, la formulation des conditions et la publication d’une page de détection. La présence de la présente documentation dans le dépôt n’est pas une publication de cette page.
