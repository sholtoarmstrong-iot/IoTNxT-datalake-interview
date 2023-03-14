import pydantic

def default_formatter_config():
    return {
        "simple": {"format": '%(asctime)s - %(name)s - %(levelname)s - %(message)s'}
    }
def default_handler_config():
    return {
        "console": {
            "class": "logging.StreamHandler",
            "level": "DEBUG",
            "formatter": "simple",
            "stream": "ext://sys.stdout"
        }
    }
def default_root_config():
    return {
        "level": "DEBUG",
        "handlers": ["console"]
    }

class LoggingConfig(pydantic.BaseModel):
    class Config:
        extra=pydantic.Extra.allow
    skip_config: bool = True
    version: int = 1
    formatters: dict = pydantic.Field(default_factory=default_formatter_config)
    handlers: dict = pydantic.Field(default_factory=default_handler_config)
    loggers: dict = pydantic.Field(default_factory=dict)
    filters: dict = pydantic.Field(default_factory=dict)
    root: dict = pydantic.Field(default_factory=default_root_config)