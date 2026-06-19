import asyncio

import httpx

from app.config import settings


class CCNNotFoundError(Exception):
    def __init__(self, ccn: str):
        self.ccn = ccn
        super().__init__(f"No CMS Provider Information record for CCN {ccn!r}")


class CMSAPIError(Exception):
    pass


async def _query(
    client: httpx.AsyncClient,
    distribution_id: str,
    conditions: list[tuple[str, str]] | None = None,
) -> dict:
    params: list[tuple[str, str]] = []
    for i, (prop, value) in enumerate(conditions or []):
        params.append((f"conditions[{i}][property]", prop))
        params.append((f"conditions[{i}][value]", value))
        params.append((f"conditions[{i}][operator]", "="))

    url = f"{settings.cms_api_base_url}/datastore/query/{distribution_id}"
    try:
        response = await client.get(url, params=params, timeout=10.0)
        response.raise_for_status()
    except httpx.HTTPError as exc:
        raise CMSAPIError(f"CMS API request failed: {exc}") from exc
    return response.json()


async def fetch_facility_raw_data(ccn: str) -> dict:
    """Fetch and bundle everything mapping.py needs for one CCN.

    Provider info determines the facility's state, which the averages
    query needs, so provider info is fetched first and the remaining two
    calls run concurrently.
    """
    async with httpx.AsyncClient() as client:
        provider_data = await _query(
            client,
            settings.cms_provider_info_distribution,
            conditions=[("cms_certification_number_ccn", ccn)],
        )
        provider_results = provider_data.get("results", [])
        if not provider_results:
            raise CCNNotFoundError(ccn)
        provider_info = provider_results[0]
        state = provider_info["state"]

        claims_data, nation_avg_data, state_avg_data = await asyncio.gather(
            _query(
                client,
                settings.cms_claims_measures_distribution,
                conditions=[("cms_certification_number_ccn", ccn)],
            ),
            _query(
                client,
                settings.cms_state_us_averages_distribution,
                conditions=[("state_or_nation", "NATION")],
            ),
            _query(
                client,
                settings.cms_state_us_averages_distribution,
                conditions=[("state_or_nation", state)],
            ),
        )

    return {
        "provider_info": provider_info,
        "claims_measures": claims_data.get("results", []),
        "nation_averages": (nation_avg_data.get("results") or [{}])[0],
        "state_averages": (state_avg_data.get("results") or [{}])[0],
    }
