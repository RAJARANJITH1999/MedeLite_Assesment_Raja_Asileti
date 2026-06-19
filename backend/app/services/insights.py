from app.config import settings
from app.schemas.facility import ClaimsMetric, FacilityData
from app.schemas.manual import ManualInputs
from app.schemas.report import InsightsResponse

SYSTEM_PROMPT = (
    "You are a healthcare operations analyst writing a 3-4 sentence plain-English "
    "summary of a skilled nursing facility's CMS performance data for an internal "
    "outreach team. Be specific with numbers, note where the facility beats or "
    "trails state/national averages, and flag anything that looks like a risk or "
    "a strength. No preamble, no markdown headers, just the summary text."
)


def _round(value: float) -> float:
    return round(value, 2)


def _metric_line(metric: ClaimsMetric) -> str:
    if metric.facility_value is None:
        return f"{metric.label}: not enough data"
    parts = [f"{metric.label}: facility {_round(metric.facility_value)}{metric.unit}"]
    if metric.national_avg is not None:
        parts.append(f"national avg {_round(metric.national_avg)}{metric.unit}")
    if metric.state_avg is not None:
        parts.append(f"state avg {_round(metric.state_avg)}{metric.unit}")
    return ", ".join(parts)


def build_facility_facts(facility: FacilityData, manual: ManualInputs) -> str:
    lines = [
        f"Facility: {facility.facility_name_from_cms} ({facility.city}, {facility.state})",
        f"Certified beds: {facility.certified_beds}",
        f"Overall rating: {facility.overall_rating}/5, Health Inspection: "
        f"{facility.health_inspection_rating}/5, Staffing: {facility.staffing_rating}/5, "
        f"Quality of Resident Care: {facility.quality_rating}/5",
        _metric_line(facility.str_hospitalization),
        _metric_line(facility.str_ed_visit),
        _metric_line(facility.lt_hospitalization),
        _metric_line(facility.lt_ed_visit),
    ]
    if manual.current_census and facility.certified_beds:
        occupancy = round(100 * manual.current_census / facility.certified_beds, 1)
        lines.append(f"Current census: {manual.current_census} ({occupancy}% occupancy)")
    if manual.patient_type:
        lines.append(f"Patient type: {manual.patient_type}")
    return "\n".join(lines)


def _rule_based_summary(facility: FacilityData, manual: ManualInputs) -> str:
    sentences = []

    if facility.overall_rating is not None:
        tier = "strong" if facility.overall_rating >= 4 else "weak" if facility.overall_rating <= 2 else "moderate"
        sentences.append(
            f"{facility.facility_name_from_cms} carries a {tier} {facility.overall_rating}/5 overall "
            f"CMS rating, with staffing at {facility.staffing_rating}/5 and quality of resident care "
            f"at {facility.quality_rating}/5."
        )

    for metric in (facility.str_hospitalization, facility.lt_hospitalization):
        if metric.facility_value is None or metric.national_avg is None:
            continue
        direction = "above" if metric.facility_value > metric.national_avg else "below"
        sentences.append(
            f"{metric.label} is {_round(metric.facility_value)}{metric.unit}, {direction} the national "
            f"average of {_round(metric.national_avg)}{metric.unit}."
        )

    if manual.current_census and facility.certified_beds:
        occupancy = round(100 * manual.current_census / facility.certified_beds, 1)
        sentences.append(
            f"Current census of {manual.current_census} against {facility.certified_beds} certified "
            f"beds puts occupancy at roughly {occupancy}%."
        )

    if not sentences:
        sentences.append("Not enough CMS data was available to generate a meaningful summary.")

    return " ".join(sentences)


async def generate_insights(facility: FacilityData, manual: ManualInputs) -> InsightsResponse:
    if not settings.openai_api_key:
        return InsightsResponse(
            summary=_rule_based_summary(facility, manual),
            generated_by="rule-based",
        )

    from openai import AsyncOpenAI

    client = AsyncOpenAI(api_key=settings.openai_api_key)
    try:
        response = await client.chat.completions.create(
            model=settings.openai_model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": build_facility_facts(facility, manual)},
            ],
            max_tokens=220,
        )
        summary = response.choices[0].message.content.strip()
        return InsightsResponse(summary=summary, generated_by=f"openai:{settings.openai_model}")
    except Exception:
        return InsightsResponse(
            summary=_rule_based_summary(facility, manual),
            generated_by="rule-based-fallback",
        )
