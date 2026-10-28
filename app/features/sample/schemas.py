from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class SampleRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=50)
    description: Optional[str] = Field(None, max_length=200)
    value: float = Field(..., ge=0)


class SampleResponse(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    value: float

    model_config = ConfigDict(from_attributes=True)
