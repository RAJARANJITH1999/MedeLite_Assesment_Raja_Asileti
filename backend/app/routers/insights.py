from fastapi import APIRouter

from app.schemas.report import InsightsRequest, InsightsResponse
from app.services.insights import generate_insights

router = APIRouter(prefix="/insights", tags=["insights"])


@router.post("", response_model=InsightsResponse)
async def post_insights(request: InsightsRequest) -> InsightsResponse:
    return await generate_insights(request.facility, request.manual)
