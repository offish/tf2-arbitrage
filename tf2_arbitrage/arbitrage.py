import asyncio
import json
import logging
import random
import time

import requests
from tf2_utils import Inventory, PricesTF
from websockets import serve
from websockets.asyncio.server import ServerConnection
from websockets.exceptions import ConnectionClosed

from .backpack import BackpackTF
from .cookies import set_cookies
from .database import Database
from .deals import Deals
from .inventory import get_pure_stock
from .options import Options
from .site import SiteEnum
from .sites.quicksell_store import QuicksellStore
from .sites.sfuminator import Sfuminator
from .sites.sites import Site
from .stn import STNTrading
from .utils import (
    can_afford_price,
    dump_to_file,
    get_file_content,
    has_invalid_defindex,
    is_blacklisted,
    worth_less_than,
)


class Arbitrage:
    def __init__(self, options: Options) -> None:
        self.options = options
        self.provider = Inventory(options.inventory_provider, options.inventory_api_key)

        self.db = Database()

        self.stn = STNTrading(options.stn_api_key)
        quicksell_store = QuicksellStore(requests)
        sfuminator = Sfuminator(requests)
        self.backpack_tf = BackpackTF(requests)

        self.sites: list[Site] = [
            self.backpack_tf,
            quicksell_store,
            sfuminator,
        ]
        self.deals = Deals()
        self.saved_deals = []

        # self.prices_tf_socket = PricesTFSocket(self.__on_socket_data)
        self.prices_tf = PricesTF()
        self.prices = {}  # these are pricestf prices
        self.stn_schema = {}
        self.sku_list = []

        self.last_time = 0
        self.sku_index = 0
        # self.stn_check_done = False

        # this is the tf2-express bot
        self.connected_client = None

    def _set_prices_tf_prices(self) -> None:
        logging.info("Getting prices from Prices.TF...")

        if self.options.skip_prices_tf_fetch:
            self.prices = self.db.get_prices_tf_prices()
        else:
            self._get_prices_tf_prices()

        logging.info("Set prices from Prices.TF")

    def _set_stn_schema(self) -> None:
        logging.info("Getting STN schema...")

        if self.options.skip_stn_schema_fetch:
            self.stn_schema = self.db.get_stn_schema()
            self.stn.schema = self.stn_schema
        else:
            self.stn_schema = self.stn.get_sku_schema()

        logging.info(f"Set STN schema with {len(self.stn_schema)} items")

    def _set_inventory(self) -> None:
        logging.info("Getting inventory...")

        if self.options.skip_inventory_fetch:
            inventory = get_file_content("inventory")
        else:
            inventory = self.provider.fetch(self.backpack_tf.our_steam_id)

        self.pure = get_pure_stock(inventory)
        self.deals.pure_stock = self.pure
        self.inventory = inventory

        keys = self.pure["keys"]
        metal = self.pure["metal"]

        logging.info(f"Set inventory with {keys} keys and {metal} ref")

    def _get_site(self, site_name: str) -> Site | None:
        for site in self.sites:
            if site.name != site_name:
                continue

            return site
        return None

    def _get_prices_tf_prices(self) -> None:
        self.prices_tf.request_access_token()
        max_pages = self.options.max_prices_tf_pages
        self.prices = self.prices_tf.get_prices_till_page(max_pages, True)

        dump_to_file("prices_tf_prices", self.prices)

    def _get_site_prices(self) -> None:
        set_cookies(self.sites)
        logging.info("Cookies are up-to-date")

        for site in self.sites:
            # only want to get cookies for bptf
            if site.name == "backpacktf":
                continue

            site.clear_prices()
            site.get_inventories()
            prices = site.get_prices()

            dump_to_file(f"{site.name}_prices", prices)

            self.deals.add_prices(prices, site.name)

    def _get_listing(self, deal_data: dict) -> dict:
        sku = deal_data["sku"]

        # price from pricestf = backpacktf listing we have to buy or sell
        if deal_data["buy_site"] == "pricestf":
            listing = self.backpack_tf.get_lowest_sell(sku, self.prices)

            if not listing:
                return {}

            deal_data["buy_data"] = listing

        if deal_data["sell_site"] == "pricestf":
            listing = self.backpack_tf.get_highest_buy(sku, self.prices)

            if not listing:
                return {}

            deal_data["sell_data"] = listing

        return deal_data

    def _check_non_stn_items(self) -> None:
        prices = self.deals.get_prices()
        temp_deals = []

        for sku in prices:
            if sku in self.stn_schema:
                continue

            deal_data = self.deals.get_deal(sku)

            if not deal_data:
                continue

            if is_blacklisted(deal_data["name"]):
                continue

            deal_data = self._get_listing(deal_data)

            if not deal_data:
                continue

            self.send_message(deal_data)

            logging.info(f"{deal_data}")
            temp_deals.append(deal_data)

        dump_to_file("non_stn_deals", temp_deals)

    def _check_stn_items(self) -> None:
        sku_amount = len(self.sku_list)

        while self.sku_index < sku_amount:
            # {
            # "5021;6": "Mann Co. Supply Crate Key",
            # ...
            # }
            sku = self.sku_list[self.sku_index]
            name = self.stn_schema[sku]
            logging.debug(f"checking {sku=} {name=}")

            self.sku_index += 1

            # item might exist in qs or sfuminator but not in prices.tf
            if sku not in self.prices:
                continue

            # no other site got this sku
            if not self.deals.is_in_prices(sku):
                continue

            if has_invalid_defindex(sku):
                continue

            if is_blacklisted(name):
                continue

            if not can_afford_price(self.prices[sku]["sell"], self.pure):
                continue

            # if price is less than 1 refined skip
            if worth_less_than(self.prices[sku]["buy"], 1.0):
                continue

            # actually fetch the data from stn
            response = self.stn.get_prices(sku)

            if not response:
                self.sku_index -= 1
                continue

            error = response.get("error", "")

            if "many requests" in error.lower():
                # revert as we did not get the price for this iteration
                self.sku_index -= 1
                stn_timeout = self.options.stn_timeout

                logging.warning(f"we are timed out, waiting {stn_timeout} seconds...")
                logging.info(
                    "progress {}/{} ({}%) items".format(
                        self.sku_index,
                        sku_amount,
                        int((self.sku_index / sku_amount) * 100),
                    )
                )
                time.sleep(stn_timeout)
                return

            if not response["success"]:
                logging.warning(f"could not get price of {sku} response {response}")
                continue

            item = response["item"]

            # swap intents, we buy for their sell price etc.
            prices = {"buy": item["pricing"]["sell"], "sell": item["pricing"]["buy"]}

            stock = item["stock"]

            deal_data = self.deals.new_deal(sku, prices)

            if not deal_data:
                continue

            if not self._has_valid_stock(deal_data, stock):
                continue

            deal_data = self._get_listing(deal_data)

            if not deal_data:
                continue

            if "stn" in deal_data["sites"]:
                deal_data["stock"] = stock

            logging.info(f"{deal_data}")
            self.send_message(deal_data)
            self.saved_deals.append(deal_data)

        # reset
        self.sku_index = 0

        dump_to_file("perhaps_stn_deals", self.saved_deals)

        self.saved_deals = []

    def _request_trade(self, deal: dict, intent: str) -> None:
        is_buy = intent == "buy"
        site_name = deal["buy_site"] if is_buy else deal["sell_site"]

        if site_name == "stn":
            asset_id = int(deal.get("our_item", "0"))
            items = deal["name"] if is_buy else [asset_id]
            response = self.stn.request_item_trade(intent, items)
        else:
            site = self._get_site(site_name)
            sku = deal["sku"]

            if site is None:
                logging.error(f"Could not find site {site_name}")
                return

            if is_buy:
                site.fetch_site_inventory()
            else:
                site.fetch_our_inventory()

            response = site.request_trade(sku, intent)

            if not response:
                logging.error(f"Could not request trade for {sku} on {site_name}")
                return

        logging.info(f"Sending after trade {response}")
        self.send_message(response)

    async def send_message(self, message: str | dict | list) -> None:
        if not self.connected_client:
            logging.warning("No client connected, cannot send message")
            return

        if not isinstance(message, str):
            message = json.dumps(message)

        await self.connected_client.send(message)
        logging.info(f"Sent message to client: {message}")

    async def handle_message(self, websocket: ServerConnection, message: str) -> None:
        logging.info(f"Got message from client: {message}")

        data = json.loads(message)

        if data.get("request_buy"):
            self._request_trade(data, "buy")

        if data.get("request_sell"):
            self._request_trade(data, "sell")

    async def handler(self, websocket: ServerConnection) -> None:
        logging.info("A client connected to the WebSocket")
        self.connected_client = websocket

        try:
            async for message in websocket:
                await self.handle_message(websocket, message)

        except ConnectionClosed:
            logging.info("Client disconnected")
        finally:
            self.connected_client = None

    async def serve_websocket(self) -> None:
        logging.info("Starting WebSocket server...")
        stop = asyncio.get_running_loop().create_future()

        async with serve(self.handler, "localhost", 6789):
            await stop

    def setup(self) -> None:
        self._set_inventory()
        self._set_prices_tf_prices()
        self._set_stn_schema()

        self.sku_list = list(self.stn_schema.keys())
        random.shuffle(self.sku_list)

        self.deals.add_prices(self.prices, SiteEnum.PRICES_TF)

    async def start(self) -> None:
        asyncio.create_task(self.serve_websocket())
        self.setup()

        while True:
            if not self.connected_client:
                logging.warning("No client has connected yet...")

            now = time.time()

            if now >= self.last_time + self.options.trading_sites_interval:
                self._get_site_prices()
                self._check_non_stn_items()  # items which does not exist in stn schema
                self.last_time = now

            # self.deals.clear_prices()
            self._check_stn_items()  # items which do exist in stn schema

            await asyncio.sleep(0.1)
