from fastapi import APIRouter, status
from app.features.sample.schemas import SampleRequest, SampleResponse
from app.features.sample import service
from app.shared.exceptions import APIResponse, create_success_response, STANDARD_ERROR_RESPONSES

router = APIRouter()


@router.post(
    "",
    response_model=APIResponse[SampleResponse],
    status_code=status.HTTP_201_CREATED,
    responses=STANDARD_ERROR_RESPONSES,
)
async def create_sample(payload: SampleRequest):
    record = service.create_sample(payload)
    return create_success_response(message="Sample created successfully", data=record)


@router.get(
    "/{sample_id}",
    response_model=APIResponse[SampleResponse],
    responses=STANDARD_ERROR_RESPONSES,
)
async def get_sample(sample_id: str):
    record = service.get_sample(sample_id)
    return create_success_response(message="Sample retrieved successfully", data=record)
