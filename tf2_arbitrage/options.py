from dataclasses import dataclass


@dataclass
class Options:
    firefox_profile: str
    steam_id: str
    geckodriver_executable: str = "geckodriver"
    headless: bool = True
    inventory_provider: str = "steamcommunity"
    inventory_api_key: str = ""
    stn_api_key: str = ""
    blacklisted_include: list[str] = None
    blacklisted_listing_detail: list[str] = None
    max_last_bump: float = 60.0
    max_prices_tf_pages: int = 3
    backpack_tf_pages: int = 3
    trading_sites_interval: int = 10 * 60 + 5.19
    stn_timeout: float = 60.0
    skip_stn_schema_fetch: bool = True
    skip_prices_tf_fetch: bool = False
    skip_inventory_fetch: bool = False
