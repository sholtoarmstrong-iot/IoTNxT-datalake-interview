import os
import typing
import pydantic
from functools import lru_cache
from .logging import LoggingConfig

if typing.TYPE_CHECKING:
    import argparse

@lru_cache(maxsize=1)
def _get_logger():
    import logging
    logger = logging.getLogger(__name__)
    return logger


class ConfigSourceManager:
    _default_config_paths = [
        './config.yml',
        # os.path.join(os.path.split(__file__)[0],'../config.yml'),
        './uncommitted/config.yml',
        '/etc/foundry/foundry.yml',
        '/etc/foundry/navigator.yml',
        os.path.expanduser('~/.foundry/foundry.yaml'),
        os.path.expanduser('~/.foundry/navigator.yaml'),
    ]
    _config_paths = None

    @staticmethod
    def yaml_conf_source(settings_path: str):
        import yaml
        try:
            from yaml import CFullLoader as FullLoader
        except ImportError:
            from yaml import FullLoader
        def inner(settings: pydantic.BaseSettings):
            if not os.path.isfile(settings_path): return {}
            with open(settings_path, 'r') as f:
                data = yaml.load(f, Loader=FullLoader)
            return data
        return inner

    @classmethod
    def _customise_sources(
        cls, 
        init_settings,
        env_settings,
        file_secret_settings,
    ) -> typing.Tuple[pydantic.env_settings.SettingsSourceCallable, ...]:
        # Ensure each file only loaded once
        config_paths = cls.get_config_paths()
        yaml_sources = [cls.yaml_conf_source(p) for p in config_paths]
        return tuple((init_settings, env_settings, *yaml_sources[::-1], file_secret_settings))

    @classmethod
    def get_config_paths(cls):
        config_paths = cls._config_paths
        if config_paths is None:
            _get_logger().warn("Config paths not configured. Using Default.")
            config_paths = cls._default_config_paths
        # Mimic ordered set (not ideal but shouldn't be too many for n^2 to actually matter might even be faster)
        unique_paths = []
        for path in config_paths:
            abs_path = os.path.abspath(path)
            if abs_path not in unique_paths: unique_paths.append(abs_path)
        return unique_paths
    

    @classmethod
    def configure_sources(cls, config: any):
        if cls._config_paths is not None:
            _get_logger().warn("Config sources already configured")
        cls._config_paths = []
        if not config.disable_default_config:
            cls._config_paths.extend(cls._default_config_paths)
        if config.conf_paths is not None:
            for path in config.conf_paths:
                abs_path = os.path.abspath(path)
                if os.path.isfile(abs_path):
                    cls._config_paths.append(abs_path)
                else:
                    _get_logger().warn(f"Could not find config path: {abs_path}")

    @classmethod
    def configure_argparser(cls, parser: "argparse.ArgumentParser"):
        parser.add_argument('--disable-default-config', action='store_true', dest="disable_default_config")
        parser.add_argument(
            '--config-path','-C', 
            metavar='Config Files', 
            type=str, 
            nargs='+', 
            help='an integer for the accumulator',
            dest = "conf_paths"
        )
    

class Settings(pydantic.BaseSettings):
    entrypoint: str = "lib.apibuilder.api:start_server"
    logging: LoggingConfig = pydantic.Field(default_factory=LoggingConfig)

    class Config:
        env_prefix = "navigator_"
        extra=pydantic.Extra.allow
        # TODO confirm paths
        customise_sources=ConfigSourceManager._customise_sources


T = typing.TypeVar("T")
@lru_cache()
def get_settings(settings_class:typing.Type[T]=Settings, mount_path=None, nest_key=None) -> T:
    """This function returns the config. By default the base config will be returned. 
    If a settings class is provided an instance of that class will be returned initialised with the relevant options.
    If a mount_path is provided (e.g. path.subpath.[4].subsubpath) the settings["path"]["subpath"][3]["subsubpath"] will be used to initialise the settings_class.
    If a mount path is not given, the "__root_mount_path__" attribute of the class is used as a mount path else it is defaulted to the root of the config.

    Args:
        settings_class (T, optional): The settings class to initialise. Defaults to Settings.
        mount_path (_type_, optional): The path the class should be constructed with. Defaults to __root_mount_path__ of the class if available or the root of the settings.

    Returns:
        T: _description_
    """
    if settings_class == Settings: return Settings()
    base_settings = get_settings()
    settings_dict = base_settings.dict()

    if mount_path is None and hasattr(settings_class, "__root_mount_path__"):
        mount_path = settings_class.__root_mount_path__
    if mount_path is not None:
        for part in mount_path.split('.'):
            if part.startswith('[') and part.endswith(']'):
                part = int(part[1:-1])
            settings_dict = settings_dict.get(part, {})
    if nest_key is None and hasattr(settings_class, "__settings_nest_key__"):
        nest_key = settings_class.__settings_nest_key__
    if nest_key is not None:
        settings_dict = {nest_key: settings_dict}
    # TODO potentially filter settings on settings_class.__fields__ if settings_class.Config.extra not configured
    return settings_class(**settings_dict)