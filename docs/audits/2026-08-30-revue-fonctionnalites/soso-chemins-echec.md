# Revue Soso — les chemins d'échec (30/08/2026)

> Verdict : **NO-GO**. Extrait du rapport final ; la trace complète de
> l'exploration n'est pas conservée (2,6 Mo).

# NO-GO

En l’état, THÉRÈSE peut déclarer une opération réussie alors que le livrable est faux, incomplet ou fondé sur aucune donnée exploitable. C’est plus grave qu’un échec franc. Les trois incidents d’amorce ne sont pas repris ci-dessous.

## Livrables faux ou succès trompeurs

1. **Le repli XLSX fabrique un tableur qui paraît valide**

   **Attendu / obtenu.** L’utilisateur demande plusieurs onglets. Il obtient un seul onglet `Données`. Les en-têtes des tableaux suivants deviennent des lignes de données. Si aucun tableau n’est compris, il reçoit quand même un classeur avec les colonnes `A`, `B`, `C`.

   **Chemin.** Le contrat promet un onglet par tableau dans [xlsx_generator.py:115](</Users/synoptia/Desktop/Dev Synoptia/Synoptia-THERESE/src/backend/app/services/skills/xlsx_generator.py:115>). Après l’échec du script, [code_executor.py:870](</Users/synoptia/Desktop/Dev Synoptia/Synoptia-THERESE/src/backend/app/services/skills/code_executor.py:870>) appelle le repli, qui crée un seul onglet dans [xlsx_generator.py:142](</Users/synoptia/Desktop/Dev Synoptia/Synoptia-THERESE/src/backend/app/services/skills/xlsx_generator.py:142>). Le parseur de [xlsx_generator.py:219](</Users/synoptia/Desktop/Dev Synoptia/Synoptia-THERESE/src/backend/app/services/skills/xlsx_generator.py:219>) mélange les tableaux. La validation ne fait que compter les lignes non vides dans [code_executor.py:213](</Users/synoptia/Desktop/Dev Synoptia/Synoptia-THERESE/src/backend/app/services/skills/code_executor.py:213>).

   **Reproduction.** Demander deux onglets, puis provoquer une réponse sans script exécutable ou un échec du script.

2. **Le repli DOCX peut insérer du code Python tronqué dans le document**

   **Attendu / obtenu.** L’utilisateur attend un document Word. Il reçoit un DOCX contenant des instructions Python présentées comme des paragraphes ordinaires.

   **Chemin.** Un bloc Python ouvert mais non refermé est tout de même extrait par [code_executor.py:235](</Users/synoptia/Desktop/Dev Synoptia/Synoptia-THERESE/src/backend/app/services/skills/code_executor.py:235>). Après son échec, seuls les blocs correctement refermés sont supprimés dans [code_executor.py:886](</Users/synoptia/Desktop/Dev Synoptia/Synoptia-THERESE/src/backend/app/services/skills/code_executor.py:886>). Le repli DOCX conserve alors les lignes Python comme contenu dans [docx_generator.py:257](</Users/synoptia/Desktop/Dev Synoptia/Synoptia-THERESE/src/backend/app/services/skills/docx_generator.py:257>). Quelques paragraphes non vides suffisent pour valider le fichier dans [code_executor.py:193](</Users/synoptia/Desktop/Dev Synoptia/Synoptia-THERESE/src/backend/app/services/skills/code_executor.py:193>).

   **Reproduction.** Faire interrompre la réponse du modèle après une ouverture `````python``, avec un script incomplet.

3. **Le générateur HTML transforme un refus ou une réponse partielle en page réussie**

   **Attendu / obtenu.** L’utilisateur attend une page web. Il obtient une page mise en forme dont le contenu est le refus du modèle, son commentaire ou du HTML incomplet affiché comme texte.

   **Chemin.** L’extraction exige un document HTML complet dans [html_generator.py:149](</Users/synoptia/Desktop/Dev Synoptia/Synoptia-THERESE/src/backend/app/services/skills/html_generator.py:149>). Sinon, toute la réponse est échappée dans un `<pre>` par [html_generator.py:174](</Users/synoptia/Desktop/Dev Synoptia/Synoptia-THERESE/src/backend/app/services/skills/html_generator.py:174>), puis enregistrée avec succès. La validation de [code_executor.py:183](</Users/synoptia/Desktop/Dev Synoptia/Synoptia-THERESE/src/backend/app/services/skills/code_executor.py:183>) ne contrôle que DOCX, PPTX et XLSX. Tout HTML passe.

   **Reproduction.** Faire produire un HTML sans `</html>` ou une réponse de refus.

4. **Une pièce jointe illisible est affichée comme prête, puis le chat répond sans son contenu**

   **Attendu / obtenu.** L’utilisateur voit la pièce jointe marquée prête et pense que la réponse s’appuie dessus. Le modèle peut répondre sans avoir reçu le document.

   **Chemin.** Les erreurs d’extraction deviennent `None` dans [file_parser.py:75](</Users/synoptia/Desktop/Dev Synoptia/Synoptia-THERESE/src/backend/app/services/file_parser.py:75>). Un PDF scanné devient une chaîne vide dans [file_parser.py:176](</Users/synoptia/Desktop/Dev Synoptia/Synoptia-THERESE/src/backend/app/services/file_parser.py:176>). L’indexation enregistre malgré tout zéro segment dans [indexation.py:537](</Users/synoptia/Desktop/Dev Synoptia/Synoptia-THERESE/src/backend/app/services/indexation.py:537>). Le frontend passe inconditionnellement la pièce jointe à `ready` dans [ChatInput.tsx:240](</Users/synoptia/Desktop/Dev Synoptia/Synoptia-THERESE/src/frontend/src/components/chat/ChatInput.tsx:240>). Le backend journalise l’échec puis poursuit l’appel au modèle dans [chat.py:1629](</Users/synoptia/Desktop/Dev Synoptia/Synoptia-THERESE/src/backend/app/routers/chat.py:1629>).

   **Reproduction.** Joindre un PDF scanné sans OCR, un fichier corrompu ou un DOCX dont les informations utiles sont uniquement dans des tableaux.

5. **Les actions déclarées avec `web_search` ne font aucune recherche web**

   **Attendu / obtenu.** « Veille concurrentielle » et « Préparation de rendez-vous » promettent des recherches publiques actuelles. L’utilisateur reçoit une réponse de modèle sans recherche ni source web.

   **Chemin.** Les actions déclarent `web_search` dans [action_agents.json:71](</Users/synoptia/Desktop/Dev Synoptia/Synoptia-THERESE/src/backend/app/agents/action_agents.json:71>) et [action_agents.json:142](</Users/synoptia/Desktop/Dev Synoptia/Synoptia-THERESE/src/backend/app/agents/action_agents.json:142>). `_gather_local_context` ne sait traiter que les données locales dans [action_agents.py:253](</Users/synoptia/Desktop/Dev Synoptia/Synoptia-THERESE/src/backend/app/services/action_agents.py:253>). Chaque étape est ensuite envoyée à `llm.stream_response()` sans outil dans [action_agents.py:664](</Users/synoptia/Desktop/Dev Synoptia/Synoptia-THERESE/src/backend/app/services/action_agents.py:664>).

   **Reproduction.** Lancer une veille sans connexion réseau. Elle produit quand même un résultat.

6. **Les rapports métier demandent des faits absents des données fournies au modèle**

   **Attendu / obtenu.** Le rapport hebdomadaire promet les e-mails reçus et envoyés, les décisions, l’activité CRM et les tâches terminées. L’audit de trésorerie promet délais de paiement, retards, prévisions et solde actuel. Le modèle ne reçoit pas ces données.

   **Chemin.** Les promesses sont dans [action_agents.json:3](</Users/synoptia/Desktop/Dev Synoptia/Synoptia-THERESE/src/backend/app/agents/action_agents.json:3>) et [action_agents.json:109](</Users/synoptia/Desktop/Dev Synoptia/Synoptia-THERESE/src/backend/app/agents/action_agents.json:109>). Le contexte réel contient seulement 20 en-têtes d’e-mails, 15 contacts, 10 événements futurs, 15 tâches et 15 factures sans dates de règlement ni solde bancaire dans [action_agents.py:262](</Users/synoptia/Desktop/Dev Synoptia/Synoptia-THERESE/src/backend/app/services/action_agents.py:262>) et [action_agents.py:366](</Users/synoptia/Desktop/Dev Synoptia/Synoptia-THERESE/src/backend/app/services/action_agents.py:366>).

   **Reproduction.** Lancer « Rapport hebdomadaire » ou « Audit trésorerie ». Le texte est généré sans les éléments nécessaires pour établir les indicateurs demandés.

7. **Une action reste “terminée” même si une ou plusieurs étapes ont échoué**

   **Attendu / obtenu.** L’utilisateur attend un rapport complet ou un état d’échec. Il reçoit un rapport amputé, ou rien, avec le statut `completed`.

   **Chemin.** Une exception d’étape est capturée puis la boucle continue dans [action_agents.py:708](</Users/synoptia/Desktop/Dev Synoptia/Synoptia-THERESE/src/backend/app/services/action_agents.py:708>). Le résultat final ne contient que les étapes réussies dans [action_agents.py:726](</Users/synoptia/Desktop/Dev Synoptia/Synoptia-THERESE/src/backend/app/services/action_agents.py:726>). Le statut passe ensuite inconditionnellement à `COMPLETED` dans [action_agents.py:740](</Users/synoptia/Desktop/Dev Synoptia/Synoptia-THERESE/src/backend/app/services/action_agents.py:740>).

   **Reproduction.** Faire échouer le fournisseur sur une étape, par exemple par quota ou jeton expiré, puis laisser une étape suivante réussir.

8. **Décision transforme une panne de recherche web en “Aucun résultat”**

   **Attendu / obtenu.** L’utilisateur attend une décision enrichie par le web ou une erreur explicite. Il obtient une décision finalisée et enregistrée sans sources, comme si la recherche n’avait simplement rien trouvé.

   **Chemin.** Toute exception de recherche devient `""` dans [board.py:274](</Users/synoptia/Desktop/Dev Synoptia/Synoptia-THERESE/src/backend/app/services/board.py:274>). La délibération émet ensuite `Aucun résultat` et continue dans [board.py:401](</Users/synoptia/Desktop/Dev Synoptia/Synoptia-THERESE/src/backend/app/services/board.py:401>). La décision est sauvegardée avec une liste de sources vide dans [board.py:815](</Users/synoptia/Desktop/Dev Synoptia/Synoptia-THERESE/src/backend/app/services/board.py:815>).

   **Reproduction.** Couper l’accès au moteur de recherche puis lancer une décision cloud.

9. **La validation d’une section de document masque l’échec du modèle**

   **Attendu / obtenu.** L’utilisateur croit avoir validé une section avec un résumé sémantique utilisable pour la cohérence globale. En cas d’échec, THÉRÈSE prend arbitrairement les 300 premiers caractères et marque quand même la section `validee`.

   **Chemin.** Le repli est appliqué sur résumé vide ou exception dans [documents.py:448](</Users/synoptia/Desktop/Dev Synoptia/Synoptia-THERESE/src/backend/app/routers/documents.py:448>), puis le statut est validé dans [documents.py:485](</Users/synoptia/Desktop/Dev Synoptia/Synoptia-THERESE/src/backend/app/routers/documents.py:485>). Ce faux résumé alimente les sections suivantes dans [document_orchestrator.py:160](</Users/synoptia/Desktop/Dev Synoptia/Synoptia-THERESE/src/backend/app/services/document_orchestrator.py:160>).

   **Reproduction.** Couper le fournisseur au moment de cliquer sur « Valider » une section déjà rédigée.

10. **La synchronisation CRM ignore entièrement l’onglet Deliverables**

   **Attendu / obtenu.** L’API annonce la synchronisation de Clients, Projects et Deliverables. Les livrables ne sont jamais lus, mais l’opération peut répondre succès.

   **Chemin.** La promesse figure dans [crm.py:1324](</Users/synoptia/Desktop/Dev Synoptia/Synoptia-THERESE/src/backend/app/routers/crm.py:1324>). L’implémentation parcourt Clients, Projects puis Tasks dans [crm.py:1392](</Users/synoptia/Desktop/Dev Synoptia/Synoptia-THERESE/src/backend/app/routers/crm.py:1392>), sans boucle Deliverables, avant de renvoyer le succès dans [crm.py:1462](</Users/synoptia/Desktop/Dev Synoptia/Synoptia-THERESE/src/backend/app/routers/crm.py:1462>).

   **Reproduction.** Modifier uniquement un livrable dans le tableur, puis lancer la synchronisation.

11. **Le statut choisi lors de la création d’une facture ou d’un devis est ignoré**

   **Attendu / obtenu.** L’utilisateur crée un document directement comme envoyé, payé ou accepté. Il reçoit systématiquement un brouillon, avec une notification de réussite.

   **Chemin.** Le frontend envoie `status` dans [InvoiceForm.tsx:247](</Users/synoptia/Desktop/Dev Synoptia/Synoptia-THERESE/src/frontend/src/components/invoices/InvoiceForm.tsx:247>). `CreateInvoiceRequest` ne définit pas ce champ dans [schemas.py:959](</Users/synoptia/Desktop/Dev Synoptia/Synoptia-THERESE/src/backend/app/models/schemas.py:959>), puis la route force `status="draft"` dans [invoices.py:294](</Users/synoptia/Desktop/Dev Synoptia/Synoptia-THERESE/src/backend/app/routers/invoices.py:294>).

   **Reproduction.** Créer une facture avec le statut « Payée » ou « Envoyée », puis la rouvrir.

12. **Un devis refusé, expiré ou encore brouillon peut être converti en facture**

   **Attendu / obtenu.** L’utilisateur s’attend à convertir seulement un devis accepté. THÉRÈSE autorise également les devis refusés, expirés et brouillons, puis marque le devis comme converti.

   **Chemin.** Le frontend bloque uniquement `converted` et `cancelled` dans [InvoiceForm.tsx:384](</Users/synoptia/Desktop/Dev Synoptia/Synoptia-THERESE/src/frontend/src/components/invoices/InvoiceForm.tsx:384>). Le backend applique la même vérification insuffisante dans [invoices.py:775](</Users/synoptia/Desktop/Dev Synoptia/Synoptia-THERESE/src/backend/app/routers/invoices.py:775>), crée la facture et bascule la source à `converted` dans [invoices.py:821](</Users/synoptia/Desktop/Dev Synoptia/Synoptia-THERESE/src/backend/app/routers/invoices.py:821>).

   **Reproduction.** Passer un devis à « Refusé » ou « Expiré », le rouvrir puis cliquer sur la conversion.

13. **Un agenda Google supprimé ou inaccessible apparaît comme un agenda vide**

   **Attendu / obtenu.** L’utilisateur attend une erreur de connexion ou d’autorisation. Il voit simplement zéro événement et une synchronisation qui peut être déclarée terminée.

   **Chemin.** Une réponse HTTP 404 est transformée en `[]` dans [calendar.py:753](</Users/synoptia/Desktop/Dev Synoptia/Synoptia-THERESE/src/backend/app/routers/calendar.py:753>). La synchronisation compte cette liste vide puis renvoie une réponse normale dans [calendar.py:1319](</Users/synoptia/Desktop/Dev Synoptia/Synoptia-THERESE/src/backend/app/routers/calendar.py:1319>). Le frontend remplace alors les événements affichés par cette liste dans [CalendarPanel.tsx:151](</Users/synoptia/Desktop/Dev Synoptia/Synoptia-THERESE/src/frontend/src/components/calendar/CalendarPanel.tsx:151>).

   **Reproduction.** Sélectionner un agenda partagé supprimé ou conserver un identifiant devenu inaccessible.

## Échecs francs ou indiagnostiquables

14. **Les deux analyses guidées de fichiers sont impossibles à lancer**

   **Attendu / obtenu.** « Analyser un Excel » et « Analyser un PDF » demandent un fichier. Aucun sélecteur n’est affiché et le bouton reste désactivé.

   **Chemin.** Les skills exigent un champ `file` dans [analysis_skills.py:11](</Users/synoptia/Desktop/Dev Synoptia/Synoptia-THERESE/src/backend/app/services/skills/analysis_skills.py:11>) et [analysis_skills.py:48](</Users/synoptia/Desktop/Dev Synoptia/Synoptia-THERESE/src/backend/app/services/skills/analysis_skills.py:48>). Le formulaire connaît le type mais ne rend que `text`, `textarea`, `select` et `number` dans [DynamicSkillForm.tsx:102](</Users/synoptia/Desktop/Dev Synoptia/Synoptia-THERESE/src/frontend/src/components/guided/DynamicSkillForm.tsx:102>). La validation requise bloque ensuite le bouton dans [DynamicSkillForm.tsx:193](</Users/synoptia/Desktop/Dev Synoptia/Synoptia-THERESE/src/frontend/src/components/guided/DynamicSkillForm.tsx:193>).

   **Reproduction.** Ouvrir Produire/Comprendre, puis « Fichier Excel » ou « Document PDF ».

15. **Les erreurs d’envoi et de brouillon d’e-mail perdent la cause réelle**

   **Attendu / obtenu.** L’utilisateur devrait savoir si son jeton a expiré, si Gmail refuse l’envoi ou si SMTP est mal configuré. Il reçoit seulement `Failed to send email` ou `Failed to create draft`.

   **Chemin.** Le client ne lit pas le corps des réponses en erreur dans [email.ts:300](</Users/synoptia/Desktop/Dev Synoptia/Synoptia-THERESE/src/frontend/src/services/api/email.ts:300>) et [email.ts:310](</Users/synoptia/Desktop/Dev Synoptia/Synoptia-THERESE/src/frontend/src/services/api/email.ts:310>). Le composeur affiche directement ce message générique dans [EmailCompose.tsx:104](</Users/synoptia/Desktop/Dev Synoptia/Synoptia-THERESE/src/frontend/src/components/email/EmailCompose.tsx:104>).

   **Reproduction.** Révoquer le jeton Gmail ou utiliser une configuration SMTP invalide.

16. **Une panne du chargement des factures devient “Aucune facture”**

   **Attendu / obtenu.** L’utilisateur attend un message d’indisponibilité. Il voit un état métier vide et peut croire que ses factures ont disparu.

   **Chemin.** Le store démarre avec `invoices: []` dans [invoiceStore.ts:54](</Users/synoptia/Desktop/Dev Synoptia/Synoptia-THERESE/src/frontend/src/stores/invoiceStore.ts:54>). Le panneau ne fait que journaliser l’échec dans [InvoicesPanel.tsx:71](</Users/synoptia/Desktop/Dev Synoptia/Synoptia-THERESE/src/frontend/src/components/invoices/InvoicesPanel.tsx:71>), puis affiche « Aucune facture » lorsque la liste reste vide dans [InvoicesPanel.tsx:250](</Users/synoptia/Desktop/Dev Synoptia/Synoptia-THERESE/src/frontend/src/components/invoices/InvoicesPanel.tsx:250>).

   **Reproduction.** Ouvrir Factures avec le sidecar ou la base indisponible.

17. **La suppression d’une conversation masque l’échec serveur**

   **Attendu / obtenu.** L’utilisateur croit avoir supprimé durablement la conversation. Elle disparaît seulement de l’état local et peut revenir après reconnexion.

   **Chemin.** L’erreur de l’API est explicitement avalée par `.catch(() => {})` dans [ConversationSidebar.tsx:98](</Users/synoptia/Desktop/Dev Synoptia/Synoptia-THERESE/src/frontend/src/components/sidebar/ConversationSidebar.tsx:98>), puis la suppression locale est exécutée malgré tout.

   **Reproduction.** Charger les conversations, couper le backend, en supprimer une, puis redémarrer ou resynchroniser.

## Frictions fonctionnelles

18. **Deux commandes du registre ne font pas l’action annoncée**

   **Attendu / obtenu.** « Rechercher dans les Contacts » devrait lancer ou focaliser une recherche. « Exporter les données » devrait ouvrir l’export. La première ouvre seulement la vue Mémoire ; la seconde ouvre les Paramètres sur l’onglet Profil.

   **Chemin.** `memory.search` et `memory.open` ont exactement le même gestionnaire dans [actionRegistry.ts:55](</Users/synoptia/Desktop/Dev Synoptia/Synoptia-THERESE/src/frontend/src/lib/actionRegistry.ts:55>). `data.export` appelle uniquement `openSettings()` dans [actionRegistry.ts:77](</Users/synoptia/Desktop/Dev Synoptia/Synoptia-THERESE/src/frontend/src/lib/actionRegistry.ts:77>), dont l’onglet par défaut est Profil dans [SettingsModal.tsx:58](</Users/synoptia/Desktop/Dev Synoptia/Synoptia-THERESE/src/frontend/src/components/settings/SettingsModal.tsx:58>).

   **Reproduction.** Exécuter ces deux commandes depuis la palette.

19. **Une recherche de prompts échouée réétiquette les anciens résultats**

   **Attendu / obtenu.** L’utilisateur attend une erreur ou les résultats de la nouvelle requête. Il voit les résultats précédents sous le libellé de la nouvelle recherche.

   **Chemin.** La requête affichée est mise à jour immédiatement dans [PromptLibrary.tsx:286](</Users/synoptia/Desktop/Dev Synoptia/Synoptia-THERESE/src/frontend/src/components/prompts/PromptLibrary.tsx:286>). L’exception est capturée sans effacer `searchResults` dans [PromptLibrary.tsx:300](</Users/synoptia/Desktop/Dev Synoptia/Synoptia-THERESE/src/frontend/src/components/prompts/PromptLibrary.tsx:300>). Ces anciens résultats sont ensuite rendus comme ceux de la nouvelle requête dans [PromptLibrary.tsx:320](</Users/synoptia/Desktop/Dev Synoptia/Synoptia-THERESE/src/frontend/src/components/prompts/PromptLibrary.tsx:320>).

   **Reproduction.** Réussir une première recherche, couper le backend, puis lancer une seconde recherche.
