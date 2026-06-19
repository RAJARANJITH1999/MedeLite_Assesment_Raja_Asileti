import re

from fastapi import APIRouter, HTTPException

from app.schemas.facility import FacilityData
from app.services.cms_client import CCNNotFoundError, CMSAPIError, fetch_facility_raw_data
from app.services.mapping import map_facility_data

router = APIRouter(prefix="/facilities", tags=["facilities"])

_CCN_PATTERN = re.compile(r"^[A-Za-z0-9]{6}$")


@router.get("/{ccn}", response_model=FacilityData)
async def get_facility(ccn: str) -> FacilityData:
    if not _CCN_PATTERN.match(ccn):
        raise HTTPException(
            status_code=422,
            detail={"error": "invalid_ccn", "message": "CCN must be 6 alphanumeric characters."},
        )

    try:
        raw = await fetch_facility_raw_data(ccn)
    except CCNNotFoundError:
        raise HTTPException(
            status_code=404,
            detail={"error": "ccn_not_found", "ccn": ccn},
        )
    except CMSAPIError as exc:
        raise HTTPException(
            status_code=502,
            detail={"error": "cms_api_unavailable", "message": str(exc)},
        )

    return map_facility_data(ccn, raw)
