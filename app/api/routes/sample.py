import uuid
from fastapi import APIRouter, status
from app.schemas.sample import SampleRequest, SampleResponse
from app.utils.exceptions import (
    APIResponse,
    create_success_response,
    NotFoundError,
    ValidationError,
    STANDARD_ERROR_RESPONSES,
)

router = APIRouter()

# In-memory store for demonstration
_sample_store = {}


@router.post(
    "",
    response_model=APIResponse[SampleResponse],
    status_code=status.HTTP_201_CREATED,
    responses=STANDARD_ERROR_RESPONSES,
)
async def create_sample(payload: SampleRequest):
    if payload.name.lower() == "forbidden":
        raise ValidationError(
            message="The name 'forbidden' is reserved and cannot be used.",
            fields={"name": "Reserved keyword"},
        )

    sample_id = str(uuid.uuid4())
    record = SampleResponse(
        id=sample_id,
        name=payload.name,
        description=payload.description,
        value=payload.value,
    )
    _sample_store[sample_id] = record

    return create_success_response(
        message="Sample created successfully",
        data=record,
    )


@router.get(
    "/{sample_id}",
    response_model=APIResponse[SampleResponse],
    responses=STANDARD_ERROR_RESPONSES,
)
async def get_sample(sample_id: str):
    if sample_id not in _sample_store:
        raise NotFoundError(message=f"Sample with id '{sample_id}' not found")

    return create_success_response(
        message="Sample retrieved successfully",
        data=_sample_store[sample_id],
    )
