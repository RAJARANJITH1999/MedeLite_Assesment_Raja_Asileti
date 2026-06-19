from pydantic import BaseModel

from app.schemas.facility import FacilityData
from app.schemas.manual import ManualInputs


class ChatFacility(BaseModel):
    facility: FacilityData
    manual: ManualInputs


class ChatRequest(BaseModel):
    facilities: list[ChatFacility]
    question: str


class ChatResponse(BaseModel):
    answer: str
    generated_by: str
