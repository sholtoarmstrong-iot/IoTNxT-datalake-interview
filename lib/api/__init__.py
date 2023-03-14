import typing
if typing.TYPE_CHECKING:
    import fastapi

def init_app(app: 'fastapi.FastAPI', api_router: 'fastapi.APIRouter'):
    from .datalake import router as datalake_router

    api_router.include_router(datalake_router, prefix="/datalake")