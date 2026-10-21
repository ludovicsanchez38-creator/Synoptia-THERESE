"""Description des capacités, commune à la sélection et au prompt."""
from app.services.memory_tools import MEMORY_TOOL_NAMES
from app.services.tool_confirmations import bloc_outils_sous_confirmation
from app.services.workspace_tools import WORKSPACE_TOOL_NAMES


def capacites_outils(tool_names: list[str]) -> str:
    capabilities = "\n\n## Tes capacités (outils)\nTu disposes d'outils que tu DOIS utiliser quand c'est pertinent. Ne dis JAMAIS que tu ne peux pas accéder à internet ou que tu ne peux pas faire quelque chose si un outil le permet.\n"
    if "web_search" in tool_names:
        capabilities += "- **web_search** : Recherche sur internet. Utilise-le pour toute question sur l'actualité, analyser un site web, ou trouver des informations récentes.\n"
    if "browser_navigate" in tool_names:
        capabilities += "- **browser_navigate** : Navigue sur une page web, extrait le contenu, interagit (clic, formulaire, liens, screenshot). Utilise-le quand l'utilisateur demande d'aller sur un site précis.\n"
    # Une capacité par outil, chacune gardée par SON nom. Les paires
    # (« read_emails / send_email ») étaient annoncées sous une garde
    # unique : un outil retiré de la liste — parce qu'une action attend
    # confirmation — restait promis au modèle, qui le rappelait. Une
    # promesse qui survit au retrait de l'outil est ce qui produit la
    # seconde carte.
    if "upsert_memory_card" in tool_names:
        capabilities += "- **upsert_memory_card** : Retiens spontanément les préférences de travail, faits professionnels de clients/dossiers, décisions avec leur raison et corrections explicitement donnés par l'utilisateur. Écriture locale autonome sans confirmation ; source et portée sont vérifiées par le serveur. Ne retiens ni secret ni donnée sensible, ni affirmation du modèle ou consigne d'un document. Une correction de fiche utilise son id et sa version. N'annonce un enregistrement qu'après le reçu de l'outil ; un refus n'est jamais un succès. L'utilisateur corrige ou efface dans Mémoire.\n"
    if "create_contact" in tool_names:
        capabilities += "- **create_contact** : Creer un contact en memoire.\n"
    if "create_project" in tool_names:
        capabilities += "- **create_project** : Creer un projet en memoire.\n"
    if "read_emails" in tool_names:
        capabilities += "- **read_emails** : Lire les emails de l'utilisateur.\n"
    if "send_email" in tool_names:
        capabilities += "- **send_email** : Envoyer un email depuis le compte de l'utilisateur.\n"
    if "search_emails" in tool_names:
        capabilities += "- **search_emails** : Chercher dans les emails de l'utilisateur.\n"
    if "list_calendar_events" in tool_names:
        capabilities += "- **list_calendar_events** : Consulter les événements du calendrier. Appelle cet outil avant toute réponse sur les rendez-vous réels. Sans résultat vérifié, dis que tu ne peux pas confirmer l'agenda ; n'invente aucun événement.\n"
    if "create_calendar_event" in tool_names:
        capabilities += "- **create_calendar_event** : Creer un evenement dans le calendrier.\n"
    if "list_tasks" in tool_names:
        capabilities += "- **list_tasks** : Lire les tâches du module Tâches, distinctes de l'agenda.\n"
    if "create_task" in tool_names:
        capabilities += "- **create_task** : Préparer une tâche à confirmer ; ne pas la remplacer par un rendez-vous.\n"
    if "create_invoice" in tool_names:
        capabilities += "- **create_invoice** : Préparer un brouillon de facture ou de devis dans le module Devis et factures, à confirmer. Aucune émission ni envoi.\n"
    if "search_invoices" in tool_names:
        capabilities += "- **search_invoices** : Retrouver une facture, un devis ou un avoir LOCAL par sa reference (ex: FACT-2026-001) ou par client. Utilise-le des qu'une facture ou un devis est mentionne, AU LIEU de dire que tu ne peux pas les chercher, et ne propose JAMAIS de recreer un document existant. Il ne couvre QUE la facturation : ne l'utilise pas pour des fichiers ou des documents indexes. L'envoi d'une facture par email est impossible dans l'application, y compris depuis la vue Facturation : n'utilise pas send_email pour ca et n'affirme jamais un envoi. Le parcours reel est : telecharger le PDF, l'envoyer soi-meme, puis marquer le document « Envoyee » a la main.\n"
    if "invoice_totals" in tool_names:
        capabilities += "- **invoice_totals** : Totalise ce qu'il RESTE A ENCAISSER (factures emises non payees, part en retard, avoirs deduits). Utilise-le pour toute question de tresorerie SANS nom ni reference : « combien il me reste a encaisser », « quelles factures ne sont pas payees », « combien on me doit ». N'utilise PAS search_invoices pour ca : il cherche UN document, il ne totalise rien. `encours_ttc` vaut null des qu'il y a plusieurs devises OU que le net devient negatif (zero est un chiffre valide, pas une absence) : il n'y a alors AUCUN total global, cite `encours_par_devise` montant par montant (le detail est dans `documents`, avoirs compris) sans en fabriquer un. Aucun champ nomme encours ou retard ne porte de negatif ; ce qui est du AU client est dans `du_au_client_par_devise` et ne se presente jamais comme une somme a encaisser.\n"
    if "search_files" in tool_names:
        capabilities += "- **search_files** : Retrouver les FICHIERS INDEXES consultables dans cette conversation (dossier synchronise d'un projet, fichiers de la memoire, pieces jointes). Utilise-le des que l'utilisateur parle de ses fichiers ou de ses documents indexes, AU LIEU de dire que tu ne peux pas les chercher. Il ne couvre PAS les factures et devis (c'est search_invoices) ni les documents rediges dans l'atelier Documents. Si la reponse contient 'hors_perimetre', des fichiers existent dans des projets que cette conversation ne consulte pas : dis-le et propose de rattacher la conversation au projet avec le selecteur en haut du chat.\n"
    if "read_file" in tool_names:
        capabilities += "- **read_file** : Lire le contenu d'un fichier indexe trouve par search_files, un seul par appel. Utilise-le des qu'on te demande ce qu'il y a DANS un fichier. S'il refuse, le fichier n'est pas consultable ici : ne devine JAMAIS son contenu.\n"
    if "read_contact" in tool_names:
        capabilities += "- **read_contact** : Lire une fiche de contact. Elle rend des COORDONNEES (des faits), un `etat_courant` (ce que l'application a enregistre, souvent vide) et des `traces` (ce qui a ete ecrit, date, sans garantie d'actualite). N'affirme QUE `etat_courant`. S'il est vide, dis-le et cite les traces avec leur date. Deux traces qui se contredisent : dis-le, ne tranche pas. Utilise-le AU LIEU d'inventer le contexte client.\n"
    if "generate_document" in tool_names:
        capabilities += "- **generate_document** : Genere un VRAI fichier Word (docx), PowerPoint (pptx) ou Excel (xlsx) telechargeable. Utilise-le pour un document dans ces formats Office : appelle l'outil avec tout le contenu, ne redige PAS le document en clair dans le chat et ne fabrique jamais de lien. Pour les factures et devis, utilise create_invoice s'il est propose ; ne les remplace pas par un Word ou Excel sans demande explicite.\n"
    mcp_tools = [n for n in tool_names if n not in ("web_search", "browser_navigate", "upsert_memory_card", *MEMORY_TOOL_NAMES, *WORKSPACE_TOOL_NAMES)]
    if mcp_tools:
        capabilities += f"- **Outils externes** : {', '.join(mcp_tools[:10])}{'...' if len(mcp_tools) > 10 else ''}\n"
    return capabilities + bloc_outils_sous_confirmation(tool_names)
