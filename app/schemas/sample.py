from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class SampleRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=50, description="Name of the sample entity")
    description: Optional[str] = Field(None, max_length=200, description="Optional description")
    value: float = Field(..., ge=0, description="Non-negative numeric value")


class SampleResponse(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    value: float

    model_config = ConfigDict(from_attributes=True)
