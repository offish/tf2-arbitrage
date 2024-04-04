from .sites import Site

from datetime import datetime, timezone
import logging

from tf2_utils import to_refined, to_scrap
from tf2_sku import to_sku
from tf2_data import QUALITIES


class QuicksellStore(Site):
    def __init__(self, r) -> None:
        name = "quicksell"
        url = "https://quicksell.store/"
        api_url = "https://quicksell.store/api"
        headers = {
            "Host": "quicksell.store",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",  # noqa
            "Accept": "*/*",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate, br",
            "Referer": "https://quicksell.store/",
            "Content-Type": "application/json",
            "Origin": "https://quicksell.store",
            "Connection": "keep-alive",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin",
            "TE": "trailers",
        }

        super().__init__(r, name, url, api_url, headers)

        self.filters = {
            "ours": {
                "classies": False,
                "filter": {
                    "name": "",
                    "class": [],
                    "quality": [],
                    "type": [],
                    "effect": [],
                    "price": {
                        "from": {"keys": 0, "ref": 0},
                        "to": {"keys": 0, "ref": 0},
                    },
                },
                # low-to-high
                "sort": "l2h",
                # "sort": "h2l",
            },
            "theirs": {
                "filter": {
                    "showNoPrice": False,
                    "name": "",
                    "class": [],
                    "quality": [],
                    "type": [],
                    "effect": [],
                    "price": {
                        "from": {"keys": 0, "ref": 0},
                        "to": {"keys": 0, "ref": 0},
                    },
                },
                "sort": "l2h",
                # "sort": "h2l",
            },
        }
        # self.utils = SchemaItemsUtils()

    def __item_data_to_sku(self, item_name: str, item: dict) -> str:
        craftable = item_name.find("Non-Craftable") == -1

        properties = {
            "defindex": self.utils.name_to_defindex(item["baseName"]),
            "quality": QUALITIES[item["quality"]],
            "craftable": craftable,
        }

        return to_sku(properties)

    def __format_inventory(self, inventory: dict, intent: str) -> None:
        if not inventory:
            logging.warning("No inventory found")
            return

        for item in inventory["inv"]:
            item_data = item["data"]
            item_name = item["name"]
            # logging.debug(f"{item}")
            # TODO: fix
            keys = 0
            metal = to_refined(item["scrap"])
            asset_id = item["assetid"]
            sku = self.__item_data_to_sku(item["name"], item_data)

            self.add_item(sku, intent, item_name, asset_id, keys, metal)

    def __can_afford(self, our_stock: dict, their_scrap: int) -> bool:
        our_scrap = to_scrap(our_stock["keys"] * 63.0 + our_stock["metal"])
        return our_scrap >= their_scrap

    def __fetch_till_cant_afford(self) -> dict:
        inventory = {"inv": []}
        pure_stock = {"keys": 0, "metal": 50.11}
        their_scrap = 0
        loaded = 0

        while self.__can_afford(
            pure_stock, their_scrap
        ) and self.__is_correct_increment(loaded):
            json = {
                "side": "ours",
                "filters": self.filters,
                # these increment by 80
                "loaded": {"ours": loaded, "theirs": 0},
            }

            response = self.post_request("/load_inventory", json=json)

            if "inv" not in response:
                return {}

            inventory["inv"] += response["inv"]

            for item in response["inv"]:
                their_scrap = item["scrap"]

            loaded += len(inventory["inv"])

        return inventory

    def __is_correct_increment(self, number: int) -> bool:
        return number % 80 == 0

    def __fetch_till_wrong_increment(self) -> dict:
        inventory = {"inv": []}
        loaded = 0
        last_loaded = -1

        # 0 items in inventory is edge case
        while self.__is_correct_increment(loaded) and loaded != last_loaded:
            last_loaded = loaded
            json = {
                "side": "theirs",
                "filters": self.filters,
                # these increment by 80
                "loaded": {"ours": 0, "theirs": loaded},
            }

            response = self.post_request("/load_inventory", json=json)

            if "inv" not in response:
                return {}

            inventory["inv"] += response["inv"]

            # amount of items
            loaded += len(response["inv"])

        return inventory

    def fetch_our_inventory(self) -> None:
        self.clear_prices()
        inventory = self.__fetch_till_wrong_increment()
        self.__format_inventory(inventory, "sell")

    def fetch_site_inventory(self) -> None:
        self.clear_prices()
        inventory = self.__fetch_till_cant_afford()
        self.__format_inventory(inventory, "buy")

    def request_trade(self, sku: str, intent: str) -> dict:
        logging.info(f"Requesting {self.name} {intent} for {sku}")

        current_utc_time = datetime.now(timezone.utc)
        formatted_date = current_utc_time.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"

        json = {
            "their_items": [],
            "our_items": [],
            "game": "tf2",
            # "value": -13,
            "mobile": False,
            "pageLoaded": formatted_date,
        }

        items_key = "our_items" if intent == "buy" else "their_items"

        if sku not in self.prices:
            logging.warning(f"no price for {sku}")
            return {}

        item = self.prices[sku]
        item_name = item["name"]
        item_price = to_scrap(item[intent]["metal"])

        # select first asset_id
        asset_id = self.get_asset_id_from_sku(sku, intent)

        json[items_key].append(
            {
                "assetid": asset_id,
                "name": item_name,
                "price": item_price,
                "bonus": False,
            }
        )

        # TODO: test selling (if the minus part works unsure)
        json["value"] = -item_price if intent == "buy" else item_price

        return self.post_request("/trade", json=json)

        # {
        #     "their_items": [],
        #     "our_items": [
        #         {
        #             "assetid": "14016483635",
        #             "name": "Wet Works",
        #             "price": 13,
        #             "bonus": False,
        #         }
        #     ],
        #     "game": "tf2",
        #     "value": -13,
        #     "mobile": False,
        #     "pageLoaded": "2024-01-06T19:35:53.988Z",
        # }
