"""
THÉRÈSE v2 - Services Package

Business logic and external service integrations.

US-016 : ce package n'a PLUS de réexports. Les anciens
`from app.services import get_llm_service, embed_text...` forçaient l'import
d'embeddings.py (donc sentence_transformers + torch, plusieurs secondes et
centaines de Mo) pour TOUT consommateur du package - y compris le sous-process
sandbox de génération de documents qui n'en a jamais besoin.
Importer directement le module voulu : `from app.services.llm import ...`,
`from app.services.embeddings import ...`, etc.
"""
