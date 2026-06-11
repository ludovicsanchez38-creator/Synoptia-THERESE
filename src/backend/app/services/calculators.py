"""
THÉRÈSE v2 - Calculateurs financiers et décisionnels

Outils de calcul pour les entrepreneurs :
- ROI (Return on Investment)
- ICE (Impact, Confidence, Ease)
- RICE (Reach, Impact, Confidence, Effort)
- NPV (Net Present Value)
- Break-even
"""

import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class ROIResult:
    """Résultat d'un calcul de ROI."""
    investment: float
    gain: float
    roi_percent: float
    profit: float
    interpretation: str


@dataclass
class ICEResult:
    """Résultat d'un score ICE."""
    impact: float
    confidence: float
    ease: float
    score: float
    interpretation: str


@dataclass
class RICEResult:
    """Résultat d'un score RICE."""
    reach: float
    impact: float
    confidence: float
    effort: float
    score: float
    interpretation: str


@dataclass
class NPVResult:
    """Résultat d'un calcul NPV."""
    initial_investment: float
    cash_flows: list[float]
    discount_rate: float
    npv: float
    interpretation: str


@dataclass
class BreakEvenResult:
    """Résultat d'un calcul de seuil de rentabilité."""
    fixed_costs: float
    variable_cost_per_unit: float
    price_per_unit: float
    break_even_units: float
    break_even_revenue: float
    interpretation: str


class CalculatorService:
    """Service de calculs financiers et décisionnels."""

    def calculate_roi(
        self,
        investment: float,
        gain: float,
    ) -> ROIResult:
        """
        Calcule le Return on Investment (ROI).

        ROI = (Gain - Investissement) / Investissement × 100

        Args:
            investment: Montant investi (en euros)
            gain: Gain total obtenu (en euros)

        Returns:
            ROIResult avec le pourcentage de ROI et interprétation
        """
        if investment <= 0:
            raise ValueError("L'investissement doit être positif")

        profit = gain - investment
        roi_percent = (profit / investment) * 100

        # Interprétation
        if roi_percent >= 100:
            interpretation = f"🚀 Excellent ! Tu as doublé ton investissement (+{roi_percent:.1f}%)"
        elif roi_percent >= 50:
            interpretation = f"✅ Très bon ROI de {roi_percent:.1f}%. L'investissement est rentable."
        elif roi_percent >= 20:
            interpretation = f"👍 ROI correct de {roi_percent:.1f}%. Investissement rentable."
        elif roi_percent >= 0:
            interpretation = f"⚠️ ROI faible de {roi_percent:.1f}%. Rentable mais marginal."
        else:
            interpretation = f"❌ ROI négatif de {roi_percent:.1f}%. Perte de {abs(profit):.2f}€"

        return ROIResult(
            investment=investment,
            gain=gain,
            roi_percent=roi_percent,
            profit=profit,
            interpretation=interpretation,
        )

    def calculate_ice(
        self,
        impact: float,
        confidence: float,
        ease: float,
    ) -> ICEResult:
        """
        Calcule le score ICE (Impact, Confidence, Ease).

        Score ICE = Impact × Confidence × Ease
        Échelle 1-10 pour chaque critère.

        Args:
            impact: Impact potentiel (1-10)
            confidence: Confiance dans l'estimation (1-10)
            ease: Facilité de mise en œuvre (1-10)

        Returns:
            ICEResult avec le score et interprétation
        """
        # Validation
        for name, value in [("impact", impact), ("confidence", confidence), ("ease", ease)]:
            if not 1 <= value <= 10:
                raise ValueError(f"{name} doit être entre 1 et 10")

        score = impact * confidence * ease

        # Interprétation (score max = 1000)
        if score >= 500:
            interpretation = f"🚀 Score ICE excellent ({score:.0f}/1000). Priorité haute !"
        elif score >= 300:
            interpretation = f"✅ Bon score ICE ({score:.0f}/1000). À considérer sérieusement."
        elif score >= 150:
            interpretation = f"👍 Score ICE moyen ({score:.0f}/1000). Peut-être intéressant."
        elif score >= 50:
            interpretation = f"⚠️ Score ICE faible ({score:.0f}/1000). Peu prioritaire."
        else:
            interpretation = f"❌ Score ICE très faible ({score:.0f}/1000). À éviter."

        return ICEResult(
            impact=impact,
            confidence=confidence,
            ease=ease,
            score=score,
            interpretation=interpretation,
        )

    def calculate_rice(
        self,
        reach: float,
        impact: float,
        confidence: float,
        effort: float,
    ) -> RICEResult:
        """
        Calcule le score RICE (Reach, Impact, Confidence, Effort).

        Score RICE = (Reach × Impact × Confidence) / Effort

        Args:
            reach: Nombre de personnes/clients touchés par trimestre
            impact: Impact (0.25=minimal, 0.5=faible, 1=moyen, 2=haut, 3=massif)
            confidence: Confiance en % (20%, 50%, 80%, 100%)
            effort: Effort en personnes-mois

        Returns:
            RICEResult avec le score et interprétation
        """
        if effort <= 0:
            raise ValueError("L'effort doit être positif")
        if not 0 <= confidence <= 100:
            raise ValueError("La confiance doit être entre 0 et 100%")

        # Convertir confidence en décimal
        conf_decimal = confidence / 100
        score = (reach * impact * conf_decimal) / effort

        # Interprétation
        if score >= 100:
            interpretation = f"🚀 Score RICE exceptionnel ({score:.1f}). Priorité absolue !"
        elif score >= 50:
            interpretation = f"✅ Très bon score RICE ({score:.1f}). Haute priorité."
        elif score >= 20:
            interpretation = f"👍 Score RICE correct ({score:.1f}). Priorité moyenne."
        elif score >= 5:
            interpretation = f"⚠️ Score RICE faible ({score:.1f}). Basse priorité."
        else:
            interpretation = f"❌ Score RICE très faible ({score:.1f}). À reconsidérer."

        return RICEResult(
            reach=reach,
            impact=impact,
            confidence=confidence,
            effort=effort,
            score=score,
            interpretation=interpretation,
        )

    def calculate_npv(
        self,
        initial_investment: float,
        cash_flows: list[float],
        discount_rate: float,
    ) -> NPVResult:
        """
        Calcule la Valeur Actuelle Nette (NPV/VAN).

        NPV = -Investment + Σ (CF_t / (1 + r)^t)

        Args:
            initial_investment: Investissement initial (positif)
            cash_flows: Liste des flux de trésorerie par période
            discount_rate: Taux d'actualisation annuel (ex: 0.10 pour 10%)

        Returns:
            NPVResult avec la VAN et interprétation
        """
        if initial_investment < 0:
            raise ValueError("L'investissement initial doit être positif")
        if discount_rate < 0:
            raise ValueError("Le taux d'actualisation doit être positif")
        if not cash_flows:
            raise ValueError("Au moins un flux de trésorerie requis")

        # Calcul NPV
        npv = -initial_investment
        for t, cf in enumerate(cash_flows, start=1):
            npv += cf / ((1 + discount_rate) ** t)

        # Interprétation
        if npv > 0:
            interpretation = f"✅ NPV positive ({npv:,.2f}€). L'investissement crée de la valeur."
        elif npv == 0:
            interpretation = "⚠️ NPV nulle. L'investissement atteint juste le seuil de rentabilité."
        else:
            interpretation = f"❌ NPV négative ({npv:,.2f}€). L'investissement détruit de la valeur."

        return NPVResult(
            initial_investment=initial_investment,
            cash_flows=cash_flows,
            discount_rate=discount_rate,
            npv=npv,
            interpretation=interpretation,
        )

    def calculate_break_even(
        self,
        fixed_costs: float,
        variable_cost_per_unit: float,
        price_per_unit: float,
    ) -> BreakEvenResult:
        """
        Calcule le seuil de rentabilité (break-even point).

        Break-even = Coûts fixes / (Prix unitaire - Coût variable unitaire)

        Args:
            fixed_costs: Coûts fixes totaux
            variable_cost_per_unit: Coût variable par unité
            price_per_unit: Prix de vente par unité

        Returns:
            BreakEvenResult avec le seuil et interprétation
        """
        if price_per_unit <= variable_cost_per_unit:
            raise ValueError("Le prix doit être supérieur au coût variable")
        if fixed_costs < 0:
            raise ValueError("Les coûts fixes doivent être positifs")

        margin_per_unit = price_per_unit - variable_cost_per_unit
        break_even_units = fixed_costs / margin_per_unit
        break_even_revenue = break_even_units * price_per_unit

        interpretation = (
            f"📊 Seuil de rentabilité : {break_even_units:.0f} unités\n"
            f"💰 CA minimum : {break_even_revenue:,.2f}€\n"
            f"📈 Marge par unité : {margin_per_unit:.2f}€"
        )

        return BreakEvenResult(
            fixed_costs=fixed_costs,
            variable_cost_per_unit=variable_cost_per_unit,
            price_per_unit=price_per_unit,
            break_even_units=break_even_units,
            break_even_revenue=break_even_revenue,
            interpretation=interpretation,
        )


# Singleton instance
_calculator_service: CalculatorService | None = None


def get_calculator_service() -> CalculatorService:
    """Get or create the calculator service singleton."""
    global _calculator_service
    if _calculator_service is None:
        _calculator_service = CalculatorService()
    return _calculator_service
