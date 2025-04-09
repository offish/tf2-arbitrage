import json
import logging
from abc import ABC, abstractmethod

import requests
from tf2_utils import SchemaItemsUtils


class Site(ABC):
    def __init__(
        self, site_name: str, url: str, api_url: str, headers: dict = {}
    ) -> None:
        self.session = requests.Session()
        self.session.headers.update(headers)
        self.site_name = site_name
        self.url = url
        self.api_url = api_url

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

    @abstractmethod
    def get_price(self, sku: str) -> dict:
        pass

    def set_cookies(self, cookies: list[dict]) -> None:
        cookie_dict = {cookie["name"]: cookie["value"] for cookie in cookies}
        self.session.cookies.update(cookie_dict)
        logging.debug("cookies set")

    @staticmethod
    def _response_to_json(res: requests.Response) -> dict:
        content = res.content
        logging.debug(f"content: {content=}")

        try:
            return json.loads(content)
        except json.decoder.JSONDecodeError:
            return {}

    @staticmethod
    def _get_asset_ids_key(intent: str) -> str:
        return "site_asset_ids" if intent == "buy" else "our_asset_ids"

    def get_asset_id_from_sku(self, sku: str, intent: str) -> str:
        asset_id_key = self._get_asset_ids_key(intent)
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
        asset_ids_key = self._get_asset_ids_key(intent)

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

    def get_request(self, endpoint: str, params: dict) -> dict:
        """Make a GET request to API endpoint with set cookies and headers"""
        self._sleep_random()
        res = self.session.get(
            self.api_url + endpoint,
            params=params,
        )
        return self._response_to_json(res)

    def post_request(self, endpoint: str, **kwargs) -> dict:
        """
        Make a POST request to API endpoint with set cookies and headers.
        Use json={} or data=\"\"
        """
        res = self.session.post(
            self.api_url + endpoint,
            **kwargs,
        )
        return self._response_to_json(res)
