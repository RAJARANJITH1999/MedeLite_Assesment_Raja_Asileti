from pydantic import BaseModel


class ClaimsMetric(BaseModel):
    label: str
    facility_value: float | None = None
    national_avg: float | None = None
    state_avg: float | None = None
    unit: str = "%"
    footnote: str | None = None


class FacilityData(BaseModel):
    ccn: str
    facility_name_from_cms: str
    legal_business_name: str
    address: str
    city: str
    state: str
    zip_code: str
    certified_beds: int | None = None
    overall_rating: int | None = None
    health_inspection_rating: int | None = None
    staffing_rating: int | None = None
    quality_rating: int | None = None
    str_hospitalization: ClaimsMetric
    str_ed_visit: ClaimsMetric
    lt_hospitalization: ClaimsMetric
    lt_ed_visit: ClaimsMetric
    medicare_care_compare_url: str
