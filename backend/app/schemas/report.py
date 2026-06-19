from pydantic import BaseModel

from app.schemas.facility import FacilityData
from app.schemas.manual import ManualInputs


class ReportPayload(BaseModel):
    facility: FacilityData
    manual: ManualInputs

    @property
    def display_name(self) -> str:
        if self.manual.facility_name_override:
            return self.manual.facility_name_override
        return self.facility.facility_name_from_cms


class InsightsRequest(BaseModel):
    facility: FacilityData
    manual: ManualInputs


class InsightsResponse(BaseModel):
    summary: str
    generated_by: str


class ExportRequest(BaseModel):
    facility: FacilityData
    manual: ManualInputs
    ai_summary: str | None = None

    def to_report_payload(self) -> ReportPayload:
        return ReportPayload(facility=self.facility, manual=self.manual)
