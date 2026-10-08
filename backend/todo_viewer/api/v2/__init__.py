from .notes_routers import global_router as notes_global_router
from .notes_routers import router as notes_router
from .routers import router

# Every router of API v2: the app mounts them and the OpenAPI export documents them.
ROUTERS = (router, notes_router, notes_global_router)

__all__ = ["ROUTERS", "notes_global_router", "notes_router", "router"]
