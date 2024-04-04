from .sites import Site

from bs4 import BeautifulSoup
from tf2_utils import to_refined
from tf2_sku import to_sku


class STNTrading(Site):
    def __init__(self, r) -> None:
        name = "stn"
        url = "https://stntrading.eu"
        api_url = "https://stntrading.eu/backend/tf2"
        headers = {
            "Host": "stntrading.eu",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",  # noqa
            "Accept": "*/*",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate, br",
            "Referer": "https://stntrading.eu/buy/hats/3",
            "Connection": "keep-alive",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin",
            "TE": "trailers",
        }

        super().__init__(r, name, url, api_url, headers)

    def __item_data_to_sku(self, item) -> str:
        item_name = item.get("name")
        craftable = item_name.find("Non-Craftable") == -1

        properties = {
            "defindex": self.utils.name_to_defindex(item_name),
            "quality": int(item.get("quality")),
            "craftable": craftable,
        }

        return to_sku(properties)

    def __format_html_inventory(self, html: str, intent: str, steam_id: str) -> None:
        soup = BeautifulSoup(html, "html.parser")

        for item in soup.find_all("div", class_="inventoryItem position-relative"):
            can_buy = int(item.get("canbuy"))

            # if they cant even buy 1 skip
            if not can_buy:
                continue

            asset_id = item.get("itemid")
            item_name = item.get("name")
            keys = int(item.get("keyval"))
            metal = to_refined(int(item.get("scrapval")))
            sku = self.__item_data_to_sku(item)

            self.add_item(sku, intent, item_name, asset_id, keys, metal, steam_id)

    def fetch_site_inventory(self) -> None:
        steam_id = "76561198310024994"
        params = {
            # TODO: get this for each bot they have
            "steamId": steam_id,
            "displayPage": "buyPage",
            "category": "Hats",
        }
        response = self.get_request("/tf2InventoryPageAjax", params)

        if "html" not in response:
            return

        self.__format_html_inventory(response["html"], "buy", steam_id)

    def fetch_our_inventory(self) -> None:
        params = {
            "steamId": self.our_steam_id,
            "displayPage": "sellPage",
            "category": "",
        }

        response = self.get_request("/tf2InventoryPageAjax", params)

        if "html" not in response:
            return

        self.__format_html_inventory(response["html"], "sell", self.our_steam_id)

    def request_trade(self, sku: str, intent: str) -> dict:
        bot_steam_id = self.prices[sku]["steam_id"]
        asset_id = int(self.get_asset_id_from_sku(sku, intent))

        form_data = {
            "fullRequest": {
                "request_type": "buy_fully_qualified_item_instances",
                "buy_fully_qualified_item_instances": {
                    "app_ctx_id": "440_2",
                    "bot_steam64": bot_steam_id,
                    "assets": [asset_id],
                },
            }
        }

        return self.post_request("/tradeQueue", data=form_data)
