"""
THÉRÈSE v2 - Email Classifier

Classifie les emails par priorité (Rouge/Orange/Vert).
US-EMAIL-08, US-EMAIL-10
"""

from dataclasses import dataclass


@dataclass
class ClassificationResult:
    """Résultat de classification."""
    priority: str  # 'high' | 'medium' | 'low'
    score: int  # 0-100
    reason: str  # Explication


class EmailClassifier:
    """Classifie emails par priorité."""

    # Mots-clés urgents (rouge)
    URGENT_KEYWORDS = [
        'urgent', 'facture', 'paiement', 'échéance', 'deadline',
        'rappel', 'relance', 'impôt', 'dgfip', 'urssaf',
        'client', 'impayé', 'retard', 'action requise', 'dernier rappel'
    ]

    # Mots-clés importants (orange)
    IMPORTANT_KEYWORDS = [
        'proposition', 'devis', 'rendez-vous', 'meeting', 'réunion',
        'projet', 'contrat', 'signature', 'accord', 'partenariat'
    ]

    # Expéditeurs prioritaires (rouge)
    PRIORITY_SENDERS = [
        'indy.fr', 'impots.gouv.fr', 'urssaf.fr', 'dgfip',
        'tresor-public', 'notaire', 'avocat', 'huissier'
    ]

    # Expéditeurs newsletters (vert)
    NEWSLETTER_SENDERS = [
        'beehiiv.com', 'substack.com', 'mailchimp.com',
        'sendgrid.net', 'noreply', 'no-reply', 'newsletter'
    ]

    @staticmethod
    def classify(
        subject: str,
        from_email: str,
        snippet: str,
        labels: list[str],
        contact_score: int | None = None,
    ) -> ClassificationResult:
        """
        Classifie un email.

        Args:
            subject: Sujet de l'email
            from_email: Expéditeur
            snippet: Preview du contenu
            labels: Labels Gmail
            contact_score: Score du contact CRM (0-100)

        Returns:
            ClassificationResult avec priorité et raison
        """
        score = 0
        reasons = []

        # Texte complet pour analyse
        full_text = f"{subject} {snippet}".lower()
        from_email_lower = from_email.lower()

        # ============================================================
        # Critères URGENT (Rouge) - Score +30 à +50
        # ============================================================

        # Mots-clés urgents dans sujet/contenu
        urgent_found = [kw for kw in EmailClassifier.URGENT_KEYWORDS if kw in full_text]
        if urgent_found:
            score += 30
            reasons.append(f"Mots-clés urgents: {', '.join(urgent_found[:3])}")

        # Expéditeurs prioritaires
        if any(sender in from_email_lower for sender in EmailClassifier.PRIORITY_SENDERS):
            score += 40
            reasons.append("Expéditeur prioritaire")

        # Label IMPORTANT Gmail
        if 'IMPORTANT' in labels:
            score += 20
            reasons.append("Marqué IMPORTANT par Gmail")

        # Contact CRM avec score élevé (client actif)
        if contact_score and contact_score >= 70:
            score += 25
            reasons.append(f"Client important (score CRM: {contact_score})")

        # ============================================================
        # Critères IMPORTANT (Orange) - Score +15 à +25
        # ============================================================

        # Mots-clés importants
        important_found = [kw for kw in EmailClassifier.IMPORTANT_KEYWORDS if kw in full_text]
        if important_found and score < 50:  # Si pas déjà urgent
            score += 20
            reasons.append(f"Mots-clés importants: {', '.join(important_found[:2])}")

        # Contact CRM score moyen (prospect)
        if contact_score and 40 <= contact_score < 70 and score < 50:
            score += 15
            reasons.append(f"Prospect (score CRM: {contact_score})")

        # Email direct (pas de no-reply)
        if 'noreply' not in from_email_lower and 'no-reply' not in from_email_lower:
            score += 5

        # ============================================================
        # Critères NORMAL (Vert) - Score -20 à -30
        # ============================================================

        # Newsletters
        if any(sender in from_email_lower for sender in EmailClassifier.NEWSLETTER_SENDERS):
            score -= 25
            reasons.append("Newsletter")

        # Categories Gmail (updates, promotions, social)
        newsletter_labels = ['CATEGORY_UPDATES', 'CATEGORY_PROMOTIONS', 'CATEGORY_SOCIAL']
        if any(label in labels for label in newsletter_labels):
            score -= 20
            reasons.append("Catégorie Gmail non-prioritaire")

        # ============================================================
        # Détermination finale
        # ============================================================

        # B-293 : la couleur en toutes lettres, sans pastille emoji (charte du
        # projet : icônes SVG, dessinées par l'écran).
        if score >= 50:
            priority = 'high'
            color = 'Rouge'
        elif score >= 20:
            priority = 'medium'
            color = 'Orange'
        else:
            priority = 'low'
            color = 'Vert'

        # Raison finale
        if not reasons:
            reasons.append("Email standard")

        reason = f"{color} (score: {score}) - " + " • ".join(reasons[:3])

        return ClassificationResult(
            priority=priority,
            score=score,
            reason=reason
        )
