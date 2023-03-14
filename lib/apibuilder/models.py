import typing
from pydantic import BaseModel
from pydantic.generics import GenericModel

DataT = typing.TypeVar('DataT')

class DataWrapped(GenericModel, typing.Generic[DataT]):
    data: DataT

class Success(BaseModel):
    success: bool = True