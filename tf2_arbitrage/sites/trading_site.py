import logging
from abc import abstractmethod

from selenium.webdriver import FirefoxOptions, FirefoxProfile

from ..config import FIREFOX_PROFILE_PATH, HEADLESS, STEAM_ID
from .site import Site


class TradingSite(Site):
    def __init__(self, site_name: str, url: str, api_url: str, headers: dict = {}):
        super().__init__(site_name, url, api_url, headers)

        self.options = FirefoxOptions()
        self.options.headless = HEADLESS
        self.options.profile = FirefoxProfile(FIREFOX_PROFILE_PATH)
        self.our_steam_id = STEAM_ID

    @abstractmethod
    def fetch_site_inventory(self) -> None:
        pass

    @abstractmethod
    def fetch_our_inventory(self) -> None:
        pass

    def get_inventories(self) -> None:
        """Get site and our inventories"""
        self.fetch_site_inventory()
        self.fetch_our_inventory()
        logging.info(f"Got inventories from {self.site_name}")

    @abstractmethod
    def request_trade(self, sku: str, intent: str) -> dict:
        pass
