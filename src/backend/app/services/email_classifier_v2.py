"""
THÉRÈSE v2 - Email Classifier V2 (Optimisé 2026)

Algorithme sophistiqué basé sur les best practices 2026 :
- Catégories email : Transactional, Administrative, Business, Promotional, Newsletter
- Scoring multi-facteurs : sender, keywords, time-sensitivity, attachments
- Logique : Business/Admin/Transactional → Rouge, Promotional → Orange, Newsletter → Vert

Sources :
- https://mailtrap.io/blog/types-of-emails/
- https://www.alibaba.com/product-insights/ai-powered-email-prioritization-tools-do-they-learn-your-true-urgent-triggers-or-just-keywords.html
- https://productivityparents.com/using-ai-to-auto-sort-and-prioritize-your-emails/
"""

import re
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta


@dataclass
class ClassificationResult:
    """Résultat de classification."""
    priority: str  # 'high' | 'medium' | 'low'
    category: str  # Type d'email
    score: int  # 0-100
    reason: str  # Explication détaillée
    signals: dict  # Détail des signaux détectés


class EmailClassifierV2:
    """
    Classifieur d'emails optimisé 2026.

    Logique de priorité :
    - 🔴 ROUGE (high) : Business critique, Admin, Transactionnel urgent
    - 🟠 ORANGE (medium) : Business normal, Promotional ciblé
    - 🟢 VERT (low) : Newsletter, Promotional bulk, Social
    """

    # ============================================================
    # CATÉGORIES D'EMAILS
    # ============================================================

    # 1. TRANSACTIONAL - Déclenchés par action utilisateur
    TRANSACTIONAL_KEYWORDS = [
        # Facturation
        'facture', 'invoice', 'paiement', 'payment', 'reçu', 'receipt',
        'commande', 'order', 'achat', 'purchase', 'transaction',
        # Confirmations
        'confirmation', 'confirmé', 'confirmed', 'validé', 'approved',
        # Livraisons
        'expédition', 'livraison', 'shipping', 'delivery', 'colis',
    ]

    TRANSACTIONAL_SENDERS = [
        'stripe.com', 'paypal.com', 'gocardless.com', 'mollie.com',
        'amazon.fr', 'amazon.com', 'ebay.fr', 'leboncoin.fr',
        'chronopost.fr', 'colissimo.fr', 'ups.com', 'dhl.com',
    ]

    # 2. ADMINISTRATIVE - Obligations légales, gouvernement
    ADMINISTRATIVE_KEYWORDS = [
        # Impôts & Admin
        'impôt', 'tax', 'déclaration', 'urssaf', 'dgfip', 'trésor public',
        'avis échéance', 'régularisation', 'redressement',
        # Juridique
        'notification', 'mise en demeure', 'rappel', 'relance',
        'obligation', 'conformité', 'compliance', 'gdpr', 'rgpd',
        # Sécurité compte
        'sécurité', 'security', 'suspicious activity', 'connexion',
        'mot de passe', 'password reset', '2fa', 'vérification',
    ]

    ADMINISTRATIVE_SENDERS = [
        'impots.gouv.fr', 'urssaf.fr', 'dgfip', 'service-public.fr',
        'ameli.fr', 'pole-emploi.fr', 'caf.fr',
        'indy.fr', 'dougs.fr', 'pennylane.com',
        'notaire', 'avocat', 'huissier', 'tribunal',
    ]

    # 3. BUSINESS - Communication professionnelle
    BUSINESS_KEYWORDS = [
        # Opportunités
        'proposition', 'proposal', 'devis', 'quote', 'partenariat', 'partnership',
        'opportunité', 'opportunity', 'collaboration',
        # Rendez-vous
        'rendez-vous', 'meeting', 'réunion', 'entretien', 'interview',
        'call', 'visio', 'zoom', 'teams', 'meet',
        # Contrats & Projets
        'contrat', 'contract', 'projet', 'project', 'signature',
        'accord', 'agreement', 'bon de commande', 'po',
        # Urgent business
        'urgent', 'asap', 'deadline', 'échéance', 'urgent action required',
    ]

    BUSINESS_SENDERS = [
        # Outils de RDV / Scheduling
        'cal.com', 'calendly.com', 'savvycal.com', 'tidycal.com',
        'youcanbook.me', 'acuityscheduling.com', 'appointlet.com',
        # CRM / Sales Tools
        'hubspot.com', 'salesforce.com', 'pipedrive.com', 'zoho.com',
        # Payment / Invoicing pro
        'quickbooks.com', 'freshbooks.com', 'wave.apps',
    ]

    HIGH_VALUE_SENDERS = [
        # Domaines institutionnels et publics
        '.gouv.fr', '.education.fr', '.sante.fr', '.cnrs.fr',
        # Domaines entreprises significatifs
        '.cci.fr', '.chambre-agriculture.fr',
    ]

    # 4. PROMOTIONAL - Marketing, ventes
    PROMOTIONAL_KEYWORDS = [
        'promotion', 'promo', 'offre', 'offer', 'soldes', 'sale',
        'réduction', 'discount', 'remise', 'code promo',
        '-50%', '-30%', '% off', 'gratuit', 'free',
        'nouveau', 'new', 'lancement', 'launch',
    ]

    PROMOTIONAL_SENDERS = [
        'marketing@', 'promo@', 'newsletter@', 'sales@',
        'hello@', 'hi@', 'info@',
    ]

    # 5. NEWSLETTER - Contenus réguliers
    NEWSLETTER_KEYWORDS = [
        'newsletter', 'édition', 'edition', 'digest', 'résumé',
        'hebdo', 'weekly', 'mensuel', 'monthly',
        'bulletin', 'actualités', 'news',
        'lire en ligne', 'view online', 'unsubscribe', 'se désabonner',
    ]

    NEWSLETTER_SENDERS = [
        'beehiiv.com', 'substack.com', 'mailchimp.com', 'sendgrid.net',
        'sendinblue.com', 'brevo.com', 'mailjet.com',
        'noreply', 'no-reply', 'donotreply',
    ]

    # ============================================================
    # SIGNAUX COMPORTEMENTAUX
    # ============================================================

    URGENT_PATTERNS = [
        r'urgent',
        r'asap',
        r'deadline\s+\d{1,2}[/-]\d{1,2}',  # deadline 28/01
        r'échéance\s+\d{1,2}[/-]\d{1,2}',
        r'avant\s+le\s+\d{1,2}',  # avant le 28
        r'dernier\s+(rappel|délai)',
        r'action\s+requise',
        r'action\s+required',
    ]

    TIME_SENSITIVE_PATTERNS = [
        r'\d{1,2}[/-]\d{1,2}[/-]\d{2,4}',  # dates
        r'(demain|tomorrow)',
        r'(aujourd\'hui|today)',
        r'(cette semaine|this week)',
    ]

    @staticmethod
    def classify(
        subject: str,
        from_email: str,
        from_name: str,
        snippet: str,
        labels: list[str],
        has_attachments: bool = False,
        date: datetime | None = None,
        contact_score: int | None = None,
    ) -> ClassificationResult:
        """
        Classifie un email avec algorithme sophistiqué.

        Args:
            subject: Sujet de l'email
            from_email: Expéditeur
            from_name: Nom expéditeur
            snippet: Preview du contenu
            labels: Labels Gmail
            has_attachments: Présence de pièces jointes
            date: Date de réception
            contact_score: Score du contact CRM (0-100)

        Returns:
            ClassificationResult avec priorité, catégorie et détails
        """
        score = 50  # Score de base (neutre)
        signals = {}
        category = "unknown"

        # Texte complet pour analyse
        full_text = f"{subject} {snippet} {from_name}".lower()
        from_email_lower = from_email.lower()

        # ============================================================
        # 1. DÉTECTION CATÉGORIE
        # ============================================================

        # Transactional (priorité haute)
        transactional_found = [kw for kw in EmailClassifierV2.TRANSACTIONAL_KEYWORDS if kw in full_text]
        sender_transactional = any(s in from_email_lower for s in EmailClassifierV2.TRANSACTIONAL_SENDERS)

        if transactional_found or sender_transactional:
            category = "transactional"
            score += 30
            signals['transactional'] = transactional_found[:3] if transactional_found else ['sender']

        # Administrative (priorité très haute)
        admin_found = [kw for kw in EmailClassifierV2.ADMINISTRATIVE_KEYWORDS if kw in full_text]
        sender_admin = any(s in from_email_lower for s in EmailClassifierV2.ADMINISTRATIVE_SENDERS)

        if admin_found or sender_admin:
            category = "administrative"
            score += 40  # Plus important que transactional
            signals['administrative'] = admin_found[:3] if admin_found else ['sender']

        # Business (priorité haute si urgent, moyenne sinon)
        business_found = [kw for kw in EmailClassifierV2.BUSINESS_KEYWORDS if kw in full_text]
        sender_business = any(s in from_email_lower for s in EmailClassifierV2.BUSINESS_SENDERS)

        if (business_found or sender_business) and category == "unknown":
            category = "business"
            score += 20  # Boost de base pour business
            # Score dépend de l'urgence (voir signaux ci-dessous)
            signals['business'] = business_found[:3] if business_found else ['sender: business tool']

        # Promotional
        promo_found = [kw for kw in EmailClassifierV2.PROMOTIONAL_KEYWORDS if kw in full_text]
        sender_promo = any(s in from_email_lower for s in EmailClassifierV2.PROMOTIONAL_SENDERS)

        if (promo_found or sender_promo) and category == "unknown":
            category = "promotional"
            score -= 20
            signals['promotional'] = promo_found[:2] if promo_found else ['sender']

        # Newsletter (priorité basse)
        newsletter_found = [kw for kw in EmailClassifierV2.NEWSLETTER_KEYWORDS if kw in full_text]
        sender_newsletter = any(s in from_email_lower for s in EmailClassifierV2.NEWSLETTER_SENDERS)

        if newsletter_found or sender_newsletter:
            category = "newsletter"
            score -= 30
            signals['newsletter'] = newsletter_found[:2] if newsletter_found else ['sender']

        # ============================================================
        # 2. SIGNAUX D'URGENCE
        # ============================================================

        # Urgence explicite (mots-clés)
        urgent_matches = []
        for pattern in EmailClassifierV2.URGENT_PATTERNS:
            matches = re.findall(pattern, full_text, re.IGNORECASE)
            urgent_matches.extend(matches)

        if urgent_matches:
            score += 25
            signals['urgent'] = urgent_matches[:2]

        # Time-sensitive (dates proches)
        time_matches = []
        for pattern in EmailClassifierV2.TIME_SENSITIVE_PATTERNS:
            matches = re.findall(pattern, full_text, re.IGNORECASE)
            time_matches.extend(matches)

        if time_matches:
            score += 15
            signals['time_sensitive'] = time_matches[:2]

        # Email récent (<24h)
        if date:
            _date = date if date.tzinfo else date.replace(tzinfo=UTC)
            if (datetime.now(UTC) - _date) < timedelta(hours=24):
                score += 5
                signals['recent'] = True

        # ============================================================
        # 3. SIGNAUX CONTEXTUELS
        # ============================================================

        # Pièces jointes (souvent important)
        if has_attachments and category in ["business", "administrative", "transactional"]:
            score += 10
            signals['attachments'] = True

        # Label Gmail IMPORTANT
        if 'IMPORTANT' in labels:
            score += 20
            signals['gmail_important'] = True

        # Contact CRM (relation client)
        if contact_score:
            if contact_score >= 80:  # Client VIP
                score += 30
                signals['crm_vip'] = contact_score
            elif contact_score >= 60:  # Client actif
                score += 20
                signals['crm_active'] = contact_score
            elif contact_score >= 40:  # Prospect
                score += 10
                signals['crm_prospect'] = contact_score

        # Email direct (pas de no-reply)
        if 'noreply' not in from_email_lower and 'no-reply' not in from_email_lower:
            score += 5
            signals['direct'] = True

        # Catégories Gmail (baisse priorité)
        low_priority_labels = ['CATEGORY_UPDATES', 'CATEGORY_PROMOTIONS', 'CATEGORY_SOCIAL', 'CATEGORY_FORUMS']
        if any(label in labels for label in low_priority_labels):
            score -= 25
            signals['gmail_category_low'] = True

        # ============================================================
        # 4. DÉTERMINATION FINALE
        # ============================================================

        # Plafond et plancher
        score = max(0, min(100, score))

        # Règles strictes pour certaines catégories
        if category == "administrative":
            priority = 'high'  # Admin = toujours rouge
        elif category == "newsletter":
            priority = 'low'  # Newsletter = toujours vert
        elif score >= 65:
            priority = 'high'
        elif score >= 35:
            priority = 'medium'
        else:
            priority = 'low'

        # ============================================================
        # 5. GÉNÉRATION RAISON
        # ============================================================

        color_emoji = {'high': '🔴 Rouge', 'medium': '🟠 Orange', 'low': '🟢 Vert'}
        category_label = {
            'transactional': 'Transactionnel',
            'administrative': 'Administratif',
            'business': 'Business',
            'promotional': 'Promotionnel',
            'newsletter': 'Newsletter',
            'unknown': 'Standard',
        }

        reasons = []
        reasons.append(f"Catégorie : {category_label[category]}")

        if 'administrative' in signals:
            reasons.append(f"Admin : {', '.join(signals['administrative'][:2])}")
        if 'transactional' in signals:
            reasons.append(f"Transaction : {', '.join(signals['transactional'][:2])}")
        if 'business' in signals:
            reasons.append(f"Business : {', '.join(signals['business'][:2])}")
        if 'urgent' in signals:
            reasons.append(f"Urgent : {', '.join(signals['urgent'][:2])}")
        if 'time_sensitive' in signals:
            reasons.append("Time-sensitive")
        if 'crm_vip' in signals:
            reasons.append(f"Client VIP (score {signals['crm_vip']})")
        elif 'crm_active' in signals:
            reasons.append(f"Client actif (score {signals['crm_active']})")
        if 'attachments' in signals:
            reasons.append("Pièce jointe")
        if 'gmail_important' in signals:
            reasons.append("Gmail IMPORTANT")

        reason = f"{color_emoji[priority]} (score: {score}) - " + " • ".join(reasons[:4])

        return ClassificationResult(
            priority=priority,
            category=category,
            score=score,
            reason=reason,
            signals=signals,
        )
