"""
THÉRÈSE v2 - Calculateurs - Router

API endpoints pour les calculateurs financiers et décisionnels.
"""

import logging

from app.models.schemas_calculators import (
    BreakEvenRequest,
    BreakEvenResponse,
    ICERequest,
    ICEResponse,
    NPVRequest,
    NPVResponse,
    RICERequest,
    RICEResponse,
    ROIRequest,
    ROIResponse,
)
from app.services.calculators import get_calculator_service
from fastapi import APIRouter, HTTPException

logger = logging.getLogger(__name__)

router = APIRouter()


# Endpoints

@router.post("/roi", response_model=ROIResponse)
async def calculate_roi(request: ROIRequest):
    """
    Calcule le Return on Investment (ROI).

    ROI = (Gain - Investissement) / Investissement × 100

    Exemple:
    - Investissement: 10000€
    - Gain: 15000€
    - ROI: 50%
    """
    service = get_calculator_service()
    try:
        result = service.calculate_roi(request.investment, request.gain)
        return ROIResponse(
            investment=result.investment,
            gain=result.gain,
            roi_percent=result.roi_percent,
            profit=result.profit,
            interpretation=result.interpretation,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/ice", response_model=ICEResponse)
async def calculate_ice(request: ICERequest):
    """
    Calcule le score ICE (Impact, Confidence, Ease).

    Score ICE = Impact × Confidence × Ease
    Échelle 1-10 pour chaque critère.

    Exemple:
    - Impact: 8/10
    - Confidence: 7/10
    - Ease: 6/10
    - Score: 336/1000
    """
    service = get_calculator_service()
    try:
        result = service.calculate_ice(request.impact, request.confidence, request.ease)
        return ICEResponse(
            impact=result.impact,
            confidence=result.confidence,
            ease=result.ease,
            score=result.score,
            interpretation=result.interpretation,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/rice", response_model=RICEResponse)
async def calculate_rice(request: RICERequest):
    """
    Calcule le score RICE (Reach, Impact, Confidence, Effort).

    Score RICE = (Reach × Impact × Confidence) / Effort

    Impact scale:
    - 0.25 = Minimal
    - 0.5 = Low
    - 1 = Medium
    - 2 = High
    - 3 = Massive

    Exemple:
    - Reach: 1000 users/quarter
    - Impact: 2 (high)
    - Confidence: 80%
    - Effort: 2 person-months
    - Score: 800
    """
    service = get_calculator_service()
    try:
        result = service.calculate_rice(
            request.reach, request.impact, request.confidence, request.effort
        )
        return RICEResponse(
            reach=result.reach,
            impact=result.impact,
            confidence=result.confidence,
            effort=result.effort,
            score=result.score,
            interpretation=result.interpretation,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/npv", response_model=NPVResponse)
async def calculate_npv(request: NPVRequest):
    """
    Calcule la Valeur Actuelle Nette (NPV/VAN).

    NPV = -Investment + Σ (CF_t / (1 + r)^t)

    Exemple:
    - Investissement: 100000€
    - Cash flows: [30000, 40000, 50000, 60000]
    - Taux: 10%
    - NPV: 34282€
    """
    service = get_calculator_service()
    try:
        result = service.calculate_npv(
            request.initial_investment, request.cash_flows, request.discount_rate
        )
        return NPVResponse(
            initial_investment=result.initial_investment,
            cash_flows=result.cash_flows,
            discount_rate=result.discount_rate,
            npv=result.npv,
            interpretation=result.interpretation,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/break-even", response_model=BreakEvenResponse)
async def calculate_break_even(request: BreakEvenRequest):
    """
    Calcule le seuil de rentabilité (break-even point).

    Break-even = Coûts fixes / (Prix unitaire - Coût variable unitaire)

    Exemple:
    - Coûts fixes: 50000€
    - Coût variable/unité: 20€
    - Prix/unité: 50€
    - Break-even: 1667 unités
    """
    service = get_calculator_service()
    try:
        result = service.calculate_break_even(
            request.fixed_costs, request.variable_cost_per_unit, request.price_per_unit
        )
        return BreakEvenResponse(
            fixed_costs=result.fixed_costs,
            variable_cost_per_unit=result.variable_cost_per_unit,
            price_per_unit=result.price_per_unit,
            break_even_units=result.break_even_units,
            break_even_revenue=result.break_even_revenue,
            interpretation=result.interpretation,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/help")
async def get_calculators_help():
    """
    Liste tous les calculateurs disponibles avec leurs descriptions.
    """
    return {
        "calculators": [
            {
                "name": "ROI",
                "endpoint": "/api/calc/roi",
                "description": "Return on Investment - Mesure le rendement d'un investissement",
                "formula": "(Gain - Investissement) / Investissement × 100",
                "params": ["investment", "gain"],
            },
            {
                "name": "ICE",
                "endpoint": "/api/calc/ice",
                "description": "Impact, Confidence, Ease - Score de priorisation",
                "formula": "Impact × Confidence × Ease",
                "params": ["impact (1-10)", "confidence (1-10)", "ease (1-10)"],
            },
            {
                "name": "RICE",
                "endpoint": "/api/calc/rice",
                "description": "Reach, Impact, Confidence, Effort - Score de priorisation produit",
                "formula": "(Reach × Impact × Confidence%) / Effort",
                "params": ["reach", "impact", "confidence (%)", "effort (person-months)"],
            },
            {
                "name": "NPV",
                "endpoint": "/api/calc/npv",
                "description": "Net Present Value - Valeur actuelle nette d'un projet",
                "formula": "-Investment + Σ (CF_t / (1 + r)^t)",
                "params": ["initial_investment", "cash_flows[]", "discount_rate"],
            },
            {
                "name": "Break-even",
                "endpoint": "/api/calc/break-even",
                "description": "Seuil de rentabilité - Quantité minimum pour être rentable",
                "formula": "Coûts fixes / (Prix - Coût variable)",
                "params": ["fixed_costs", "variable_cost_per_unit", "price_per_unit"],
            },
        ]
    }
