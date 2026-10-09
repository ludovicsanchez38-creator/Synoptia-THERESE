"""
THERESE v2 - Token Tracker Service

US-ESC-01 to US-ESC-05: Token tracking, cost estimation, and limits.
"""

import json
import logging
import os
from collections import deque
from dataclasses import dataclass
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class PalierTarif:
    """Un palier de longueur, appliqué à toute la requête.

    Mécanisme unique des lots M1 et M2. Les nombres ne sont écrits qu'ici.

    Couple absolu (Haiku 5.5, Grok 4.7) : ``entree`` et ``sortie``
    (USD / 1M) remplacent le tarif court. ``inclus`` vrai : le seuil
    compte (Grok 4.7, « dès 200 000 »). ``inclus`` faux : le palier
    commence au jeton suivant (Haiku 5.5, « au-delà de 100 000 »).

    Multiplicateurs (gpt-6.1-sol) : ``multiplicateur_entree`` et
    ``multiplicateur_sortie`` s'appliquent au tarif court quand
    ``entree`` est absent. Le seuil est exclusif (« plus de 272 000 »).
    ``seuil_entree`` est le nom lu par le lot M2.

    Plusieurs paliers se lisent du seuil le plus bas au plus haut :
    le dernier franchi l'emporte. ``PALIERS_TARIF`` en porte un par
    modèle. ``PALIERS_PROMPT`` est la même donnée lue comme une suite.
    """

    seuil_entree: int
    multiplicateur_entree: float = 1.0
    multiplicateur_sortie: float = 1.0
    inclus: bool = False
    entree: float | None = None
    sortie: float | None = None
    source: str = ""

    @property
    def seuil(self) -> int:
        """Même entier que ``seuil_entree`` (lecture du lot M1)."""
        return self.seuil_entree


@dataclass(frozen=True)
class BasculeTarif:
    """Nouveau couple à partir d'un jour, inclus.

    TOKEN_PRICES garde le couple d'avant. ``debut`` vient de la grille.
    """

    entree: float
    sortie: float
    debut: date
    source: str


@dataclass(frozen=True)
class PromotionTarif:
    """Tarif soldé entre deux dates. ``fin`` est exclusive.

    ``fin`` absente : aucune date de fin écrite, la promo reste.
    ``hypothese`` : la source ne publie pas cette heure de fin. ``lecture``
    dit comment elle a été retenue. Le tarif publié est à revérifier
    au basculement.
    """

    entree: float
    sortie: float
    debut: date
    fin: date | None
    source: str
    hypothese: bool = False
    lecture: str = ""


logger = logging.getLogger(__name__)


# ============================================================
# Token Pricing (USD per 1M tokens, January 2026)
# ============================================================

TOKEN_PRICES = {
    # Anthropic (juin 2026) - USD / 1M tokens
    # Frontiers 0.48, relevés aux sources officielles le 25/08/2026
    # (platform.claude.com/docs, developers.openai.com, ai.google.dev,
    # docs.mistral.ai/inference/pricing, docs.x.ai) - panel de revue :
    # un frontier absent d'ici affiche un coût menti à 0,00.
    # Cycle 6 (D184, relevé platform.claude.com/docs/en/about-claude/pricing le 10/09/2026)
    "claude-fable-5": {"input": 10.00, "output": 50.00},
    "claude-sonnet-5": {"input": 2.00, "output": 10.00},
    # M1, 09/10/2026 (platform.claude.com, vues d'ensemble). Haiku : ce
    # couple est le palier court (<= 100 k). Au-delà, PALIERS_TARIF.
    "claude-fable-5-1": {"input": 10.00, "output": 50.00},
    "claude-sonnet-5-5": {"input": 2.00, "output": 10.00},
    "claude-haiku-5-5": {"input": 0.10, "output": 0.50},
    "claude-opus-4-7": {"input": 5.00, "output": 25.00},
    "claude-opus-4-6": {"input": 5.00, "output": 25.00},
    "claude-opus-5": {"input": 5.00, "output": 25.00},
    # P-122 : relevé platform.claude.com/docs/en/about-claude/models/overview le 25/09/2026.
    "claude-opus-5-5": {"input": 4.00, "output": 20.00},
    "claude-opus-4-8": {"input": 5.00, "output": 25.00},
    "claude-sonnet-4-6": {"input": 3.00, "output": 15.00},
    "claude-haiku-4-5-20251001": {"input": 1.00, "output": 5.00},
    # OpenAI (juin 2026 ; gpt-6-astra relevé developers.openai.com/api/docs/pricing le 10/09/2026, standard, contexte court)
    "gpt-6-astra": {"input": 10.00, "output": 50.00},
    # P-122 : relevé developers.openai.com/api/docs/pricing le 25/09/2026 (standard, contexte court).
    "gpt-6-sol": {"input": 2.00, "output": 10.00},
    "gpt-6-luna": {"input": 0.10, "output": 0.50},
    # gpt-6.1-sol : fiche developers.openai.com/api/docs/models/gpt-6.1-sol
    # le 09/10/2026, tarif texte standard (2 $ / 10 $). Le palier >272k est
    # dans PALIERS_TARIF. Cache, Fast, Flex, Batch, Ultrafast et régional
    # ne sont pas ici.
    "gpt-6.1-sol": {"input": 2.00, "output": 10.00},
    "gpt-5.6-sol": {"input": 4.00, "output": 20.00},
    "gpt-5.6-terra": {"input": 2.00, "output": 12.00},
    "gpt-5.6-luna": {"input": 0.20, "output": 1.20},
    "gpt-5.5": {"input": 5.00, "output": 30.00},
    "gpt-5.5-pro": {"input": 30.00, "output": 180.00},
    "gpt-5.4": {"input": 2.50, "output": 15.00},
    "gpt-5.4-mini": {"input": 0.75, "output": 4.50},
    "gpt-5.3-codex": {"input": 1.75, "output": 14.00},
    # Gemini (juin 2026)
    # Tarif en vigueur jusqu'au 31/12/2026. Dès le 01/01/2027 inclus,
    # BASCULES_TARIF applique 1,50 / 7,50 (grille officielle).
    "gemini-3.7-flash": {"input": 0.75, "output": 3.75},
    # M1, 09/10/2026 : couple payant d'avant la bascule. Dès le 01/01/2027
    # inclus, BASCULES_TARIF applique 1,50 / 7,50 (grille officielle).
    "gemini-3.8-flash": {"input": 0.75, "output": 3.75},
    # Cycle 6 (D184, relevé ai.google.dev/gemini-api/docs/pricing le 10/09/2026, prompts <= 200k)
    "gemini-3.6-flash": {"input": 0.75, "output": 3.75},
    "gemini-3.5-flash-lite": {"input": 0.30, "output": 2.50},
    "gemini-2.5-pro": {"input": 1.25, "output": 10.00},
    "gemini-2.5-flash": {"input": 0.30, "output": 2.50},
    "gemini-3.1-pro-preview": {"input": 2.00, "output": 12.00},
    "gemini-3.5-flash": {"input": 1.50, "output": 9.00},
    "gemini-3.1-flash-lite": {"input": 0.25, "output": 1.50},
    # Mistral (alias evergreen)
    "mistral-medium-3-5": {"input": 1.50, "output": 7.50},
    # M1 : tarif barré, hors promotion. Le soldé vit dans PROMOTIONS.
    "mistral-large-4": {"input": 1.36, "output": 4.18},
    # Cycle 6 (D184, relevé docs.mistral.ai/inference/pricing le 10/09/2026)
    "mistral-medium-latest": {"input": 1.50, "output": 7.50},
    "mistral-large-2512": {"input": 0.50, "output": 1.50},
    "mistral-small-2603": {"input": 0.15, "output": 0.60},
    "codestral-2508": {"input": 0.30, "output": 0.90},
    "ministral-8b-2512": {"input": 0.15, "output": 0.15},
    "ministral-3b-2512": {"input": 0.10, "output": 0.10},
    "mistral-large-latest": {"input": 2.00, "output": 6.00},
    "codestral-latest": {"input": 0.30, "output": 0.90},
    "mistral-small-latest": {"input": 0.20, "output": 0.60},
    # Grok (juin 2026)
    # < 200k tokens de prompt (le cas Board/chat)
    "grok-4.6": {"input": 2.00, "output": 6.00},
    # M1 : couple court (< 200 k). Dès 200 k, PALIERS_TARIF applique 4 / 12.
    "grok-4.7": {"input": 2.00, "output": 6.00},
    "grok-4.5": {"input": 2.00, "output": 6.00},  # relevé docs.x.ai/docs/models le 10/09/2026 (< 200k)
    "grok-4.3": {"input": 1.25, "output": 2.50},
    "grok-4.20-0309-reasoning": {"input": 1.25, "output": 2.50},
    "grok-4.20-0309-non-reasoning": {"input": 1.25, "output": 2.50},
    # DeepSeek (juin 2026)
    "deepseek-v4-pro": {"input": 0.435, "output": 0.87},
    "deepseek-v4-flash": {"input": 0.14, "output": 0.28},
    # Ollama (local, no cost) + fallback
    "default": {"input": 0.0, "output": 0.0},
}

# Paliers de longueur. Un seul registre : couple absolu ou multiplicateurs.
# Fiches du 09/10/2026. Le dernier seuil franchi l'emporte.
PALIERS_TARIF: dict[str, PalierTarif] = {
    "claude-haiku-5-5": PalierTarif(
        seuil_entree=100_000,
        inclus=False,
        entree=0.50,
        sortie=2.50,
        source="https://platform.claude.com/docs/en/models/haiku-5-5/overview",
    ),
    "grok-4.7": PalierTarif(
        seuil_entree=200_000,
        inclus=True,
        entree=4.00,
        sortie=12.00,
        source="https://docs.x.ai/developers/pricing",
    ),
    # gpt-6.1-sol : au-delà de 272 000 jetons d'entrée, 2× l'entrée et
    # 1,5× la sortie, sur toute la requête.
    "gpt-6.1-sol": PalierTarif(
        seuil_entree=272_000,
        multiplicateur_entree=2.0,
        multiplicateur_sortie=1.5,
        source="https://developers.openai.com/api/docs/models/gpt-6.1-sol",
    ),
}

# Même registre, lu comme une suite (le lot M1 indexe ``[0]``).
PALIERS_PROMPT: dict[str, tuple[PalierTarif, ...]] = {
    cle: (palier,) for cle, palier in PALIERS_TARIF.items()
}


# Bascules datées. ``debut`` inclus. Le couple de TOKEN_PRICES est celui
# d'avant. Gemini 3.7 Flash et 3.8 Flash : la grille annonce 1,50 / 7,50
# dès le 1er janvier 2027 (0,75 / 3,75 jusqu'au 31 décembre 2026).
# Source : https://ai.google.dev/gemini-api/docs/pricing
BASCULES_TARIF: dict[str, BasculeTarif] = {
    "gemini-3.8-flash": BasculeTarif(
        entree=1.50,
        sortie=7.50,
        debut=date(2027, 1, 1),
        source="https://ai.google.dev/gemini-api/docs/pricing",
    ),
    "gemini-3.7-flash": BasculeTarif(
        entree=1.50,
        sortie=7.50,
        debut=date(2027, 1, 1),
        source="https://ai.google.dev/gemini-api/docs/pricing",
    ),
}


# Promotions datées. ``fin`` exclusive. None : pas de date de fin écrite.
# Mistral Large 4 : le changelog du 6 octobre 2026 dit « deux semaines à
# partir du 6 octobre » et n'écrit ni jour calendaire ni heure de fin.
# Hypothèse de lecture, pas une heure publiée : du 6 octobre 2026 inclus
# au 20 octobre 2026 à 00 h UTC exclu (quatorze jours). À revérifier sur
# le tarif publié au basculement. Les montants soldés ne changent pas.
PROMOTIONS: dict[str, PromotionTarif] = {
    "mistral-large-4": PromotionTarif(
        entree=0.68,
        sortie=2.09,
        debut=date(2026, 10, 6),
        fin=date(2026, 10, 20),
        source="https://docs.mistral.ai/resources/changelogs",
        hypothese=True,
        lecture=(
            "Hypothèse de lecture : le changelog dit « deux semaines » à partir "
            "du 6 octobre 2026, sans heure de fin. On retient le 20 octobre 2026 "
            "à 00 h UTC, fin exclusive. À revérifier sur le tarif publié au basculement."
        ),
    ),
}


# ============================================================
# US-ESC-03: Token Limits
# ============================================================


@dataclass
class TokenLimits:
    """Token limit configuration."""

    # Per-message limits
    max_input_tokens: int = 8000
    max_output_tokens: int = 4000

    # Daily limits
    daily_input_limit: int = 500000  # 500K tokens/day
    daily_output_limit: int = 100000  # 100K tokens/day

    # Plafond mensuel, en USD (tarifs fournisseurs en dollars ; le nom du
    # champ reste historique - dette de renommage actée en 0.48.1)
    monthly_budget_eur: float = 50.0

    # Warnings
    warn_at_percentage: int = 80  # Warn when usage reaches 80%

    def to_dict(self) -> dict[str, Any]:
        return {
            "max_input_tokens": self.max_input_tokens,
            "max_output_tokens": self.max_output_tokens,
            "daily_input_limit": self.daily_input_limit,
            "daily_output_limit": self.daily_output_limit,
            "monthly_budget_eur": self.monthly_budget_eur,
            "warn_at_percentage": self.warn_at_percentage,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "TokenLimits":
        return cls(
            max_input_tokens=data.get("max_input_tokens", 8000),
            max_output_tokens=data.get("max_output_tokens", 4000),
            daily_input_limit=data.get("daily_input_limit", 500000),
            daily_output_limit=data.get("daily_output_limit", 100000),
            monthly_budget_eur=data.get("monthly_budget_eur", 50.0),
            warn_at_percentage=data.get("warn_at_percentage", 80),
        )


# ============================================================
# US-ESC-02/04: Token Usage Record
# ============================================================


@dataclass
class TokenUsageRecord:
    """Record of token usage for a single request."""

    timestamp: datetime
    conversation_id: str
    model: str
    provider: str
    input_tokens: int
    output_tokens: int
    cost_eur: float
    context_truncated: bool = False
    truncated_messages: int = 0

    def to_dict(self) -> dict:
        return {
            "timestamp": self.timestamp.isoformat(),
            "conversation_id": self.conversation_id,
            "model": self.model,
            "provider": self.provider,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "cost_eur": self.cost_eur,
            "context_truncated": self.context_truncated,
            "truncated_messages": self.truncated_messages,
        }


# ============================================================
# Token Tracker Service
# ============================================================


class TokenTracker:
    """
    Singleton service for tracking token usage and costs.

    Provides:
    - Real-time cost estimation (US-ESC-02)
    - Token limit enforcement (US-ESC-03)
    - Usage history (US-ESC-04)
    - Context truncation alerts (US-ESC-05)
    """

    _instance: "TokenTracker | None" = None

    def __new__(cls) -> "TokenTracker":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True

        # Usage history (keep last 1000 records)
        self._usage_history: deque[TokenUsageRecord] = deque(maxlen=1000)

        # Daily counters
        self._today_input: int = 0
        self._today_output: int = 0
        self._today_cost: float = 0.0
        self._today_date: str = datetime.now(UTC).strftime("%Y-%m-%d")

        # Monthly counters
        self._month_input: int = 0
        self._month_output: int = 0
        self._month_cost: float = 0.0
        self._current_month: str = datetime.now(UTC).strftime("%Y-%m")

        # B-500 (05/09/2026) : ces compteurs ne vivaient qu'en mémoire ; le
        # plafond mensuel s'appliquait à un compteur remis à zéro à chaque
        # lancement. Relus depuis le disque au démarrage, écrits à chaque usage.
        self._charger_depuis_le_disque()

        # Limits
        self._limits = TokenLimits()
        # B-582 : les plafonds enregistrés (Paramètres > Limites) n'étaient lus
        # qu'à l'ouverture de l'onglet ; le chat appliquait le défaut jusque-là.
        self._limites_chargees = False

    def _charger_limites_si_besoin(self) -> None:
        if self._limites_chargees:
            return
        try:
            from app.models.database import get_sync_connection
            from sqlalchemy import text

            with get_sync_connection() as conn:
                row = conn.execute(
                    text("SELECT value FROM preferences WHERE key = :key"), {"key": "token_limits"}
                ).fetchone()
            if row and row[0]:
                self._limits = TokenLimits.from_dict(json.loads(row[0]))
                logger.info(f"[TOKEN] Limits loaded from DB: {self._limits.to_dict()}")
            # Cycle 6 : le drapeau ne se pose qu'après une lecture réussie ; un
            # échec (base verrouillée) figeait les défauts jusqu'au redémarrage.
            self._limites_chargees = True
        except Exception as e:
            logger.debug("Plafonds non relus depuis la base : %s", e)

    def set_limits(self, limits: TokenLimits) -> None:
        """Set token limits."""
        self._limites_chargees = True
        self._limits = limits
        logger.info(f"[TOKEN] Limits updated: {limits.to_dict()}")

    def get_limits(self) -> TokenLimits:
        """Get current token limits."""
        self._charger_limites_si_besoin()
        return self._limits

    def _reset_daily_if_needed(self) -> None:
        """Reset daily counters if date has changed."""
        today = datetime.now(UTC).strftime("%Y-%m-%d")
        if today != self._today_date:
            self._today_input = 0
            self._today_output = 0
            self._today_cost = 0.0
            self._today_date = today

    def _reset_monthly_if_needed(self) -> None:
        """Reset monthly counters if month has changed."""
        month = datetime.now(UTC).strftime("%Y-%m")
        if month != self._current_month:
            self._month_input = 0
            self._month_output = 0
            self._month_cost = 0.0
            self._current_month = month

    @staticmethod
    def _present_en_grille(nom: str) -> bool:
        return nom in TOKEN_PRICES or nom in PALIERS_TARIF or nom in PROMOTIONS

    def _cle_grille(self, model: str) -> str:
        """Identifiant de la grille, préfixe OpenRouter retiré s'il le faut."""
        if self._present_en_grille(model):
            return model
        if "/" in model:
            reste = model.split("/", 1)[1]
            if self._present_en_grille(reste):
                return reste
        return model

    def _prix_pour(self, model: str) -> dict[str, float] | None:
        """Cherche le tarif d'un modele dans la grille, sinon None.

        Recherche UNIQUE, partagee par `estimate_cost` et `tarif_connu`
        (B-190) : un drapeau calcule a part finirait par contredire le
        montant qu'il accompagne, notamment sur le prefixe OpenRouter.
        """
        return TOKEN_PRICES.get(self._cle_grille(model))

    def _tarif_pour(self, model: str, jetons_prompt: int) -> dict[str, float]:
        """Couple entrée/sortie applicable, palier de longueur compris.

        Le palier franchi remplace le couple court pour toute la requête.
        """
        cle = self._cle_grille(model)
        prix = self._appliquer_bascule(
            cle, TOKEN_PRICES.get(cle, TOKEN_PRICES["default"])
        )
        retenu = self._appliquer_promotion(cle, prix)
        for palier in PALIERS_PROMPT.get(cle, ()):
            franchi = (
                jetons_prompt >= palier.seuil_entree
                if palier.inclus
                else jetons_prompt > palier.seuil_entree
            )
            if not franchi:
                continue
            if palier.entree is not None and palier.sortie is not None:
                retenu = {"input": palier.entree, "output": palier.sortie}
            else:
                retenu = {
                    "input": retenu["input"] * palier.multiplicateur_entree,
                    "output": retenu["output"] * palier.multiplicateur_sortie,
                }
        return retenu

    def _appliquer_bascule(
        self, cle: str, prix: dict[str, float]
    ) -> dict[str, float]:
        """Remplace le couple à partir du jour annoncé, inclus."""
        bascule = BASCULES_TARIF.get(cle)
        if bascule is None or datetime.now(UTC).date() < bascule.debut:
            return prix
        return {"input": bascule.entree, "output": bascule.sortie}

    def _appliquer_promotion(
        self, cle: str, prix: dict[str, float]
    ) -> dict[str, float]:
        """Remplace le couple barré pendant la fenêtre, sinon le laisse."""
        promo = PROMOTIONS.get(cle)
        if promo is None:
            return prix
        jour = datetime.now(UTC).date()
        if jour < promo.debut:
            return prix
        if promo.fin is not None and jour >= promo.fin:
            return prix
        return {"input": promo.entree, "output": promo.sortie}

    def tarif_connu(self, model: str) -> bool:
        """Dit si la grille tarife vraiment ce modele (B-190).

        Sans ce drapeau, un modele absent de TOKEN_PRICES sortait a 0.0,
        indiscernable d'un modele local reellement gratuit : le garde-budget
        annoncait « gratuit » tout ce qu'il ignorait.
        """
        return self._prix_pour(model) is not None

    def estimate_cost(
        self,
        model: str,
        input_tokens: int,
        output_tokens: int,
    ) -> float:
        """
        Estimate cost for a request (US-ESC-02).

        Returns cost in USD (tarifs relevés en dollars chez tous les
        fournisseurs - le nom `cost_eur` des champs reste historique, cf.
        revue Soso 0.48.1 finding S2-4).
        """
        prices = self._tarif_pour(model, input_tokens)
        input_cost = (input_tokens / 1_000_000) * prices["input"]
        output_cost = (output_tokens / 1_000_000) * prices["output"]
        return input_cost + output_cost

    def cout_des_appels(
        self,
        model: str,
        appels: list[tuple[int, int]],
    ) -> float:
        """Somme des coûts, chaque appel avec sa propre longueur de prompt.

        Le palier porte sur une requête fournisseur, pas sur le total de
        plusieurs tours d'outils.
        """
        return sum(
            self.estimate_cost(model, entree, sortie) for entree, sortie in appels
        )

    def record_usage(
        self,
        conversation_id: str,
        model: str,
        provider: str,
        input_tokens: int,
        output_tokens: int,
        context_truncated: bool = False,
        truncated_messages: int = 0,
        appels: list[tuple[int, int]] | None = None,
    ) -> TokenUsageRecord:
        """
        Record token usage for a request (US-ESC-04).
        """
        self._reset_daily_if_needed()
        self._reset_monthly_if_needed()

        if appels:
            cost = self.cout_des_appels(model, appels)
        else:
            cost = self.estimate_cost(model, input_tokens, output_tokens)

        record = TokenUsageRecord(
            timestamp=datetime.now(UTC),
            conversation_id=conversation_id,
            model=model,
            provider=provider,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost_eur=cost,
            context_truncated=context_truncated,
            truncated_messages=truncated_messages,
        )

        self._usage_history.append(record)

        # Update counters
        self._today_input += input_tokens
        self._today_output += output_tokens
        self._today_cost += cost

        self._month_input += input_tokens
        self._month_output += output_tokens
        self._month_cost += cost
        self._sauver_sur_le_disque()

        logger.info(
            f"[TOKEN] Recorded: {input_tokens} in / {output_tokens} out "
            f"({cost:.4f} USD) - {model}"
        )

        return record

    def check_limits(
        self,
        input_tokens: int,
        output_tokens: int | None = None,
        model: str | None = None,
        *,
        local: bool = False,
        taille_message: int | None = None,
    ) -> dict:
        """
        Check if a request would exceed limits (US-ESC-03).

        Returns dict with status and any warnings/errors.

        B-482 / B-486 (05/09/2026, décision de Ludo) : un modèle hors grille
        tarifaire est SIGNALÉ (avertissement), pas compté à zéro en silence ;
        les deux contrôles de sortie (par message, par jour) existent enfin.
        `local` : un modèle local (Ollama) n'a pas de tarif, ce n'est pas un
        oubli de la grille.
        """
        self._charger_limites_si_besoin()
        self._reset_daily_if_needed()
        self._reset_monthly_if_needed()

        result: dict[str, Any] = {
            "allowed": True,
            "warnings": [],
            "errors": [],
        }

        if model and not local and not self.tarif_connu(model):
            result["warnings"].append(
                f"Modèle hors grille tarifaire ({model}) : son coût n'est pas compté "
                "dans le budget mensuel."
            )

        # Contrôles de sortie (B-486)
        if output_tokens:
            if output_tokens > self._limits.max_output_tokens:
                result["warnings"].append(
                    f"Sortie demandée ({output_tokens:,} tokens) au-delà du plafond par "
                    f"message ({self._limits.max_output_tokens:,})."
                )
            projected_daily_output = self._today_output + output_tokens
            daily_output_pct = (
                (projected_daily_output / self._limits.daily_output_limit * 100)
                if self._limits.daily_output_limit > 0
                else 0.0
            )
            if daily_output_pct >= 100:
                result["errors"].append(
                    f"Limite quotidienne de sortie atteinte: {projected_daily_output:,} tokens "
                    f"(limite: {self._limits.daily_output_limit:,})"
                )
                result["allowed"] = False
            elif daily_output_pct >= self._limits.warn_at_percentage:
                result["warnings"].append(
                    f"Sortie quotidienne: {daily_output_pct:.0f}% "
                    f"({projected_daily_output:,} / {self._limits.daily_output_limit:,} tokens)"
                )

        # Le plafond de taille vise le message, pas l'historique. Sans
        # taille séparée, on retombe sur l'entrée entière (budget, palier).
        jetons_message = input_tokens if taille_message is None else taille_message
        if jetons_message > self._limits.max_input_tokens:
            result["errors"].append(
                f"Message trop long: {jetons_message} tokens "
                f"(limite: {self._limits.max_input_tokens})"
            )
            result["allowed"] = False

        # Check daily limits
        projected_daily_input = self._today_input + input_tokens
        # Garde anti division par zero : une limite a 0 ne doit pas planter en 500 (rapport Syn 14/06)
        daily_input_pct = (projected_daily_input / self._limits.daily_input_limit * 100) if self._limits.daily_input_limit > 0 else 0.0

        if daily_input_pct >= 100:
            result["errors"].append(
                f"Limite quotidienne atteinte: {projected_daily_input:,} tokens "
                f"(limite: {self._limits.daily_input_limit:,})"
            )
            result["allowed"] = False
        elif daily_input_pct >= self._limits.warn_at_percentage:
            result["warnings"].append(
                f"Utilisation quotidienne: {daily_input_pct:.0f}% "
                f"({projected_daily_input:,} / {self._limits.daily_input_limit:,} tokens)"
            )

        # Check monthly budget
        # B-007 : le plafond ne pouvait jamais se declencher. Deux verrous
        # tenaient ici. (1) La projection etait calculee avec le modele
        # « default », dont TOKEN_PRICES dit 0,00 USD en entree comme en
        # sortie : elle valait TOUJOURS le cumul deja consomme, le cout de la
        # requete examinee ne pesait jamais rien. Le modele employe est
        # desormais celui que l'appelant annonce ; sans annonce on retombe
        # sur « default », c'est-a-dire sur l'ancien comportement, jamais sur
        # un tarif suppose. (2) Le bloc entier vivait sous `if output_tokens:`
        # et sautait des que la sortie etait absente ou nulle, alors que les
        # tokens d'ENTREE sont deja factures.
        estimated_cost = self.estimate_cost(
            model or "default", input_tokens, output_tokens or 0
        )
        projected_month_cost = self._month_cost + estimated_cost
        budget_pct = (projected_month_cost / self._limits.monthly_budget_eur * 100) if self._limits.monthly_budget_eur > 0 else 0.0

        if budget_pct >= 100:
            result["errors"].append(
                f"Budget mensuel atteint: {projected_month_cost:.2f} USD "
                f"(budget: {self._limits.monthly_budget_eur:.2f} USD)"
            )
            result["allowed"] = False
        elif budget_pct >= self._limits.warn_at_percentage:
            result["warnings"].append(
                f"Budget mensuel: {budget_pct:.0f}% "
                f"({projected_month_cost:.2f} / {self._limits.monthly_budget_eur:.2f} USD)"
            )

        return result

    def get_daily_usage(self) -> dict:
        """Get today's usage summary."""
        # Cycle 6 : ces lecteurs affichaient les plafonds par défaut tant
        # qu'aucun contrôle n'avait chargé ceux de la base.
        self._charger_limites_si_besoin()
        self._reset_daily_if_needed()

        return {
            "date": self._today_date,
            "input_tokens": self._today_input,
            "output_tokens": self._today_output,
            "total_tokens": self._today_input + self._today_output,
            "cost_eur": self._today_cost,
            "input_limit": self._limits.daily_input_limit,
            "output_limit": self._limits.daily_output_limit,
            "input_usage_pct": (self._today_input / self._limits.daily_input_limit * 100) if self._limits.daily_input_limit > 0 else 0.0,
            "output_usage_pct": (self._today_output / self._limits.daily_output_limit * 100) if self._limits.daily_output_limit > 0 else 0.0,
        }

    # ------------------------------------------------------------------
    # B-500 : persistance des compteurs
    # ------------------------------------------------------------------

    @staticmethod
    def _fichier_usage() -> Path:
        from app.config import settings

        return Path(settings.data_dir) / "token_usage.json"

    def _charger_depuis_le_disque(self) -> None:
        # Seul le singleton du processus persiste : un traceur isolé (tests,
        # object.__new__) ne lit ni n'écrit le fichier.
        if TokenTracker._instance is not self:
            return
        try:
            fichier = self._fichier_usage()
            if not fichier.exists():
                return
            charge = json.loads(fichier.read_text(encoding="utf-8"))
            if charge.get("today_date") == self._today_date:
                self._today_input = int(charge.get("today_input", 0))
                self._today_output = int(charge.get("today_output", 0))
                self._today_cost = float(charge.get("today_cost", 0.0))
            if charge.get("current_month") == self._current_month:
                self._month_input = int(charge.get("month_input", 0))
                self._month_output = int(charge.get("month_output", 0))
                self._month_cost = float(charge.get("month_cost", 0.0))
        except Exception as e:  # une persistance illisible ne bloque jamais l'usage
            logger.warning("Compteurs de jetons illisibles, repart de zéro : %s", e)

    def _sauver_sur_le_disque(self) -> None:
        if TokenTracker._instance is not self:
            return
        try:
            fichier = self._fichier_usage()
            fichier.parent.mkdir(parents=True, exist_ok=True)
            charge = {
                "today_date": self._today_date,
                "today_input": self._today_input,
                "today_output": self._today_output,
                "today_cost": self._today_cost,
                "current_month": self._current_month,
                "month_input": self._month_input,
                "month_output": self._month_output,
                "month_cost": self._month_cost,
            }
            temporaire = fichier.with_suffix(".json.tmp")
            temporaire.write_text(json.dumps(charge), encoding="utf-8")
            os.replace(temporaire, fichier)
        except Exception as e:
            logger.warning("Compteurs de jetons non sauvegardés : %s", e)

    def get_monthly_usage(self) -> dict:
        """Get this month's usage summary."""
        self._charger_limites_si_besoin()
        self._reset_monthly_if_needed()

        return {
            "month": self._current_month,
            "input_tokens": self._month_input,
            "output_tokens": self._month_output,
            "total_tokens": self._month_input + self._month_output,
            "cost_eur": self._month_cost,
            "budget_eur": self._limits.monthly_budget_eur,
            "budget_usage_pct": (self._month_cost / self._limits.monthly_budget_eur * 100) if self._limits.monthly_budget_eur > 0 else 0.0,
        }

    def get_usage_history(
        self,
        limit: int = 50,
        conversation_id: str | None = None,
    ) -> list[dict]:
        """
        Get usage history (US-ESC-04).

        Optionally filter by conversation.
        """
        records = list(self._usage_history)

        if conversation_id:
            records = [r for r in records if r.conversation_id == conversation_id]

        # Sort by timestamp descending
        records.sort(key=lambda r: r.timestamp, reverse=True)

        return [r.to_dict() for r in records[:limit]]

    def get_stats(self) -> dict:
        """Get overall token tracking stats."""
        return {
            "daily": self.get_daily_usage(),
            "monthly": self.get_monthly_usage(),
            "limits": self._limits.to_dict(),
            "history_count": len(self._usage_history),
        }


# Singleton accessor
_token_tracker: TokenTracker | None = None


def get_token_tracker() -> TokenTracker:
    """Get the token tracker singleton."""
    global _token_tracker
    if _token_tracker is None:
        _token_tracker = TokenTracker()
    return _token_tracker


# ============================================================
# US-ESC-01: Confidence/Uncertainty Detection
# ============================================================

# Phrases that indicate LLM uncertainty
UNCERTAINTY_PHRASES = [
    "je ne suis pas sur",
    "je ne suis pas certain",
    "il est possible que",
    "je pense que",
    "peut-etre",
    "probablement",
    "il semble que",
    "d'apres ce que je sais",
    "sous reserve",
    "je ne peux pas confirmer",
    "a ma connaissance",
    "i'm not sure",
    "i'm not certain",
    "it's possible that",
    "i think",
    "maybe",
    "probably",
    "it seems",
    "as far as i know",
    "i cannot confirm",
]


def _sans_accents(texte: str) -> str:
    """Replie les accents (« sûr » -> « sur ») pour une comparaison lexicale."""
    import unicodedata

    return "".join(
        c for c in unicodedata.normalize("NFKD", texte) if not unicodedata.combining(c)
    )


def detect_uncertainty(response: str) -> dict[str, Any]:
    """
    Detect if the LLM response indicates uncertainty (US-ESC-01).

    Returns dict with uncertainty indicators.

    B-496 (05/09/2026) : le vocabulaire est écrit sans accents et la
    comparaison était un simple `in` sur la réponse en minuscules. « je ne
    suis pas sûr » ne rencontrait jamais « je ne suis pas sur » : une réponse
    en français correct passait pour une certitude absolue. Les deux côtés
    sont repliés sur les accents avant comparaison.
    """
    lower_response = _sans_accents(response.lower())

    # Check for uncertainty phrases
    detected_phrases = []
    for phrase in UNCERTAINTY_PHRASES:
        if _sans_accents(phrase) in lower_response:
            detected_phrases.append(phrase)

    # Calculate confidence score (inverse of uncertainty)
    # More uncertainty phrases = lower confidence
    base_confidence = 100
    penalty_per_phrase = 15
    confidence_score = max(0, base_confidence - (len(detected_phrases) * penalty_per_phrase))

    # Classify confidence level
    if confidence_score >= 80:
        confidence_level = "high"
    elif confidence_score >= 50:
        confidence_level = "medium"
    else:
        confidence_level = "low"

    return {
        "is_uncertain": len(detected_phrases) > 0,
        "uncertainty_phrases": detected_phrases,
        "confidence_score": confidence_score,
        "confidence_level": confidence_level,
        "should_verify": confidence_level in ["low", "medium"] and len(detected_phrases) > 1,
    }


def enregistrer_usage_llm(
    llm_service: object,
    usage_sink: dict[str, int] | None,
    conversation_id: str,
    texte_entree: str = "",
    texte_sortie: str = "",
) -> TokenUsageRecord:
    """Compte un appel au modèle hors chat (atelier documentaire, skills).

    B-632 (persona Sophie, c4) : deux générations réelles de l'atelier ne
    laissaient aucune trace dans `token_usage.json`. Même convention que le
    chat : usage réel du fournisseur quand il est fourni, sinon estimation à
    deux jetons par mot.
    """
    usage = usage_sink or {}
    # Cycle 6 : un zéro réel du fournisseur est une mesure, pas une absence ;
    # `or` le remplaçait par l'estimation à deux jetons par mot.
    input_tokens = usage.get("input_tokens")
    if input_tokens is None:
        input_tokens = len(texte_entree.split()) * 2
    output_tokens = usage.get("output_tokens")
    if output_tokens is None:
        output_tokens = len(texte_sortie.split()) * 2
    modele = str(getattr(llm_service, "modele_effectif", None) or getattr(getattr(llm_service, "config", None), "model", "inconnu"))
    fournisseur = str(getattr(llm_service, "fournisseur_effectif", None) or getattr(getattr(getattr(llm_service, "config", None), "provider", None), "value", "inconnu"))
    return get_token_tracker().record_usage(
        conversation_id=conversation_id,
        model=modele,
        provider=fournisseur,
        input_tokens=int(input_tokens),
        output_tokens=int(output_tokens),
    )
