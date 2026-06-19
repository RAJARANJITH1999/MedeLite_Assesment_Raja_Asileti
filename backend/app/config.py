from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")

    cms_api_base_url: str = "https://data.cms.gov/provider-data/api/1"
    medicare_care_compare_base_url: str = "https://www.medicare.gov/care-compare/details/nursing-home"
    cors_allow_origins: list[str] = ["http://localhost:8000"]

    # CMS Provider Data Catalog distribution UUIDs, verified live 2026-06-18.
    # See PROJECT.md section 5 for how to re-derive these if CMS rotates them.
    cms_provider_info_distribution: str = "588f22e8-145d-5db5-baff-f59ce253316c"
    cms_claims_measures_distribution: str = "19fa35fb-11f0-5ed8-999e-52f272a25b01"
    cms_state_us_averages_distribution: str = "03e812a4-7576-5b9b-8cd7-2135649118f4"

    openai_api_key: str | None = None
    openai_model: str = "gpt-4o-mini"


settings = Settings()
