import typing
if typing.TYPE_CHECKING:
    import fastapi
    from .config.api import StaticPathConfigs, SecurityHeadersConfig, CORSConfig
import logging

IS_RUNNING_AS_API = False

def configure_logging(logging_settings):
    from logging import config
    if logging_settings.pop("skip_config", False): return
    config.dictConfig(logging_settings)


def register_default_exception_handler(app: "fastapi.FastAPI"):
    from lib.apibuilder.exceptions import FoundryAPIException
    from fastapi.responses import JSONResponse
    from fastapi.requests import Request
    from pydantic import error_wrappers

    @app.exception_handler(FoundryAPIException)
    async def foundry_exception_handler(request: Request, exc: FoundryAPIException) -> JSONResponse:
        headers = getattr(exc, "headers", None)
        if not exc.hide_logs:
            logging.exception(exc)
        if headers:
            return JSONResponse(
                exc.get_dict(), status_code=exc.status_code, headers=headers
            )
        else:
            return JSONResponse(exc.get_dict(), status_code=exc.status_code)

    @app.exception_handler(error_wrappers.ValidationError)
    async def pydantic_exception_handler(request: Request, exc: error_wrappers.ValidationError) -> JSONResponse:
        return JSONResponse({
            "user_message": "Invalid Request Parameters",
            "detail": error_wrappers.display_errors(exc.errors()),
            "errors": exc.errors()
        },status_code=400)


def initialise_route(app: "fastapi.FastAPI", api_router: "fastapi.APIRouter", route_module:str):
    import importlib
    route_module = route_module.split(":")
    if len(route_module) >= 2:
        route_module, init_func = route_module
    else:
        init_func = "init_app"
        route_module = route_module[0]
    mod = importlib.import_module(route_module)
    init_fn = getattr(mod, init_func)
    return init_fn(app, api_router)
    

def add_static_paths(app: "fastapi.FastAPI", static_paths: "StaticPathConfigs"):
    if len(static_paths) <= 0: return
    from starlette.staticfiles import StaticFiles, PathLike, HTTPException, RedirectResponse, stat, URL
    import anyio
    class Static404Override(StaticFiles):
        def __init__(
            self,
            *,
            directory: typing.Optional[PathLike] = None,
            packages: typing.Optional[
                typing.List[typing.Union[str, typing.Tuple[str, str]]]
            ] = None,
            html: bool = False,
            check_dir: bool = True,
            override_404_file=None
        ):
            super().__init__(directory=directory,packages=packages,html=html,check_dir=check_dir)
            self.override_404_file = override_404_file
        
        async def get_response(self, path, scope):
            try:
                return await super().get_response(path=path,scope=scope)
            except HTTPException as ex:
                if ex.status_code != 404 or self.override_404_file is None: raise ex

            full_path, stat_result = await anyio.to_thread.run_sync(
                self.lookup_path, self.override_404_file
            )
            if stat_result is not None and stat.S_ISREG(stat_result.st_mode):
                # TODO validate if needed
                # if not scope["path"].endswith("/"):
                #     # Directory URLs should redirect to always end in "/".
                #     url = URL(scope=scope)
                #     url = url.replace(path=url.path + "/")
                #     return RedirectResponse(url=url)
                return self.file_response(full_path, stat_result, scope)
            raise HTTPException(status_code=404)

    for path in static_paths:
        app.mount(
            path.mount_path, 
            Static404Override(
                directory=path.directory, 
                packages=path.packages, 
                html=path.html, 
                check_dir=path.check_dir,
                override_404_file=path.override_404_file
            ),
            name=path.name
        )


def add_cors_middleware(app: "fastapi.FastAPI", cors_config: "CORSConfig"):
    if not cors_config.enabled: return
    from fastapi.middleware.cors import CORSMiddleware
    conf_dict = cors_config.dict()
    conf_dict.pop("enabled")
    app.add_middleware(
        CORSMiddleware,
        **conf_dict
    )

def add_security_headers_middleware(app: "fastapi.FastAPI", security_headers_config: "SecurityHeadersConfig"):
    if not security_headers_config.enabled: return
    from .csp_middleware import SecurityHeadersMiddleware
    conf_dict = security_headers_config.dict()
    conf_dict.pop("enabled")
    app.add_middleware(
        SecurityHeadersMiddleware,
        **conf_dict
    )

def init_app():
    global IS_RUNNING_AS_API
    IS_RUNNING_AS_API = True
    import fastapi
    import lib.apibuilder.app as appbuilder
    from lib.apibuilder.config import get_settings
    from .config.api import APISettings
    app_settings = appbuilder.init_app_config()
    api_settings: APISettings = get_settings(APISettings)
    api_app_settings_dict = api_settings.app.dict()
    route_modules = api_app_settings_dict.pop("route_modules")

    app = fastapi.FastAPI(
        **api_app_settings_dict
    )

    register_default_exception_handler(app)
    configure_logging(app_settings.logging.dict())
    add_cors_middleware(app, api_settings.cors)
    add_security_headers_middleware(app, api_settings.security_headers)

    api_router = fastapi.APIRouter()
    for route_module in route_modules:
        initialise_route(app, api_router, route_module)
    app.include_router(api_router, **api_settings.api_route.dict())

    add_static_paths(app, api_settings.static_paths)
    return app


def start_server():
    import uvicorn
    from lib.apibuilder.config import get_settings
    from .config.api import APISettings
    api_settings: APISettings = get_settings(APISettings)
    uvicorn.run(__name__+":init_app", factory=True, **api_settings.server.dict())


if __name__ == "__main__": start_server()