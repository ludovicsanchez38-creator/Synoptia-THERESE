"""BUG-164 — THÉRÈSE répond parfois en anglais.

Le prompt système est rédigé en français, mais ne contient aucune consigne
impérative de langue : « une assistante IA souveraine française » qualifie le
produit, « tu utilises un français naturel et fluide » est une note de style.
Et la variante servie quand le profil utilisateur est vide — le cas d'un
testeur qui vient d'installer — ne contient même pas cette seconde phrase.

Un prompt écrit en français n'est qu'une préférence statistique. Le modèle
imite la langue dominante de sa fenêtre, pas celle de ses instructions. Or le
contexte est massivement dilué : garde-fous, mémoire, contenu intégral des
pièces jointes, THERESE.md jusqu'à 10 000 caractères, résultats d'outils. Il
suffit qu'un document ou un résultat de recherche soit anglophone pour que
l'anglais devienne majoritaire. Une fois la première réponse anglaise produite,
l'historique la verrouille : il est renvoyé à chaque tour.

Le point d'injection compte autant que la consigne. `to_openai_format` place le
prompt système DANS les messages, et `OpenAIProvider.stream` ignore le
paramètre `system_prompt` qu'on lui passe. Poser la consigne après la
conversion ne toucherait donc aucun provider OpenAI-compatible, soit la
majorité d'entre eux. Elle doit être posée avant.
"""
import pytest


class TestLaConsigneEstPoseeAvantLaConversion:
    def test_le_prompt_openai_porte_la_consigne(self):
        """Le cas qui couvre OpenAI, Mistral, Grok, DeepSeek, OpenRouter, Ollama.

        Ces providers ne lisent QUE les messages : si la consigne n'est pas
        entrée avant la conversion, elle ne leur parvient jamais.
        """
        from app.services.context import ContextWindow
        from app.services.llm import LLMService

        contexte = ContextWindow(messages=[], system_prompt="Tu es THÉRÈSE.")
        contexte.system_prompt = LLMService._avec_consigne_de_langue(
            contexte.system_prompt
        )

        messages = contexte.to_openai_format()
        systeme = next((m for m in messages if m["role"] == "system"), None)

        assert systeme is not None
        assert "français" in systeme["content"].lower(), (
            "le prompt envoyé aux providers OpenAI-compatible ne contient "
            "aucune consigne de langue : rien ne retient le modèle de basculer "
            "en anglais quand son contexte l'est"
        )

    def test_le_prompt_anthropic_et_gemini_porte_la_consigne(self):
        """La seconde surface : ces fournisseurs reçoivent un champ séparé.

        Anthropic, Gemini et Ollama lisent le prompt système par paramètre, la
        famille OpenAI par un message. Corriger le champ à la source alimente
        les deux d'un coup ; corriger l'une des deux surfaces en oublierait
        sept fournisseurs sur dix.
        """
        from app.services.context import ContextWindow
        from app.services.llm import LLMService

        contexte = ContextWindow(messages=[], system_prompt="Tu es THÉRÈSE.")
        contexte.system_prompt = LLMService._avec_consigne_de_langue(
            contexte.system_prompt
        )

        systeme_anthropic, _ = contexte.to_anthropic_format()
        systeme_gemini, _ = contexte.to_gemini_format()

        assert systeme_anthropic and "français" in systeme_anthropic.lower()
        assert systeme_gemini and "français" in systeme_gemini.lower()

    def test_un_prompt_absent_recoit_quand_meme_la_consigne(self):
        """`system_prompt=None` est atteignable et ne doit pas rester muet."""
        from app.services.llm import LLMService

        resultat = LLMService._avec_consigne_de_langue(None)

        assert resultat and "français" in resultat.lower()

    def test_la_consigne_n_est_pas_empilee_a_chaque_tour(self):
        """Idempotence : la continuation après outils repasse par le même chemin.

        Sans garde, chaque tour d'outils ajouterait un bloc de plus, et une
        conversation un peu longue finirait avec la consigne répétée dix fois
        dans son prompt système.
        """
        from app.services.llm import LLMService

        une_fois = LLMService._avec_consigne_de_langue("Tu es THÉRÈSE.")
        deux_fois = LLMService._avec_consigne_de_langue(une_fois)

        assert une_fois == deux_fois

    def test_la_consigne_precede_le_reste_du_prompt(self):
        """En tête, jamais en queue.

        Plusieurs chemins terminent leur prompt par une consigne de format
        forte. Une instruction de langue ajoutée après serait en concurrence
        avec elles ; placée avant, elle cadre tout ce qui suit.
        """
        from app.services.llm import LLMService

        resultat = LLMService._avec_consigne_de_langue("CONSIGNE FINALE DE FORMAT")

        assert resultat.index("français") < resultat.index("CONSIGNE FINALE")


class TestLaConsigneEstImperative:
    def test_elle_ordonne_plutot_qu_elle_ne_decrit(self):
        """« assistante française » décrit un produit, pas une langue de sortie."""
        from app.services.llm import LLMService

        texte = LLMService.LANGUE_BLOCK.lower()

        assert "réponds" in texte or "répond" in texte
        assert "français" in texte

    def test_elle_couvre_le_cas_du_contexte_anglophone(self):
        """C'est le déclencheur réel : un document ou un mail en anglais."""
        from app.services.llm import LLMService

        texte = LLMService.LANGUE_BLOCK.lower()

        assert "anglais" in texte, (
            "la consigne ne dit rien du cas qui produit le bug : un contexte "
            "rédigé dans une autre langue que celle de la réponse attendue"
        )


class TestAucunCheminNePeutContournerLaConsigne:
    def test_le_provider_n_est_appele_que_depuis_les_deux_sites_corriges(self):
        """Garde-fou structurel : c'est ce qui rend l'oubli impossible.

        La consigne est posée dans `stream_response_with_tools` et
        `continue_with_tool_results`. Tant que tout appel à un modèle transite
        par l'un des deux, un nouveau chemin en hérite sans que personne n'ait
        à y penser. Ce test échoue le jour où quelqu'un appelle un provider
        directement, et rappelle alors qu'il faut y poser la consigne.

        On lit le fichier plutôt que d'inspecter l'objet : c'est la structure
        du code qu'on verrouille, pas un comportement d'exécution.
        """
        import ast
        import inspect

        from app.services import llm as module_llm

        source = inspect.getsource(module_llm)
        arbre = ast.parse(source)

        fonctions_autorisees = {
            "stream_response_with_tools",
            "continue_with_tool_results",
        }
        appels_hors_sites: list[str] = []

        for noeud in ast.walk(arbre):
            if not isinstance(noeud, ast.AsyncFunctionDef | ast.FunctionDef):
                continue
            if noeud.name in fonctions_autorisees:
                continue
            for interne in ast.walk(noeud):
                if not isinstance(interne, ast.Attribute):
                    continue
                if interne.attr not in ("stream", "continue_with_tool_results"):
                    continue
                cible = interne.value
                if isinstance(cible, ast.Attribute) and cible.attr == "_provider":
                    appels_hors_sites.append(f"{noeud.name} -> _provider.{interne.attr}")

        assert not appels_hors_sites, (
            "un modèle est appelé hors des deux points où la consigne de langue "
            f"est posée, ce chemin répondra donc dans la langue de son contexte : {appels_hors_sites}"
        )


class TestLeReglageMortEstRetire:
    def test_la_langue_n_est_plus_un_reglage_stocke_que_rien_ne_lit(self):
        """Un réglage enregistré qu'aucun code ne consulte est un piège.

        `LLMBehaviorSettings.language` était stocké en base par une route
        dédiée, n'était lu nulle part, et n'avait aucun écran. Le laisser
        aurait fait croire au prochain développeur que la langue est
        configurable, et à un utilisateur curieux de l'API qu'il peut la régler.
        """
        from app.models.schemas_personalisation import LLMBehaviorSettings

        assert not hasattr(LLMBehaviorSettings(), "language"), (
            "le réglage de langue est toujours là, toujours sans lecteur "
            "et toujours sans écran"
        )


@pytest.mark.asyncio
async def test_le_chat_transmet_la_consigne_au_provider(monkeypatch):
    """Bout en bout : ce que le provider reçoit réellement."""
    from app.services.context import ContextWindow
    from app.services.llm import LLMConfig, LLMProvider, LLMService

    service = LLMService(LLMConfig(provider=LLMProvider.OPENAI, model="gpt-5.6"))

    recus: list[list[dict]] = []

    class FauxProvider:
        async def stream(self, _system_prompt, messages, _tools=None, **_kwargs):
            recus.append(messages)
            return
            yield  # pragma: no cover - générateur vide

    service._provider = FauxProvider()

    async def deja_pret():
        return None

    monkeypatch.setattr(service, "_ensure_provider", deja_pret)

    contexte = ContextWindow(messages=[], system_prompt="Tu es THÉRÈSE.")
    async for _ in service.stream_response_with_tools(contexte):
        pass

    assert recus, "le provider n'a pas été appelé"
    systeme = next((m for m in recus[0] if m["role"] == "system"), None)
    assert systeme and "français" in systeme["content"].lower()
