"""
THÉRÈSE v2 - OpenAI Provider

GPT API streaming implementation with tool support.
Sprint 2 - PERF-2.1: Extracted from monolithic llm.py
"""

import contextlib
import json
import logging
from typing import Any, AsyncGenerator

import httpx

from .base import (
    BaseProvider,
    LLMProvider,
    StreamEvent,
    ToolCall,
    ToolResult,
    ToolTurn,
    message_erreur_http,
    plafond_sortie_a_envoyer,
)

logger = logging.getLogger(__name__)

OPENAI_API_URL = "https://api.openai.com/v1/chat/completions"

# Outils via Responses (fiches lues le 09/10/2026) :
# - gpt-6.1-sol : « Use the Responses API for tool calling ».
# - gpt-6-astra : le guide function-calling et le guide raisonnement exigent
#   Responses pour les outils. Poser none renvoie HTTP 400.
# - gpt-6-sol : la fiche dit que Chat Completions accepte les outils avec
#   reasoning_effort=none. On ne le migre pas.
_MODELES_OUTILS_RESPONSES = frozenset({"gpt-6.1-sol", "gpt-6-astra"})

def _sortie_responses(modele: str, demande: int) -> int:
    """Borne la sortie au plafond publié, le même que Chat Completions."""
    plafond = plafond_sortie_a_envoyer(modele, demande)
    return demande if plafond is None else plafond


def _outils_via_responses(model: str) -> bool:
    return model.lower() in _MODELES_OUTILS_RESPONSES


def _arguments_outil(brut: Any) -> dict[str, Any]:
    if isinstance(brut, dict):
        return brut
    if not isinstance(brut, str) or not brut:
        return {}
    try:
        lu = json.loads(brut)
    except json.JSONDecodeError:
        return {}
    return lu if isinstance(lu, dict) else {}


def _bloc_chat_vers_responses(bloc: Any) -> Any:
    """Un bloc Chat (texte ou image) vers le bloc Responses correspondant.

    Le guide vision (09/10/2026) : `input_text` et `input_image`, avec
    `image_url` en chaîne (URL ou data URL), pas l'objet Chat `{url}`.
    """
    if not isinstance(bloc, dict):
        return {"type": "input_text", "text": "" if bloc is None else str(bloc)}
    type_bloc = bloc.get("type")
    if type_bloc == "text":
        return {"type": "input_text", "text": bloc.get("text") or ""}
    if type_bloc == "image_url":
        source = bloc.get("image_url")
        url = source.get("url") if isinstance(source, dict) else source
        return {"type": "input_image", "image_url": url or ""}
    return bloc


# Items de sortie à rejouer tels quels avec les résultats d'outils.
# Le guide function-calling (09/10/2026) : les éléments de raisonnement
# reviennent avec les function_call, sinon le tour suivant les perd.
_TYPES_SORTIE_A_REJOUER = frozenset({"reasoning", "function_call", "message"})


def _elements_a_rejouer(contenu: Any) -> list[dict[str, Any]]:
    if not isinstance(contenu, list):
        return []
    return [
        element for element in contenu
        if isinstance(element, dict) and element.get("type") in _TYPES_SORTIE_A_REJOUER
    ]


def _contenu_message_responses(contenu: Any) -> Any:
    """Une chaîne reste une chaîne. Une liste de blocs est traduite."""
    if contenu is None:
        return ""
    if not isinstance(contenu, list):
        return contenu
    return [_bloc_chat_vers_responses(bloc) for bloc in contenu]


def _messages_vers_input_responses(messages: list[dict[Any, Any]]) -> list[dict[str, Any]]:
    """Traduit le transcript Chat déjà construit vers les items Responses."""
    items: list[dict[str, Any]] = []
    for msg in messages:
        role = msg.get("role")
        if role == "tool":
            sortie = msg.get("content")
            if not isinstance(sortie, str):
                sortie = json.dumps(sortie) if sortie is not None else ""
            items.append({
                "type": "function_call_output",
                "call_id": msg.get("tool_call_id") or "",
                "output": sortie,
            })
            continue
        appels = msg.get("tool_calls")
        if role == "assistant" and appels:
            rejoues = _elements_a_rejouer(msg.get("content"))
            items.extend(rejoues)
            deja = {
                element.get("call_id")
                for element in rejoues
                if element.get("type") == "function_call"
            }
            for appel in appels:
                if (appel.get("id") or "") in deja:
                    continue
                fonction = appel.get("function") or {}
                items.append({
                    "type": "function_call",
                    "call_id": appel.get("id") or "",
                    "name": fonction.get("name") or "",
                    "arguments": fonction.get("arguments") or "{}",
                })
            continue
        if role in ("user", "assistant", "system", "developer"):
            items.append({
                "role": role,
                "content": _contenu_message_responses(msg.get("content")),
            })
    return items


def _outils_vers_responses(tools: list[dict[Any, Any]]) -> list[dict[str, Any]]:
    convertis: list[dict[str, Any]] = []
    for outil in tools:
        fonction = outil.get("function")
        if outil.get("type") == "function" and isinstance(fonction, dict):
            entree: dict[str, Any] = {
                "type": "function",
                "name": fonction.get("name") or "",
            }
            if fonction.get("description"):
                entree["description"] = fonction["description"]
            if "parameters" in fonction:
                entree["parameters"] = fonction["parameters"]
            convertis.append(entree)
        else:
            convertis.append(outil)
    return convertis


def _message_erreur_flux_responses(event: dict[Any, Any]) -> str:
    """Phrase d'écran. Le message brut du fournisseur n'y entre pas."""
    erreur: dict[Any, Any] = {}
    if event.get("type") == "response.failed":
        reponse = event.get("response") or {}
        erreur = reponse.get("error") or {}
    code = erreur.get("code") or event.get("code")
    if code == "server_error":
        return "API error: 500"
    if code == "rate_limit_exceeded":
        return message_erreur_http(LLMProvider.OPENAI, 429)
    return "Requête refusée par le service d'IA."


def _refuse_le_sampling(model: str) -> bool:
    """Ce modèle rejette-t-il `temperature` ?

    Signalé par Ludo le 28/08 (« gpt ne marche pas », 400 sur chaque message),
    reproduit contre l'API réelle qui répond : « Unsupported value:
    'temperature' does not support 0.7 with this model. Only the default (1)
    value is supported. »

    Même motif que Gemini 3 en 0.48.2 : les modèles de raisonnement refusent
    les réglages d'échantillonnage. C'est la même famille que celle qui exige
    `max_completion_tokens`, d'où la règle partagée ci-dessous.
    """
    return _uses_max_completion_tokens(model)


def _uses_max_completion_tokens(model: str) -> bool:
    """Check if model uses max_completion_tokens instead of max_tokens.

    GPT-5.x and o-series models require max_completion_tokens parameter.
    """
    model_lower = model.lower()
    return (
        model_lower.startswith("gpt-6") or
        model_lower.startswith("gpt-5") or
        model_lower.startswith("o1") or
        model_lower.startswith("o3") or
        model_lower.startswith("o4")
    )


class OpenAIProvider(BaseProvider):
    """OpenAI GPT API provider."""

    # US-009 : URL surclassable - GrokProvider réutilise toute la boucle
    # d'outils (xAI est OpenAI-compatible) en ne changeant que l'endpoint.
    API_URL = OPENAI_API_URL

    def url_effective(self) -> str:
        """L'adresse réellement appelée : celle configurée, sinon le défaut.

        Dette 0.43.4 : cette méthode existait sur QwenProvider mais n'était
        appelée NULLE PART - stream() partait sur API_URL en dur, et le défaut
        Qwen contient un marqueur {EspaceDeTravail} qui ne peut pas
        fonctionner. La documentation des fournisseurs donne l'adresse SANS le
        suffixe /chat/completions : on l'ajoute si l'utilisateur a collé la
        base, on ne double pas s'il a collé l'adresse complète.
        """
        base: str | None = getattr(self.config, "base_url", None)
        if not base:
            return self.API_URL
        base = base.rstrip("/")
        if base.endswith("/chat/completions"):
            return base
        return f"{base}/chat/completions"

    def url_responses(self) -> str:
        """Responses : la base configurée, sinon la même base que ``url_effective``.

        Sans ``base_url``, le repli part de ``self.API_URL`` (pas de l'adresse
        OpenAI en dur). Un héritier dont l'identifiant ressemble à un modèle
        OpenAI ne doit pas viser api.openai.com.
        """
        base: str | None = getattr(self.config, "base_url", None)
        if not base:
            base = self.API_URL
        base = base.rstrip("/")
        for suffixe in ("/chat/completions", "/responses"):
            if base.endswith(suffixe):
                base = base[: -len(suffixe)]
                break
        return f"{base}/responses"

    def _corps_responses(
        self,
        messages: list[dict[Any, Any]],
        tools: list[dict[Any, Any]] | None,
    ) -> dict[str, Any]:
        corps: dict[str, Any] = {
            "model": self.config.model,
            "input": _messages_vers_input_responses(messages),
            "stream": True,
            "max_output_tokens": _sortie_responses(
                self.config.model, self.config.max_tokens
            ),
        }
        if self.config.effort_resolu:
            corps["reasoning"] = {"effort": self.config.effort_resolu}
        if tools:
            corps["tools"] = _outils_vers_responses(tools)
            corps["tool_choice"] = "auto"
        return corps

    def _build_request_body(
        self,
        messages: list[dict],
        tools: list[dict] | None = None,
    ) -> dict[str, Any]:
        """Build request body with correct token parameter."""
        request_body: dict[str, Any] = {
            "model": self.config.model,
            "messages": messages,
            "stream": True,
            # Usage réel (dette 14/06/2026) : sans ce flag, le chunk usage final
            # n'est pas envoyé du tout par l'API OpenAI en streaming.
            "stream_options": {"include_usage": True},
        }

        plafond = plafond_sortie_a_envoyer(self.config.model, self.config.max_tokens)
        if plafond is not None and _uses_max_completion_tokens(self.config.model):
            request_body["max_completion_tokens"] = plafond
        elif plafond is not None:
            request_body["max_tokens"] = plafond

        # Le réglage reste utile là où il est accepté : on ne le retire que
        # pour les modèles qui le refusent.
        if not _refuse_le_sampling(self.config.model):
            request_body["temperature"] = self.config.temperature

        if tools:
            request_body["tools"] = tools
            request_body["tool_choice"] = "auto"

        # 0.48 : l'effort emis est RESOLU par le catalogue a la
        # construction de la config (plafonds et supports par modele y
        # vivent - gpt-5.6 tel quel, grok-4.6 xhigh, grok-4.5 plafonne
        # high, 5.5/5.4 rien). Plus de table locale.
        if self.config.effort_resolu:
            request_body["reasoning_effort"] = self.config.effort_resolu

        # 30/08/2026 : sur /v1/chat/completions, la famille GPT-5 refuse les
        # outils de fonction dès qu'un effort de raisonnement s'applique.
        # L'API le dit mot pour mot :
        #
        #   Function tools with reasoning_effort are not supported for
        #   gpt-5.6-luna in /v1/chat/completions. To use function tools, use
        #   /v1/responses or set reasoning_effort to 'none'.
        #
        # OMETTRE le paramètre ne suffit PAS : le modèle a un effort par
        # défaut, et le refus tombe quand même. Il faut le poser à « none ».
        # Vérifié contre l'API réelle sur luna, sol, terra, 5.5 et 5.4-mini :
        # les cinq refusaient. Comme THÉRÈSE fournit ses outils à CHAQUE
        # message, aucun modèle OpenAI ne fonctionnait, sur aucun écran.
        #
        # L'arbitrage : les outils sont le produit, le raisonnement est un
        # réglage. Sans outil, l'effort demandé part normalement.
        if (
            tools
            and _uses_max_completion_tokens(self.config.model)
            and not _outils_via_responses(self.config.model)
        ):
            if request_body.get("reasoning_effort") not in (None, "none"):
                logger.info(
                    "%s : effort %s neutralisé pour ce message, les outils et le "
                    "raisonnement ne cohabitent pas sur /v1/chat/completions",
                    self.config.model,
                    request_body["reasoning_effort"],
                )
            request_body["reasoning_effort"] = "none"

        return request_body

    async def _stream_request(
        self, request_body: dict[str, Any]
    ) -> AsyncGenerator[StreamEvent, None]:
        """Une tentative, et UN rejeu sans reasoning_effort si l'API le refuse.

        Le 30/08/2026, une instance neuve sur gpt-5.6-luna répondait
        `API error: 400` à TOUT message. L'API disait :

            Function tools with reasoning_effort are not supported for
            gpt-5.6-luna in /v1/chat/completions. To use function tools, use
            /v1/responses or set reasoning_effort to 'none'.

        THÉRÈSE fournit 29 outils à chaque message ET un effort : le produit
        était inutilisable avec ce modèle, sur tous les écrans. On avait
        d'abord cru à un défaut de la pièce jointe, parce que c'est là que
        Ludo l'avait vu.

        Ce repli existait chez GrokProvider seulement, pour un conflit de
        documentation sur grok-4.6. Il vit désormais ici, donc il couvre
        OpenAI et les cinq fournisseurs compatibles qui en héritent.

        Après le début du flux, jamais de rejeu : dupliquer des jetons déjà
        rendus à l'écran serait pire que l'erreur.
        """
        emis = 0
        try:
            async for event in self._une_tentative(request_body):
                emis += 1
                yield event
        except httpx.HTTPStatusError as e:
            if emis or e.response.status_code != 400 or "reasoning_effort" not in request_body:
                raise
            logger.warning(
                "%s a refusé reasoning_effort=%s (400) : seconde tentative sans "
                "le paramètre",
                type(self).__name__,
                request_body["reasoning_effort"],
            )
            corps = {k: v for k, v in request_body.items() if k != "reasoning_effort"}
            async for event in self._une_tentative(corps):
                yield event

    async def _une_tentative(
        self, request_body: dict[str, Any]
    ) -> AsyncGenerator[StreamEvent, None]:
        """UNE tentative de streaming sur le corps donné (0.48).

        Laisse remonter httpx.HTTPStatusError : c'est le point d'accroche
        du repli Grok (rejeu du corps sans reasoning_effort sur un 400).
        La gestion d'erreurs vit dans stream().
        """
        async with self.client.stream(
            "POST",
            self.url_effective(),
            headers={
                "Authorization": f"Bearer {self.config.api_key}",
                "Content-Type": "application/json",
            },
            json=request_body,
        ) as response:
            response.raise_for_status()

            # Track tool calls being built
            tool_calls: dict[int, dict[str, Any]] = {}
            # Usage réel (dette 14/06/2026) : le chunk usage (stream_options.
            # include_usage) arrive APRÈS le chunk finish_reason, choices vide.
            # On mémorise stop_reason et on n'émet "done" qu'à la toute fin
            # (chunk usage ou [DONE]) pour ne pas le manquer.
            pending_stop_reason: str | None = None
            input_tokens: int | None = None
            output_tokens: int | None = None
            # Garde de robustesse : si la connexion se coupe après
            # finish_reason mais avant [DONE]/le chunk usage, il faut
            # quand même émettre "done" (sinon chat.py reste bloqué en
            # attente indéfiniment de ce signal).
            done_emitted = False

            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    data = line[6:]
                    if data.strip() == "[DONE]":
                        yield StreamEvent(
                            type="done",
                            stop_reason=pending_stop_reason or "stop",
                            input_tokens=input_tokens,
                            output_tokens=output_tokens,
                        )
                        done_emitted = True
                        break
                    try:
                        event = json.loads(data)
                        if usage := event.get("usage"):
                            input_tokens = usage.get("prompt_tokens", input_tokens)
                            output_tokens = usage.get("completion_tokens", output_tokens)
                        choices = event.get("choices", [])
                        if choices:
                            delta = choices[0].get("delta", {})
                            finish_reason = choices[0].get("finish_reason")

                            # Handle text content
                            if content := delta.get("content"):
                                yield StreamEvent(type="text", content=content)

                            # Handle tool calls
                            if tool_call_deltas := delta.get("tool_calls"):
                                for tc_delta in tool_call_deltas:
                                    idx = tc_delta.get("index", 0)

                                    if idx not in tool_calls:
                                        tool_calls[idx] = {
                                            "id": tc_delta.get("id", ""),
                                            "name": "",
                                            "arguments": "",
                                        }
                                    # B-489 : l'id peut arriver dans un fragment ultérieur (Mistral le
                                    # gérait déjà) ; sans réaffectation, l'appel partait avec "".
                                    if tc_delta.get("id"):
                                        tool_calls[idx]["id"] = tc_delta["id"]

                                    if func := tc_delta.get("function"):
                                        if name := func.get("name"):
                                            tool_calls[idx]["name"] = name
                                        if args := func.get("arguments"):
                                            tool_calls[idx]["arguments"] += args

                            # Check if done
                            if finish_reason == "tool_calls":
                                # Emit all collected tool calls
                                for tc in tool_calls.values():
                                    try:
                                        arguments = json.loads(tc["arguments"]) if tc["arguments"] else {}
                                    except json.JSONDecodeError:
                                        arguments = {}

                                    yield StreamEvent(
                                        type="tool_call",
                                        tool_call=ToolCall(
                                            id=tc["id"],
                                            name=tc["name"],
                                            arguments=arguments,
                                        ),
                                    )
                                pending_stop_reason = "tool_calls"

                            elif finish_reason == "stop":
                                pending_stop_reason = "stop"

                    except json.JSONDecodeError:
                        continue

        # Filet : le flux s'est terminé sans jamais voir [DONE] (coupure
        # après finish_reason, ou pas de finish_reason explicite du tout).
        if not done_emitted:
            yield StreamEvent(
                type="done",
                stop_reason=pending_stop_reason or "stop",
                input_tokens=input_tokens,
                output_tokens=output_tokens,
            )

    async def _lire_flux_responses(
        self,
        messages: list[dict[Any, Any]],
        tools: list[dict[Any, Any]] | None,
    ) -> AsyncGenerator[StreamEvent, None]:
        """Un flux Responses. Lève HTTPStatusError avant le premier jeton."""
        appels: dict[int, dict[str, str]] = {}
        elements_du_tour: list[dict[str, Any]] = []
        input_tokens: int | None = None
        output_tokens: int | None = None
        pending_stop: str | None = None
        done_emitted = False
        erreur_emise = False

        async with self.client.stream(
            "POST",
            self.url_responses(),
            headers={
                "Authorization": f"Bearer {self.config.api_key}",
                "Content-Type": "application/json",
            },
            json=self._corps_responses(messages, tools),
        ) as response:
            response.raise_for_status()
            async for line in response.aiter_lines():
                if line.startswith("data: ") and line[6:].strip() == "[DONE]":
                    break
                event = self._parse_sse_line(line)
                if event is None:
                    continue
                type_evenement = event.get("type")
                if type_evenement in (
                    "response.output_text.delta",
                    "response.refusal.delta",
                ):
                    # Le refus est du texte : l'ignorer laisse une réponse vide
                    # qui se termine quand même par done/stop.
                    if delta := event.get("delta"):
                        yield StreamEvent(type="text", content=delta)
                elif type_evenement == "response.output_item.added":
                    self._noter_appel_responses(appels, event)
                elif type_evenement == "response.function_call_arguments.delta":
                    self._ajouter_delta_responses(appels, event)
                elif type_evenement == "response.output_item.done":
                    item = event.get("item")
                    if isinstance(item, dict) and item.get("type"):
                        elements_du_tour.append(item)
                    appel = self._appel_termine_responses(appels, event)
                    if appel is not None:
                        yield StreamEvent(
                            type="tool_call",
                            tool_call=appel,
                            assistant_content_brut=list(elements_du_tour),
                        )
                        pending_stop = "tool_calls"
                elif type_evenement == "response.completed":
                    usage = (event.get("response") or {}).get("usage") or {}
                    input_tokens = usage.get("input_tokens", input_tokens)
                    output_tokens = usage.get("output_tokens", output_tokens)
                    yield StreamEvent(
                        type="done",
                        stop_reason=pending_stop or "stop",
                        input_tokens=input_tokens,
                        output_tokens=output_tokens,
                    )
                    done_emitted = True
                    break
                elif type_evenement == "response.incomplete":
                    # Limite de sortie (ou filtre) : la doc émet cet événement.
                    # Le filet plus bas dirait « stop » et annoncerait une fin normale.
                    usage = (event.get("response") or {}).get("usage") or {}
                    input_tokens = usage.get("input_tokens", input_tokens)
                    output_tokens = usage.get("output_tokens", output_tokens)
                    yield StreamEvent(
                        type="done",
                        stop_reason="incomplete",
                        input_tokens=input_tokens,
                        output_tokens=output_tokens,
                    )
                    done_emitted = True
                    break
                elif type_evenement in ("error", "response.error", "response.failed"):
                    logger.warning(
                        "Réponse OpenAI en erreur (%s) : %s",
                        type_evenement,
                        str(event.get("message") or event)[:500],
                    )
                    yield StreamEvent(
                        type="error",
                        content=_message_erreur_flux_responses(event),
                    )
                    erreur_emise = True
                    break

        if not done_emitted and not erreur_emise:
            yield StreamEvent(
                type="done",
                stop_reason=pending_stop or "stop",
                input_tokens=input_tokens,
                output_tokens=output_tokens,
            )

    @staticmethod
    def _noter_appel_responses(
        appels: dict[int, dict[str, str]], event: dict[Any, Any],
    ) -> None:
        item = event.get("item") or {}
        if item.get("type") != "function_call":
            return
        index = event.get("output_index", 0)
        appels[index] = {
            "id": item.get("call_id") or "",
            "name": item.get("name") or "",
            "arguments": item.get("arguments") or "",
        }

    @staticmethod
    def _ajouter_delta_responses(
        appels: dict[int, dict[str, str]], event: dict[Any, Any],
    ) -> None:
        index = event.get("output_index", 0)
        if index not in appels:
            appels[index] = {"id": "", "name": "", "arguments": ""}
        if delta := event.get("delta"):
            appels[index]["arguments"] += delta

    @staticmethod
    def _appel_termine_responses(
        appels: dict[int, dict[str, str]],
        event: dict[Any, Any],
    ) -> ToolCall | None:
        item = event.get("item") or {}
        if item.get("type") != "function_call":
            return None
        index = event.get("output_index", 0)
        connu = appels.get(index, {})
        brut = item.get("arguments") or connu.get("arguments") or ""
        return ToolCall(
            id=item.get("call_id") or connu.get("id") or "",
            name=item.get("name") or connu.get("name") or "",
            arguments=_arguments_outil(brut),
        )

    async def stream(
        self,
        system_prompt: str | None,
        messages: list[dict],
        tools: list[dict] | None = None,
    ) -> AsyncGenerator[StreamEvent, None]:
        """Stream from OpenAI API with tool support."""
        # Responses n'existe que chez OpenAI. Grok, GLM, Kimi, MiniMax et Qwen
        # héritent de cette méthode : un identifiant personnalisé du catalogue
        # OpenAI ne doit pas y envoyer leur clé.
        if (
            tools
            and self.config.provider == LLMProvider.OPENAI
            and _outils_via_responses(self.config.model)
        ):
            source = self._lire_flux_responses(messages, tools)
        else:
            source = self._stream_request(self._build_request_body(messages, tools))

        try:
            try:
                async for event in source:
                    yield event
            finally:
                # Fermer le générateur interne : aclose du flux extérieur
                # n'atteint pas le `async with` imbriqué (la requête resterait
                # ouverte après Annuler).
                await source.aclose()
        except httpx.HTTPStatusError as e:
            # Le corps porte la raison du refus — « temperature does not
            # support 0.7 with this model » pour le 400 du 28/08 — et le log
            # la jetait : diagnostiquer obligeait à reproduire l'appel à la
            # main. Le détail va aux logs, jamais à l'écran (frontière 0.48).
            # Sur une reponse en FLUX, .text leve ResponseNotRead tant que le
            # corps n'a pas ete lu, et le suppress avalait l'exception : le
            # detail ajoute le 28/08 pour diagnostiquer un 400 est reste vide
            # depuis, y compris sur le 400 du 30/08 avec piece jointe. Il faut
            # lire le corps d'abord.
            detail = ""
            with contextlib.suppress(Exception):
                await e.response.aread()
                detail = e.response.text[:500]
            logger.error(
                f"{type(self).__name__} API error: {e.response.status_code} {detail}"
            )
            yield StreamEvent(
                type="error",
                content=message_erreur_http(
                    self.config.provider, e.response.status_code
                ),
            )
        except Exception as e:
            logger.error(f"{type(self).__name__} streaming error: {e}")
            # Revue 0.48 p2 (F1) : jamais str(e) brut dans un évènement
            # relayé à l'écran - le détail vit dans le log ci-dessus. La forme
            # dit la CLASSE d'erreur : une panne de transport ouvre le circuit
            # (_is_provider_outage matche « réseau »), un bug local jamais.
            if isinstance(e, httpx.TransportError):
                yield StreamEvent(
                    type="error",
                    content=f"Erreur réseau vers le service d'IA ({type(e).__name__})",
                )
            else:
                yield StreamEvent(
                    type="error",
                    content=f"Erreur interne du service d'IA ({type(e).__name__})",
                )

    async def continue_with_tool_results(
        self,
        system_prompt: str | None,
        messages: list[dict],
        assistant_content: str,
        tool_calls: list[ToolCall],
        tool_results: list[ToolResult],
        tools: list[dict] | None = None,
        prior_turns: list[ToolTurn] | None = None,
        assistant_content_brut: "list[Any] | None" = None,
    ) -> AsyncGenerator[StreamEvent, None]:
        """Continue OpenAI conversation with tool results."""
        messages = list(messages)  # copie
        # Multi-tours (bug lcjp 11/06/2026) : rejouer les tours précédents
        # avant le tour courant, sinon le modèle re-demande le même outil.
        for turn in prior_turns or []:
            self._append_openai_tool_turn(
                messages,
                turn.assistant_content,
                turn.tool_calls,
                turn.tool_results,
                assistant_content_brut=turn.assistant_content_brut,
            )
        self._append_openai_tool_turn(
            messages,
            assistant_content,
            tool_calls,
            tool_results,
            assistant_content_brut=assistant_content_brut,
        )

        async for event in self.stream(system_prompt, messages, tools):
            yield event
