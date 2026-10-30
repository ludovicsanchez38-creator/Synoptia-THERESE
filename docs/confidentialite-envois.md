# Confidentialité des envois IA

## Tentatives et reprises

Le moteur utilise deux SDK de fournisseurs IA : `openai.OpenAI` et
`google.genai.Client`, dans `services/image_generator.py`. Ils reçoivent un
client HTTP dont le transport relit l'accord images avant chaque requête,
y compris une reprise interne après 429. Le transport sous cette garde ne
réessaie pas de lui-même. Un refus est présenté en français à l'utilisateur.

Les adaptateurs LLM (Anthropic, OpenAI et compatibles, Gemini, Mistral,
DeepSeek, OpenRouter, Perplexity, Infomaniak et Ollama) utilisent HTTPX
directement, sans SDK fournisseur. Le service commun relit les accords LLM,
documents et fiches avant ses appels et continuations ; la garde accompagne
le client de chaque appel. La garde désactive le suivi automatique des
redirections pour `stream`, `post` et `get`, même si le client partagé l'active.
Toute réponse HTTP 3xx est refusée avec un message français, sans nouvel envoi,
y compris vers le même hôte. Une redirection n'est donc pas une destination
implicitement autorisée. Fal, les téléchargements d'images et la dictée Groq
utilisent aussi cette garde HTTPX.
Les SDK Qdrant et les bibliothèques de modèles locaux ne sont pas des clients
de génération chez un fournisseur IA externe. Les connecteurs métier, la
recherche web et les téléchargements de modèles restent des circuits distincts.

Un retrait ne rappelle pas les octets déjà remis au transport. Aucun appel
réel de fournisseur n'est nécessaire aux tests : les SDK sont réels, leur
transport réseau est remplacé par un transport en mémoire.

## Historique

`messages.extra_data.provenance_documents` conserve `documents`,
`sans_document` ou `inconnue`. Les pièces jointes et tout contexte documentaire
marquent aussi les réponses qui en découlent, sans tenter de reconnaître une
citation par sa syntaxe. Les continuations, reprises de messages enregistrés, réponses partielles et
erreurs conservent cette précaution. La métadonnée locale n'est pas envoyée au modèle.

Les messages antérieurs sont repris lors de leur relecture : sources,
citations, pièces jointes ou traces mémoire conservées valent provenance
documentaire par prudence. Sans trace exploitable, la provenance est inconnue.
La reprise est enregistrée dans le même champ JSON, sans changement de schéma.
Un contenu mal formé ne devient jamais une preuve d'absence de document.

Sans accord documents pour la destination effective, les messages documentaires
ou inconnus sont retirés du contexte transmis. Ils restent visibles dans
l'historique local. Les anciennes pièces jointes sont également exclues du
rappel automatique, avant la lecture de leur contenu. La nouvelle question
continue avec le contexte autorisé, dans les deux modes, avec ou sans flux.
La réponse commence par une phrase au tutoiement expliquant ce retrait.
Un fichier nouvellement joint ou explicitement demandé par `/fichier` ou
`/analyse` exige toujours l'accord documents ; l'ancien historique seul ne
déclenche plus cette demande dans le composeur.
Un accord retiré après cette préparation est encore contrôlé avant
l'envoi ; les messages retenus conservent leur finalité documentaire.

## Confirmations et autres copies différées

Les cartes gardent une copie indépendante de leurs arguments et de leur
provenance. Les instantanés textuels de recherche web conservent la provenance
de chaque message, même lorsqu'une image est retirée de la copie. Une ancienne
copie sans booléen fiable reste documentaire par prudence.

À la confirmation, l'historique copié est filtré pour le fournisseur effectif
avant la rédaction. Les arguments générés par un modèle qui a vu des documents
peuvent eux-mêmes en reprendre le contenu : ils ne peuvent pas être nettoyés
avec certitude. Si leur accord documents manque, la carte de recherche est
refusée avant la recherche et la rédaction, avec un message au tutoiement.
Une nouvelle demande sans document permet de poursuivre. Confirmer la carte
ne crée aucun accord, y compris après un changement de fournisseur.

La rédaction conserve la provenance dans sa réponse enregistrée. La garde
finale lit aussi les marques portées par les messages et les copies conservées
pour la relecture mémoire ; elle ne dépend pas du seul drapeau du contexte.
L'extraction automatique différée relit la provenance en base et la transmet
à sa garde IA. Une trace absente y reste documentaire par prudence.

Les autres cartes d'outils conservent aussi la provenance de leurs arguments.
Leurs effets locaux ou leurs envois vers les connecteurs métier restent soumis
à leur confirmation propre ; ils ne relancent pas une rédaction IA. Les
directives explicites d'agenda n'ont pas de contexte documentaire de modèle.

## OpenClaw

Les routes `POST /api/agents/dispatch` et
`POST /api/agents/sessions/{session_id}/send` répondent 403, quel que soit
l'état des accords. Aucun appel de passerelle ni création de session n'a lieu.
Les fonctions internes d'envoi sont également fermées. Le fournisseur aval
ne peut pas être vérifié : donner tous les accords n'autorise donc pas ce circuit.

Le message propose d'utiliser un agent embarqué de l'Atelier. Les anciens
composants `NewTaskDialog` et `AgentChat` appellent encore ces routes via
`openclawStore` ; ils reçoivent le refus. Leur export dans `atelier/index.ts`
subsiste, mais ils ne sont pas montés dans l'interface principale actuelle.
La consultation et l'annulation des anciennes sessions restent accessibles.

Cette provenance de confidentialité est distincte du marquage des contenus
générés par IA, décrit dans `marquage-ia.md`.
