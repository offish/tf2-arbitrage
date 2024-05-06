from .sites.quicksell_store import QuicksellStore
from .sites.sfuminator import Sfuminator
from .sites.sites import Site
from .backpack import BackpackTF
from .cookies import set_cookies
from .config import (
    MAX_PRICES_TF_PAGES,
    SKIP_PRICES_TF_FETCH,
    PRICES_TF_FILE,
    STN_API_KEY,
    STN_TIMEOUT,
    TRADING_SITES_INTERVAL,
    INVENTORY_PROVIDER,
    INVENTORY_API_KEY,
    SKIP_INVENTORY_FETCH,
    SKIP_STN_SCHEMA_FETCH,
    INVENTORY_PURE_STOCK,
    STN_SCHEMA_PATH,
)
from .deals import Deals
from .utils import (
    dump_to_json_file,
    read_json_file,
    can_afford_price,
    has_invalid_defindex,
    worth_less_than,
    is_blacklisted,
    get_file_name,
    encode_data,
    decode_data,
    compress_message,
)
from .stn import STNTrading

from threading import Thread
import logging
import socket
import random
import time

from tf2_utils import PricesTF, to_refined, Inventory, map_inventory
import requests as r


class Arbitrage:
    def __init__(self) -> None:
        self.provider = Inventory(INVENTORY_PROVIDER, INVENTORY_API_KEY)

        self.stn = STNTrading(STN_API_KEY)
        quicksell_store = QuicksellStore(r)
        sfuminator = Sfuminator(r)
        # stn_trading = STNTrading(r)
        self.backpack_tf = BackpackTF(r)

        self.sites: list[Site] = [
            self.backpack_tf,
            quicksell_store,
            sfuminator,
            # stn_trading,
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

        # NOTE: socket
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        server_address = ("localhost", 12345)
        self.server_socket.bind(server_address)
        self.server_socket.listen(1)
        self.connection = None

        logging.info("Socket listening for connections...")

    def __get_site(self, site_name: str) -> Site | None:
        for site in self.sites:
            if site.name != site_name:
                continue

            return site
        return None

    def __set_inventory_pure(self) -> None:
        stock = {"keys": 0, "metal": 0.0}
        scrap = 0
        inventory = self.provider.fetch(self.backpack_tf.our_steam_id)

        for item in map_inventory(inventory, True):
            sku = item["sku"]

            if not item["tradable"]:
                continue

            match sku:
                case "5021;6":
                    stock["keys"] += 1

                case "5002;6":
                    scrap += 9

                case "5001;6":
                    scrap += 3

                case "5000;6":
                    scrap += 1

                case _:
                    pass

        stock["metal"] = to_refined(scrap)
        self.pure = stock
        self.deals.pure_stock = self.pure

        logging.info(f"got inventory pure {stock}")

    def on_socket_data(self, data: dict) -> None:
        # update self.prices
        # self.deals.update_price()

        # TODO: FIX THIS
        return

        prices = self.__format_prices_tf_price(data)
        self.deals.update_price(data["sku"], prices)

        print(data)

    # def __sort_by_profit(self, deals: list[dict]) -> list[dict]:
    #     return sorted(deals, key=lambda x: x["profit"], reverse=True)

    def __get_prices_tf_prices(self) -> None:
        self.prices_tf.request_access_token()
        self.prices = self.prices_tf.get_prices_till_page(MAX_PRICES_TF_PAGES, True)

        file_name = get_file_name("prices")
        dump_to_json_file(self.prices, file_name)

    def __get_site_prices(self) -> None:
        set_cookies(self.sites)
        logging.info("cookies are up-to-date")

        for site in self.sites:
            # only want to get cookies for bptf
            if site.name == "backpacktf":
                continue

            site.clear_prices()
            site.get_inventories()
            prices = site.get_prices()

            file_name = get_file_name(site.name)
            dump_to_json_file(prices, file_name)

            self.deals.add_prices(prices, site.name)

    def __is_overstocked(self, stock: dict) -> bool:
        return stock["level"] >= stock["limit"]

    def __is_in_stock(self, stock: dict) -> bool:
        return stock["level"] > 0

    def __has_valid_stock(self, deal_data: dict, stock: dict) -> bool:
        # make sure they have item in stock
        if deal_data["buy_site"] == "stn":
            if not self.__is_in_stock(stock):
                return False

        # make sure not overstocked
        if deal_data["sell_site"] == "stn":
            if self.__is_overstocked(stock):
                return False

        return True

    def __get_listing(self, deal_data: dict) -> dict:
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

    def __check_non_stn_items(self) -> None:
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

            deal_data = self.__get_listing(deal_data)

            if not deal_data:
                continue

            self.send(deal_data)

            logging.info(f"{deal_data}")
            temp_deals.append(deal_data)

        file_name = get_file_name("non_deals")
        dump_to_json_file(temp_deals, file_name)

    def __check_stn_items(self) -> None:
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

                logging.warning(f"we are timed out, waiting {STN_TIMEOUT} seconds...")
                logging.info(
                    "progress {}/{} ({}%) items".format(
                        self.sku_index,
                        sku_amount,
                        int((self.sku_index / sku_amount) * 100),
                    )
                )
                time.sleep(STN_TIMEOUT)
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

            if not self.__has_valid_stock(deal_data, stock):
                continue

            deal_data = self.__get_listing(deal_data)

            if not deal_data:
                continue

            if "stn" in deal_data["sites"]:
                deal_data["stock"] = stock

            logging.info(f"{deal_data}")
            self.send(deal_data)
            self.saved_deals.append(deal_data)

        # reset
        self.sku_index = 0

        file_name = get_file_name("perhaps_stn_deals")
        dump_to_json_file(self.saved_deals, file_name)

        self.saved_deals = []

    def send(self, data: dict) -> None:
        if not self.connection:
            logging.warning("No connection, cannot send data")
            return

        message = compress_message(data)

        logging.info(f"Sending socket {message}")
        self.connection.sendto(encode_data(message), self.client_address)

    def __request_trade(self, deal: dict, intent: str) -> None:
        is_buy = intent == "buy"
        site_name = deal["buy_site"] if is_buy else deal["sell_site"]

        if site_name == "stn":
            # this is assetid
            our_item = int(deal.get("our_item", "0"))

            items = deal["name"] if is_buy else [our_item]
            response = self.stn.request_item_trade(intent, items)

        else:
            site = self.__get_site(site_name)
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
        self.send(response)

    def listen(self):
        while True:
            # Wait for a connection
            self.connection, self.client_address = self.server_socket.accept()

            try:
                print("Connection established with", self.client_address)

                while True:
                    # Receive data from the client
                    data = self.connection.recv(1024)

                    if not data:
                        break  # break out of the loop if no data is received

                    deals = decode_data(data)

                    logging.info(f"Got a socket message {deals}")

                    for deal in deals:
                        logging.info(f"Processing message {deal}")

                        if deal.get("request_buy"):
                            self.__request_trade(deal, "buy")

                        if deal.get("request_sell"):
                            self.__request_trade(deal, "sell")

            except KeyboardInterrupt:
                break

        # Close the server socket outside of the loop
        self.server_socket.close()

    def run(self) -> None:
        socket_thread = Thread(target=self.listen, daemon=True)
        socket_thread.start()

        if SKIP_INVENTORY_FETCH:
            self.pure = INVENTORY_PURE_STOCK
            self.deals.pure_stock = self.pure
        else:
            self.__set_inventory_pure()

        if SKIP_PRICES_TF_FETCH:
            self.prices = read_json_file(PRICES_TF_FILE)
        else:
            self.__get_prices_tf_prices()

        logging.info("got prices from prices.tf")

        # get and set this once
        if SKIP_STN_SCHEMA_FETCH:
            self.stn_schema = read_json_file(STN_SCHEMA_PATH)
            self.stn.schema = self.stn_schema
        else:
            self.stn_schema = self.stn.get_sku_schema()

        logging.info(f"stn schema got {len(self.stn_schema)} items")

        self.sku_list = list(self.stn_schema.keys())
        random.shuffle(self.sku_list)

        self.deals.add_prices(self.prices, "pricestf")

        while True:
            if not self.connection:
                logging.warning("No client connected to socket yet...")

            now = time.time()

            if now >= self.last_time + TRADING_SITES_INTERVAL:
                self.__get_site_prices()
                self.__check_non_stn_items()  # items which does not exist in stn schema
                self.last_time = now

            # self.deals.clear_prices()
            self.__check_stn_items()  # items which do exist in stn schema

            time.sleep(0.1)
