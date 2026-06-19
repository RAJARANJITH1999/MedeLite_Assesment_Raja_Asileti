from typing import Literal

from pydantic import BaseModel


class ManualInputs(BaseModel):
    facility_name_override: str | None = None
    emr: str = ""
    current_census: int | None = None
    patient_type: str = ""
    previous_coverage: Literal["Yes", "No", ""] = ""
    previous_performance: str = ""
    medical_coverage: str = ""
