from app.config import settings
from app.schemas.chat import ChatFacility, ChatResponse
from app.services.insights import build_facility_facts

SANAVOX_SYSTEM_PROMPT = (
    "You are Sanavox, a careful healthcare-operations assistant. You answer questions "
    "about one or more skilled nursing facilities being compared, using ONLY the CMS "
    "and manual data provided below. If the data doesn't contain the answer, say so "
    "plainly instead of guessing or inventing numbers. Keep answers to 2-4 sentences, "
    "no markdown headers."
)

SANAVOX_OFF_TOPIC_MESSAGE = (
    "Sanavox only answers questions about the facility reports and comparisons shown "
    "on this page — things like star ratings, hospitalization/ED metrics, census, EMR, "
    "or coverage details. That question doesn't look related, so it hasn't used up one "
    "of your preview questions. Please ask something about the reports above."
)

# Deterministic keyword gate — catches obviously off-topic questions (chit-chat,
# general trivia, unrelated requests) before spending an OpenAI call on them.
_RELEVANT_KEYWORDS = (
    "facility", "facilities", "report", "compare", "comparison", "rating",
    "rated", "star", "inspection", "staffing", "staff", "quality", "resident",
    "care", "hospitalization", "hospitalize", "hospital", "emergency",
    "ed visit", "visit", "census", "bed", "beds", "emr", "medicare", "ccn",
    "location", "address", "state", "national", "average", "patient",
    "coverage", "medical", "performance", "score", "percent", "percentage",
    "metric", "measure", "snapshot", "better", "worse", "compared",
)


def _is_in_scope(question: str, facilities: list[ChatFacility]) -> bool:
    text = question.lower()
    if any(keyword in text for keyword in _RELEVANT_KEYWORDS):
        return True
    for item in facilities:
        for word in item.facility.facility_name_from_cms.lower().split():
            if len(word) > 3 and word in text:
                return True
    return False


def _build_context(facilities: list[ChatFacility]) -> str:
    blocks = [
        f"--- Facility {i}: {item.facility.facility_name_from_cms} ---\n"
        + build_facility_facts(item.facility, item.manual)
        for i, item in enumerate(facilities, start=1)
    ]
    return "\n\n".join(blocks)


async def answer_question(facilities: list[ChatFacility], question: str) -> ChatResponse:
    if not _is_in_scope(question, facilities):
        return ChatResponse(answer=SANAVOX_OFF_TOPIC_MESSAGE, generated_by="filtered")

    if not settings.openai_api_key:
        return ChatResponse(
            answer=(
                "Sanavox needs an OpenAI API key configured on this deployment to answer "
                "questions — none is set right now."
            ),
            generated_by="unavailable",
        )

    from openai import AsyncOpenAI

    client = AsyncOpenAI(api_key=settings.openai_api_key)
    context = _build_context(facilities)
    try:
        response = await client.chat.completions.create(
            model=settings.openai_model,
            messages=[
                {"role": "system", "content": SANAVOX_SYSTEM_PROMPT},
                {"role": "user", "content": f"Facility data:\n{context}\n\nQuestion: {question}"},
            ],
            max_tokens=220,
        )
        answer = response.choices[0].message.content.strip()
        return ChatResponse(answer=answer, generated_by=f"openai:{settings.openai_model}")
    except Exception:
        return ChatResponse(
            answer="Sanavox couldn't reach the AI service just now — please try again in a moment.",
            generated_by="error",
        )
