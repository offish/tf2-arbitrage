import json
import logging

from ..config import FIREFOX_PROFILE_PATH, HEADLESS, STEAM_ID
import time
import random

import requests
from selenium.webdriver import FirefoxOptions, FirefoxProfile

from tf2_utils import SchemaItemsUtils


class Site:
    def __init__(
        self, r: requests, name: str, url: str, api_url: str, headers: dict = {}
    ) -> None:
        # requests
        self.r = r
        self.session = r.Session()
        self.session.headers.update(headers)

        # specifics
        self.name = name
        self.url = url
        self.api_url = api_url

        # selenium if we get javascript challenges
        self.options = FirefoxOptions()
        self.options.headless = HEADLESS
        self.options.profile = FirefoxProfile(FIREFOX_PROFILE_PATH)

        # data
        self.our_steam_id = STEAM_ID
        self.prices = {}
        # self.site_inventory = {}
        # self.our_inventory = {}
        self.last_fetch = 0
        self.utils = SchemaItemsUtils()

    def get_prices(self) -> dict:
        """
        {
            "5021;6": {
                "buy": {"keys": 0, "metal": 50.33},
                "sell": {"keys": 0, "metal": 50.44},
                "site_asset_ids": [],
                "our_asset_ids": []
            },
            ...
        }
        """
        return self.prices

    def clear_prices(self) -> None:
        self.prices = {}

    def fetch_site_inventory(self) -> None: ...

    # def get_site_inventory(self) -> dict:
    #     return self.site_inventory

    def fetch_our_inventory(self) -> None: ...

    def get_inventories(self) -> None:
        """Get site and our inventories"""
        self.fetch_site_inventory()
        self.fetch_our_inventory()
        logging.info(f"got inventories from {self.name}")

    def request_trade(self, sku: str, intent: str) -> dict: ...

    # def get_our_inventory(self) -> dict:
    #     return self.our_inventory

    def get_price(self, sku: str) -> dict:
        """
        {
            "buy": {"keys": 0, "metal": 50.33},
            "sell": {"keys": 0, "metal": 50.44}
        }
        """
        return self.prices[sku]

    def set_cookies(self, cookies: list) -> None:
        cookie_dict = {cookie["name"]: cookie["value"] for cookie in cookies}
        self.session.cookies.update(cookie_dict)
        logging.debug("cookies set")

    @staticmethod
    def __get_content_from_response(res: requests.Response) -> str:
        # TODO: check if compressed with brotli
        # for some reason quicksell this condition is true
        # but the decompression does not work

        # if res.headers.get("Content-Encoding") == "br":
        #     return brotli.decompress(res.content)

        # logging.debug(f"{res.content}")

        return res.content

    def __response_to_json(self, res: requests.Response) -> dict:
        content = self.__get_content_from_response(res)
        # logging.debug(f"content: {content}")

        # if "Enable JavaScript and cookies to continue" in content.decode("utf-8"):
        #     self.driver = Firefox(options=self.options)
        #     logging.info("got javascript challenge, launching selenium")
        #     self.driver.get(res.url)

        #     time.sleep(5)

        #     content = self.driver.page_source
        #     self.driver.quit()
        try:
            return json.loads(content)
        except json.decoder.JSONDecodeError:
            return {}

    @staticmethod
    def __get_asset_ids_key(intent: str) -> str:
        return "site_asset_ids" if intent == "buy" else "our_asset_ids"

    def get_asset_id_from_sku(self, sku: str, intent: str) -> str:
        asset_id_key = self.__get_asset_ids_key(intent)
        return self.prices[sku][asset_id_key][0]

    def add_item(
        self,
        sku: str,
        intent: str,
        item_name: str,
        asset_id: str,
        keys: int,
        metal: float,
        steam_id: str = "",
    ) -> None:
        """Add an item to prices"""
        asset_ids_key = self.__get_asset_ids_key(intent)

        if sku not in self.prices:
            self.prices[sku] = {
                intent: {"keys": keys, "metal": metal},
                asset_ids_key: [asset_id],
                "name": item_name,
            }

            if intent == "buy":
                # first steam_id matches the first asset_id
                # needed for sending trades
                self.prices[sku]["steam_id"] = steam_id

        else:
            # sku is already in the pricelist
            if intent not in self.prices[sku]:
                self.prices[sku][intent] = {"keys": keys, "metal": metal}

            if asset_ids_key not in self.prices[sku]:
                self.prices[sku][asset_ids_key] = [asset_id]
            else:
                self.prices[sku][asset_ids_key].append(asset_id)

    def __sleep_random(self) -> None:
        sleep_time = random.random()  # [0,1)
        time.sleep(sleep_time)

    def get_request(self, endpoint: str, params: dict) -> dict:
        """Make a GET request to API endpoint with set cookies and headers"""
        self.__sleep_random()
        res = self.session.get(
            self.api_url + endpoint,
            params=params,
        )
        return self.__response_to_json(res)

    def post_request(self, endpoint: str, **kwargs) -> dict:
        """
        Make a POST request to API endpoint with set cookies and headers.
        Use json={} or data=\"\"
        """
        self.__sleep_random()
        res = self.session.post(
            self.api_url + endpoint,
            **kwargs,
        )
        return self.__response_to_json(res)
