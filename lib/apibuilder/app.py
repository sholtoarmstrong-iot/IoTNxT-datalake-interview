import typing
from functools import lru_cache
if typing.TYPE_CHECKING:
    from .config import Settings

# Ensure only called once
@lru_cache(maxsize=1)
def init_app_config() -> 'Settings':
    from .config import get_settings, ConfigSourceManager
    import argparse
    app_arg_parser = argparse.ArgumentParser()
    ConfigSourceManager.configure_argparser(app_arg_parser)
    args, unknown_args = app_arg_parser.parse_known_args()
    if unknown_args:
        import logging
        logger = logging.getLogger(__name__)
        logger.warn(f"Unknown args {unknown_args}")
    ConfigSourceManager.configure_sources(args)
    return get_settings()

def start_app():
    settings = init_app_config()
    import importlib
    entrypoint_module = settings.entrypoint.split(":")
    if len(entrypoint_module) >= 2:
        entrypoint_module, init_func = entrypoint_module
    else:
        init_func = "main"
        entrypoint_module = entrypoint_module[0]
    mod = importlib.import_module(entrypoint_module)
    init_fn = getattr(mod, init_func)
    return init_fn()

if __name__ == "__main__": start_app()