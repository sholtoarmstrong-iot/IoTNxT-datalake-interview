import typing
import pydantic
from .api_security import CORSConfig, SecurityHeadersConfig

def secret_key_generator():
    import string
    import secrets
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for i in range(25))

class AppConfig(pydantic.BaseModel):
    class Config:
        extra=pydantic.Extra.allow

    route_modules: typing.List[str] = pydantic.Field(default_factory=list)
    debug: bool = False
    title: str = "FastAPI"
    description: str = "",
    version: str = "0.1.0"
    openapi_url: typing.Optional[str] = "/openapi.json"
    docs_url: typing.Optional[str] = "/docs"
    redoc_url: typing.Optional[str] = "/redoc"
    swagger_ui_oauth2_redirect_url: typing.Optional[str] = "/docs/oauth2-redirect"
    terms_of_service: typing.Optional[str] = None
    contact: typing.Optional[typing.Dict[str, typing.Union[str, typing.Any]]] = None
    license_info: typing.Optional[typing.Dict[str, typing.Union[str, typing.Any]]] = None
    openapi_prefix: str = ""
    root_path: str = ""
    app_prefix: str = "/"

class ServerConfig(pydantic.BaseModel):
    class Config:
        extra=pydantic.Extra.allow   
    host: str = "0.0.0.0"
    port: int = 8002

class AuthClientConfig(pydantic.BaseModel):
    class Config:
        extra=pydantic.Extra.allow
    server_metadata_url: str = pydantic.Field()
    client_id: typing.Optional[str] = pydantic.Field(None)
    client_kwargs: dict = pydantic.Field(default_factory=lambda:{"scope": "openid"})


class StaticPathConfig(pydantic.BaseModel):
    name: str
    mount_path: str
    directory: typing.Optional[str] = None
    packages: typing.Optional[
        typing.List[typing.Union[str, typing.Tuple[str, str]]]
    ] = None
    html: bool = False
    check_dir: bool = True
    override_404_file: typing.Optional[str] = None

class APIRouteConfig(pydantic.BaseModel):
    class Config:
        extra=pydantic.Extra.allow
    prefix: str = "/api"


StaticPathConfigs = typing.List[StaticPathConfig]

class APISettings(pydantic.BaseModel):
    app: AppConfig = AppConfig()
    api_route: APIRouteConfig = APIRouteConfig()
    server: ServerConfig = ServerConfig()
    cors: CORSConfig = CORSConfig()
    security_headers: SecurityHeadersConfig = SecurityHeadersConfig()
    static_paths: StaticPathConfigs = pydantic.Field(default_factory=list)
    include_core: bool = True