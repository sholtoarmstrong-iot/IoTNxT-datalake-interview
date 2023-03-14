import typing
import pydantic

CSPConfig = typing.Union[typing.Dict[str, typing.Union[str,typing.List[str]]],str]

class CORSConfig(pydantic.BaseModel):
    class Config:
        extra=pydantic.Extra.allow

    enabled: bool = False
    allow_origins: typing.Sequence[str] = ()
    allow_methods: typing.Sequence[str] = ("GET",)
    allow_headers: typing.Sequence[str] = ()
    allow_credentials: bool = False
    allow_origin_regex: typing.Optional[str] = None
    expose_headers: typing.Sequence[str] = ()
    max_age: int = 600


class SecurityHeadersConfig(pydantic.BaseModel):
    enabled: bool = False
    """
    Example of a CSP
    {
        "default-src": "'self'",
        "img-src": [
            "*",
            # For SWAGGER UI
            "data:",
        ],
        "connect-src": "'self'",
        "script-src": "'self'",
        "style-src": ["'self'", "'unsafe-inline'"],
        "script-src-elem": [
            # For SWAGGER UI
            "https://cdn.jsdelivr.net/npm/swagger-ui-dist@4/swagger-ui-bundle.js",
            "'sha256-1I8qOd6RIfaPInCv8Ivv4j+J0C6d7I8+th40S5U/TVc='",
        ],
        "style-src-elem": [
            # For SWAGGER UI
            "https://cdn.jsdelivr.net/npm/swagger-ui-dist@4/swagger-ui.css",
        ],
    }
    """
    csp: typing.Optional[CSPConfig] = pydantic.Field(default_factory=lambda:{
        "default-src": "'self'",
        "img-src": ["*"],
    })
    additional_headers: typing.Optional[typing.Dict[str, str]] = pydantic.Field(default_factory=lambda:{
        "Cross-Origin-Opener-Policy": "same-origin",
        "Referrer-Policy": "strict-origin-when-cross-origin",
        "Strict-Transport-Security": "max-age=31556926; includeSubDomains",
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": "DENY",
        "X-XSS-Protection": "1; mode=block",
    })


