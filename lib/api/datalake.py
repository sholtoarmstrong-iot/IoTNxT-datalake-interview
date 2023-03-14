import typing
import fastapi
from ..models.config import DatalakeConfig
from lib.apibuilder.config import get_settings
from pydantic import BaseModel
from pathlib import Path

router = fastapi.APIRouter(
    prefix="",
    tags=["datalake"],
    responses={404: {"description": "Not Found"}}
)

class UploadedResponse(BaseModel):
    size_uploaded: float

@router.post("/upload")
async def upload_to_datalake(files: typing.List[fastapi.UploadFile])->UploadedResponse:
    config: DatalakeConfig = get_settings(DatalakeConfig)
    # TODO check file type is one of supported types
    # TODO read data and store to data directory
        # BONUS What did you store the data as and why? (Answer as a comment)
        # BONUS what can be done to optimise calls to the info request
    # NOTE we can assume all data uploaded to this endpoint has the same schema. Bonus to assume a schema and enforce it
    return UploadedResponse(size_uploaded=sum(file.size for file in files))


class InfoResponse(BaseModel):
    min_value: float
    max_value: float
    mean_value: float
    number_of_files: int
    total_records: int

@router.get("/info")
async def info(column: str, date: typing.Optional[str]=None, key: typing.Optional[str]=None) -> InfoResponse:
    config: DatalakeConfig = get_settings(DatalakeConfig)
    # TODO return statistics for uploaded data for the given date (single day) and key.
    # NOTE if no key or date given the statistics should be given for all files

    return InfoResponse(
        min_value=0,  # TODO Calculate me
        max_value=0,  # TODO Calculate me
        mean_value=0,  # TODO Calculate me
        number_of_files=0,  # Number of files scanned
        total_records=0,  # Number of records matching criteria
    )

class SizeResponse(BaseModel):
    size_before: float
    size_after: float

@router.post("/optimise")
async def upload_to_datalake()->SizeResponse:
    config: DatalakeConfig = get_settings(DatalakeConfig)

    root_directory = Path(config.data_directory)
    size_before = sum(f.stat().st_size for f in root_directory.glob('**/*') if f.is_file())
    # TODO Assuming the upload endpoint is used multiple times a day what can be done to optimise the datalake
    size_after = sum(f.stat().st_size for f in root_directory.glob('**/*') if f.is_file())
    return SizeResponse(size_before=size_before, size_after=size_after)

@router.delete("/")
async def delete(date: typing.Optional[str]=None, key: typing.Optional[str]=None) -> SizeResponse:
    config: DatalakeConfig = get_settings(DatalakeConfig)
    root_directory = Path(config.data_directory)
    size_before = sum(f.stat().st_size for f in root_directory.glob('**/*') if f.is_file())
    # TODO delete data matching the given criteria. Note this time all data before the given date should be deleted
    # NOTE if no key or date given the data should be deleted for all files

    size_after = sum(f.stat().st_size for f in root_directory.glob('**/*') if f.is_file())
    return SizeResponse(size_before=size_before, size_after=size_after)