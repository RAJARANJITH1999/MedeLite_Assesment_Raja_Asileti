from app.config import settings
from app.schemas.facility import ClaimsMetric, FacilityData

# State US Averages dataset column names (verified live, see PROJECT.md section 5).
_NATIONAL_STATE_FIELD = {
    "521": "percentage_of_short_stay_residents_who_were_rehospitalized__1d02",
    "522": "percentage_of_short_stay_residents_who_had_an_outpatient_em_d911",
    "551": "number_of_hospitalizations_per_1000_longstay_resident_days",
    "552": "number_of_outpatient_emergency_department_visits_per_1000_l_de9d",
}

_CLAIMS_METRICS = (
    ("521", "Short Term Hospitalization", "%"),
    ("522", "STR ED Visit", "%"),
    ("551", "LT Hospitalization", ""),
    ("552", "LT ED Visit", ""),
)


def _to_int(value: str | None) -> int | None:
    if value in (None, ""):
        return None
    return int(float(value))


def _to_float(value: str | None) -> float | None:
    if value in (None, ""):
        return None
    return float(value)


def _claims_metric(
    code: str,
    label: str,
    unit: str,
    claims_by_code: dict[str, dict],
    nation_averages: dict,
    state_averages: dict,
) -> ClaimsMetric:
    row = claims_by_code.get(code, {})
    field = _NATIONAL_STATE_FIELD[code]
    return ClaimsMetric(
        label=label,
        facility_value=_to_float(row.get("observed_score")),
        national_avg=_to_float(nation_averages.get(field)),
        state_avg=_to_float(state_averages.get(field)),
        unit=unit,
        footnote=row.get("footnote_for_score") or None,
    )


def map_facility_data(ccn: str, raw: dict) -> FacilityData:
    info = raw["provider_info"]
    claims_by_code = {row["measure_code"]: row for row in raw["claims_measures"]}
    nation_averages = raw["nation_averages"]
    state_averages = raw["state_averages"]

    metrics = {
        code: _claims_metric(code, label, unit, claims_by_code, nation_averages, state_averages)
        for code, label, unit in _CLAIMS_METRICS
    }

    return FacilityData(
        ccn=ccn,
        facility_name_from_cms=info["provider_name"],
        legal_business_name=info.get("legal_business_name") or info["provider_name"],
        address=info["provider_address"],
        city=info["citytown"],
        state=info["state"],
        zip_code=info["zip_code"],
        certified_beds=_to_int(info.get("number_of_certified_beds")),
        overall_rating=_to_int(info.get("overall_rating")),
        health_inspection_rating=_to_int(info.get("health_inspection_rating")),
        staffing_rating=_to_int(info.get("staffing_rating")),
        quality_rating=_to_int(info.get("qm_rating")),
        str_hospitalization=metrics["521"],
        str_ed_visit=metrics["522"],
        lt_hospitalization=metrics["551"],
        lt_ed_visit=metrics["552"],
        medicare_care_compare_url=f"{settings.medicare_care_compare_base_url}/{ccn}",
    )
