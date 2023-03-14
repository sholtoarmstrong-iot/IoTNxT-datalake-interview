import pydantic
import typing

class DatalakeConfig(pydantic.BaseModel):
    __root_mount_path__ = "datalake" 
    class Config:
        extra=pydantic.Extra.allow

    data_directory: str
    # We assume the data is timeseries data and this key is used to determine what field is used.
    timeseries_column: str
    # We assume the data has a key relating to a specific instance
    key_column: str
    supported_types: typing.List[str]

