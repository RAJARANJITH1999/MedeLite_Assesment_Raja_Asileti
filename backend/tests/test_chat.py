from app.schemas.chat import ChatFacility
from app.schemas.facility import ClaimsMetric, FacilityData
from app.schemas.manual import ManualInputs
from app.services.chat import SANAVOX_GREETING_MESSAGE, SANAVOX_THANKS_MESSAGE, _greeting_response, _is_in_scope

_METRIC = ClaimsMetric(label="Short Term Hospitalization", facility_value=27.4, national_avg=20.0, state_avg=21.0)

_FACILITY = ChatFacility(
    facility=FacilityData(
        ccn="686123",
        facility_name_from_cms="Kendall Lakes Healthcare and Rehab Center",
        legal_business_name="Kendall Lakes Healthcare and Rehab Center",
        address="123 Main St",
        city="Miami",
        state="FL",
        zip_code="33196",
        certified_beds=150,
        overall_rating=5,
        health_inspection_rating=5,
        staffing_rating=2,
        quality_rating=5,
        str_hospitalization=_METRIC,
        str_ed_visit=_METRIC,
        lt_hospitalization=_METRIC,
        lt_ed_visit=_METRIC,
        medicare_care_compare_url="https://www.medicare.gov/care-compare/details/nursing-home/686123",
    ),
    manual=ManualInputs(),
)


def test_relevant_keyword_question_is_in_scope():
    assert _is_in_scope("Which facility has better staffing?", [_FACILITY]) is True


def test_facility_name_mention_is_in_scope():
    assert _is_in_scope("Tell me about Kendall Lakes", [_FACILITY]) is True


def test_unrelated_question_is_out_of_scope():
    assert _is_in_scope("What's the weather like today?", [_FACILITY]) is False


def test_generic_chitchat_is_out_of_scope():
    assert _is_in_scope("Tell me a joke", [_FACILITY]) is False


def test_hi_is_recognized_as_opening_greeting():
    assert _greeting_response("Hi") == SANAVOX_GREETING_MESSAGE


def test_thank_you_is_recognized_as_closing_courtesy():
    assert _greeting_response("Thank you!") == SANAVOX_THANKS_MESSAGE


def test_real_question_is_not_treated_as_greeting():
    assert _greeting_response("Which facility has better staffing?") is None


def test_unrelated_trivia_is_not_treated_as_greeting():
    assert _greeting_response("What's the weather like today?") is None
