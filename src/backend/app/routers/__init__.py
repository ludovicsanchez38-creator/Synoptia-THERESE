"""
THÉRÈSE v2 - API Routers

FastAPI router modules for each feature area.
"""

# v0.5 - Agents IA Embarqués (Atelier)
from app.routers.agents import router as agents_router
from app.routers.board import router as board_router

# v0.6 - Browser Automation (Manus-inspired)
from app.routers.browser import router as browser_router
from app.routers.calculators import router as calc_router
from app.routers.calendar import router as calendar_router
from app.routers.chat import router as chat_router

# User Commands
from app.routers.commands import router as commands_router

# V3 - Commands unifiées
from app.routers.commands_v3 import router as commands_v3_router
from app.routers.config import router as config_router

# Phase 5 CRM (implemented)
from app.routers.crm import router as crm_router

# US-005 - Dashboard "Ma journée" (v0.9.0)
from app.routers.dashboard import router as dashboard_router
from app.routers.data import router as data_router

# Phase 1-4 routers (ACTIVATED)
from app.routers.email import router as email_router

# Email Setup Wizard (Phase 1.2)
from app.routers.email_setup import router as email_setup_router
from app.routers.escalation import router as escalation_router
from app.routers.files import router as files_router

# Email Follow-Ups (Email Backlog)
from app.routers.follow_ups import router as follow_ups_router
from app.routers.images import router as images_router
from app.routers.invoices import router as invoices_router
from app.routers.mcp import router as mcp_router
from app.routers.memory import router as memory_router

# US-004 - Notifications push in-app (v0.9.0)
from app.routers.notifications import router as notifications_router
from app.routers.performance import router as perf_router
from app.routers.personalisation import router as personalisation_router

# Phase 6 RGPD Compliance
from app.routers.rgpd import router as rgpd_router
from app.routers.skills import router as skills_router
from app.routers.tasks import router as tasks_router

# V3 - Installed Tools
from app.routers.tools import router as tools_router
from app.routers.voice import router as voice_router

__all__ = [
    "chat_router",
    "memory_router",
    "files_router",
    "config_router",
    "skills_router",
    "voice_router",
    "images_router",
    "board_router",
    "calc_router",
    "mcp_router",
    "data_router",
    "perf_router",
    "personalisation_router",
    "escalation_router",
    "email_router",  # Phase 1 - ACTIVATED
    "calendar_router",  # Phase 2 - ACTIVATED
    "tasks_router",  # Phase 3 - ACTIVATED
    "invoices_router",  # Phase 4 - ACTIVATED
    "crm_router",  # Phase 5 - Implemented
    "rgpd_router",  # Phase 6 - RGPD Compliance
    "email_setup_router",  # Phase 1.2 - Email Setup Wizard
    "commands_router",  # User Commands
    "commands_v3_router",  # V3 - Commands unifiées
    "tools_router",  # V3 - Installed Tools
    "agents_router",  # v0.5 - Agents IA Embarqués (Atelier)
    "browser_router",  # v0.6 - Browser Automation
    "notifications_router",  # US-004 - Notifications push in-app
    "dashboard_router",  # US-005 - Dashboard Ma journée
    "follow_ups_router",  # Email Backlog - Follow-ups
]
