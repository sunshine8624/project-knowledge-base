from .document import router as document_router
from .query import router as query_router
from .settings import router as settings_router

__all__ = ["document_router", "query_router", "settings_router"]