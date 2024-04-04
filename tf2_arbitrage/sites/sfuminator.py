from .sites import Site

import logging

from tf2_sku import to_sku
from tf2_data import QUALITIES, DEFINDEX_NAMES


class Sfuminator(Site):
    def __init__(self, r) -> None:
        name = "sfuminator"
        url = "https://sfuminator.tf/"
        api_url = "https://sfuminator.tf/api"
        headers = {
            "Host": "sfuminator.tf",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",  # noqa
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Referer": "https://sfuminator.tf/",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin",
        }

        super().__init__(r, name, url, api_url, headers)

    def __item_data_to_sku(self, item_name: str, item: dict) -> str:
        if item_name not in DEFINDEX_NAMES:
            return ""

        properties = {
            "defindex": DEFINDEX_NAMES[item_name][0],
            "quality": QUALITIES[item["quality"]],
            "craftable": item["craftable"],
        }

        return to_sku(properties)

    def __format_inventory(self, inventory: dict, intent: str) -> None:
        for item in inventory:
            if "steam_item" not in item:
                logging.warning("No steam_item in inventory, maybe not logged in?")
                return

            item_name = item["steam_item"]["item_name"]
            keys = item["keys"]
            metal = item["metal"]
            asset_id = item["instance_id"]
            sku = self.__item_data_to_sku(item_name, item)

            if not sku:
                continue

            if keys is None:
                keys = 0

            if metal is None:
                metal = 0.0

            self.add_item(sku, intent, item_name, asset_id, keys, metal)

    def fetch_our_inventory(self) -> None:
        inventory = self.get_request("/user-inventory", params={})
        self.__format_inventory(inventory, "sell")

    def fetch_site_inventory(self) -> None:
        inventory = self.get_request("/bot-inventory", params={})
        self.__format_inventory(inventory, "buy")

    def request_trade(self, sku: str, intent: str) -> dict:
        logging.info(f"Requesting {self.name} {intent} for {sku}")

        asset_id = self.get_asset_id_from_sku(sku, intent)
        params = {"instances": [asset_id]}

        if intent == "buy":
            return self.post_request("/trade/sell/action", json=params)

        return self.post_request("/trade/buy/action", json=params)
