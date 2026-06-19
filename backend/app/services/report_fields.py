from app.schemas.facility import ClaimsMetric
from app.schemas.report import ReportPayload


def _fmt_int(value: int | None) -> str:
    return str(value) if value is not None else "N/A"


def _fmt_percent(value: float | None) -> str:
    return f"{value:.1f}%" if value is not None else "N/A"


def _fmt_rate(value: float | None) -> str:
    return f"{value:.2f}" if value is not None else "N/A"


def build_report_rows(payload: ReportPayload) -> list[tuple[str, str]]:
    """Ordered (label, value) pairs matching Facility Assessment Snapshot.docx exactly."""
    f = payload.facility
    m = payload.manual

    def metric_row_percent(metric: ClaimsMetric) -> tuple[str, str, str]:
        return (_fmt_percent(metric.facility_value), _fmt_percent(metric.national_avg), _fmt_percent(metric.state_avg))

    def metric_row_rate(metric: ClaimsMetric) -> tuple[str, str, str]:
        return (_fmt_rate(metric.facility_value), _fmt_rate(metric.national_avg), _fmt_rate(metric.state_avg))

    str_hosp_val, str_hosp_nat, str_hosp_state = metric_row_percent(f.str_hospitalization)
    str_ed_val, str_ed_nat, str_ed_state = metric_row_percent(f.str_ed_visit)
    lt_hosp_val, lt_hosp_nat, lt_hosp_state = metric_row_rate(f.lt_hospitalization)
    lt_ed_val, lt_ed_nat, lt_ed_state = metric_row_rate(f.lt_ed_visit)

    return [
        ("Name of Facility", payload.display_name),
        ("Location", f"{f.address}, {f.city}, {f.state}"),
        ("EMR", m.emr or "N/A"),
        ("Census Capacity", _fmt_int(f.certified_beds)),
        ("Current Census", _fmt_int(m.current_census)),
        ("Type of Patient", m.patient_type or "N/A"),
        ("Previous Coverage from Medelite", m.previous_coverage or "N/A"),
        ("Previous Provider Performance from Medelite", m.previous_performance or "N/A"),
        ("Medical Coverage", m.medical_coverage or "N/A"),
        ("Overall Star Rating", _fmt_int(f.overall_rating)),
        ("Health Inspection", _fmt_int(f.health_inspection_rating)),
        ("Staffing", _fmt_int(f.staffing_rating)),
        ("Quality of Resident Care", _fmt_int(f.quality_rating)),
        ("Short Term Hospitalization", str_hosp_val),
        ("STR National Avg. for Hospitalization", str_hosp_nat),
        ("STR State National Avg. for Hospitalization", str_hosp_state),
        ("STR ED Visit", str_ed_val),
        ("STR ED Visits National Avg.", str_ed_nat),
        ("STR ED Visits State Avg.", str_ed_state),
        ("LT Hospitalization", lt_hosp_val),
        ("LT National Avg. for Hospitalization", lt_hosp_nat),
        ("LT State National Avg. for Hospitalization", lt_hosp_state),
        ("ED Visit", lt_ed_val),
        ("LT ED Visits National Avg.", lt_ed_nat),
        ("LT ED Visits State Avg.", lt_ed_state),
    ]
