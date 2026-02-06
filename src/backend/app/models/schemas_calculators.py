"""
THÉRÈSE v2 - Schemas Calculateurs

Request/Response models pour les calculateurs financiers et décisionnels.
"""

from pydantic import BaseModel, Field

# ============================================================
# ROI
# ============================================================


class ROIRequest(BaseModel):
    """Requête pour calcul ROI."""

    investment: float = Field(..., gt=0, description="Montant investi (euros)")
    gain: float = Field(..., description="Gain total obtenu (euros)")


class ROIResponse(BaseModel):
    """Réponse calcul ROI."""

    investment: float
    gain: float
    roi_percent: float
    profit: float
    interpretation: str


# ============================================================
# ICE
# ============================================================


class ICERequest(BaseModel):
    """Requête pour score ICE."""

    impact: float = Field(..., ge=1, le=10, description="Impact potentiel (1-10)")
    confidence: float = Field(..., ge=1, le=10, description="Confiance (1-10)")
    ease: float = Field(..., ge=1, le=10, description="Facilité (1-10)")


class ICEResponse(BaseModel):
    """Réponse score ICE."""

    impact: float
    confidence: float
    ease: float
    score: float
    interpretation: str


# ============================================================
# RICE
# ============================================================


class RICERequest(BaseModel):
    """Requête pour score RICE."""

    reach: float = Field(..., gt=0, description="Nombre de personnes touchées/trimestre")
    impact: float = Field(
        ..., gt=0, description="Impact (0.25=min, 0.5=low, 1=med, 2=high, 3=massive)"
    )
    confidence: float = Field(..., ge=0, le=100, description="Confiance en %")
    effort: float = Field(..., gt=0, description="Effort en personnes-mois")


class RICEResponse(BaseModel):
    """Réponse score RICE."""

    reach: float
    impact: float
    confidence: float
    effort: float
    score: float
    interpretation: str


# ============================================================
# NPV (Valeur Actuelle Nette)
# ============================================================


class NPVRequest(BaseModel):
    """Requête pour calcul NPV."""

    initial_investment: float = Field(..., ge=0, description="Investissement initial")
    cash_flows: list[float] = Field(
        ..., min_length=1, description="Flux de trésorerie par période"
    )
    discount_rate: float = Field(
        ..., ge=0, le=1, description="Taux d'actualisation (ex: 0.10 pour 10%)"
    )


class NPVResponse(BaseModel):
    """Réponse calcul NPV."""

    initial_investment: float
    cash_flows: list[float]
    discount_rate: float
    npv: float
    interpretation: str


# ============================================================
# Break-Even (Seuil de rentabilité)
# ============================================================


class BreakEvenRequest(BaseModel):
    """Requête pour calcul break-even."""

    fixed_costs: float = Field(..., ge=0, description="Coûts fixes totaux")
    variable_cost_per_unit: float = Field(
        ..., ge=0, description="Coût variable par unité"
    )
    price_per_unit: float = Field(..., gt=0, description="Prix de vente par unité")


class BreakEvenResponse(BaseModel):
    """Réponse calcul break-even."""

    fixed_costs: float
    variable_cost_per_unit: float
    price_per_unit: float
    break_even_units: float
    break_even_revenue: float
    interpretation: str
