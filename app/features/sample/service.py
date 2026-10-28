import uuid
from app.features.sample.schemas import SampleRequest, SampleResponse
from app.shared.exceptions import NotFoundError, ValidationError

_store: dict[str, SampleResponse] = {}


def create_sample(payload: SampleRequest) -> SampleResponse:
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
    _store[sample_id] = record
    return record


def get_sample(sample_id: str) -> SampleResponse:
    if sample_id not in _store:
        raise NotFoundError(message=f"Sample with id '{sample_id}' not found")
    return _store[sample_id]
