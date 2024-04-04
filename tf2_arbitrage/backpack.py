from .sites.sites import Site
from .database import Database
from .config import BACKPACK_TF_PAGES, BLACKLISTED_LISTING_DETAIL, MAX_LAST_BUMP
from .utils import their_is_less_or_equal, their_is_more_or_equal

from urllib.parse import urlencode
import logging
import time

from selenium.webdriver import Firefox
from tf2_utils import sku_to_defindex, account_id_to_steam_id, get_token_from_trade_url
from tf2_data import DEFINDEX_NAMES, DEFINDEX_FULL_NAMES
from tf2_sku import to_sku, from_sku
from bs4 import BeautifulSoup


class BackpackTF(Site):
    def __init__(self, r) -> None:
        name = "backpacktf"
        url = "https://backpack.tf"
        api_url = "https://backpack.tf"
        headers = {
            "Host": "backpack.tf",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",  # noqa
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",  # noqa
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate, br",
            "Referer": "https://backpack.tf/",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "same-origin",
            "Sec-Fetch-User": "?1",
            "TE": "trailers",
        }

        super().__init__(r, name, url, api_url, headers)
        self.threshold = 30 * 60  # 30 minutes
        self.db = Database()
        self.driver = None

    @staticmethod
    def __is_supported_bot(client: str) -> bool:
        for bot in ["tf2autobot", "gladiator.tf", "scrapyardbot"]:
            if bot in client:
                return True

        return False

    @staticmethod
    def __is_recently_bumped(listing: dict) -> bool:
        return time.time() < listing["bump"] + MAX_LAST_BUMP

    def __is_bot_listning(self, listing: dict) -> bool:
        if "userAgent" not in listing:
            return False

        client = listing["userAgent"]["client"].lower()

        if not self.__is_supported_bot(client):
            return False

        return True

    def __has_blacklisted_details(self, listing: dict) -> bool:
        # turn special characters into normal ones?
        details = listing.get("details", "").lower()

        for tag in BLACKLISTED_LISTING_DETAIL:
            if tag in details:
                return True

        return False

    def __has_matching_sku(self, listing: dict, sku: str) -> bool:
        item = listing["item"]
        sku_properties = {
            "defindex": item["defindex"],
            "quality": item["quality"],
            "craftable": not item.get("flag_cannot_craft", False),
        }

        return sku == to_sku(sku_properties)

    def __has_good_price(
        self, listing: dict, prices: dict, sku: str, intent: str
    ) -> bool:
        price = listing["currencies"]

        if "keys" not in price:
            price["keys"] = 0

        if "metal" not in price:
            price["metal"] = 0.0

        # if they are selling, we want less or equal
        if intent == "sell":
            return their_is_less_or_equal(price, prices[sku]["sell"])

        # they are buying, so more or equal to buy is best
        return their_is_more_or_equal(price, prices[sku]["buy"])

    def __is_valid_listing(
        self, listing: dict, intent: str, sku: str, prices: dict
    ) -> bool:
        # has to match intent
        if intent != listing["intent"]:
            return False

        # only trade offers, no "add me"
        if listing["offers"] != 1:
            return False

        if not self.__is_bot_listning(listing):
            return False

        if not self.__is_recently_bumped(listing):
            return False

        if self.__has_blacklisted_details(listing):
            return False

        # matches sku
        if not self.__has_matching_sku(listing, sku):
            return False

        # intent is "sell" when we buy
        if not self.__has_good_price(listing, prices, sku, intent):
            return False

        return True

    def __format_html_classifieds(self, html: str) -> None:
        soup = BeautifulSoup(html, "html.parser")

        for listing in soup.find_all("div", class_="item"):
            account_id = listing.get("data-listing_account_id")
            trade_url = listing.get("data-listing_offers_url")

            if not account_id or not trade_url:
                continue

            steam_id = account_id_to_steam_id(account_id)
            token = get_token_from_trade_url(trade_url)

            # save all trade urls in database for use later
            self.db.add_trade_url(steam_id, account_id, token)

    def __get_trade_url(self, sku: str, steam_id: str) -> str:
        if self.driver is None:
            self.driver = Firefox(options=self.options)

        logging.info("getting trade urls")

        item = from_sku(sku)
        # here item name is Team Captain and not The Team Captain
        item_name = DEFINDEX_NAMES[str(item["defindex"])]

        params = {
            "item": item_name,
            "quality": item["quality"],
            "tradable": 1,
            "craftable": 1 if item["craftable"] else -1,
            "australium": -1,
            "killstreak_tier": 0,
        }

        for page in range(1, BACKPACK_TF_PAGES + 1):
            params["page"] = page
            self.driver.get(f"https://backpack.tf/classifieds?{urlencode(params)}")

            time.sleep(3)

            self.__format_html_classifieds(self.driver.page_source)

        return self.db.get_trade_url(steam_id)

    def __get_listings(self, sku: str) -> dict:
        defindex = sku_to_defindex(sku)
        item_name = DEFINDEX_FULL_NAMES[str(defindex)]

        params = {"sku": item_name, "appid": 440}
        response = self.get_request("/api/classifieds/listings/snapshot", params)

        listings_amount = len(response.get("listings", []))

        # ratelimited, wait 1 second
        if "limit exceeded" in response.get("message", ""):
            logging.warning("bptf rate limited")
            time.sleep(1.1)
            return self.__get_listings(sku)

        if listings_amount == 0:
            logging.warning("did not find any listings")
            return {}

        return response

    def __get_valid_listing(self, sku: str, intent: str, prices: dict) -> dict:
        logging.info("getting listings")
        listings = self.__get_listings(sku)
        valid_listing = {}

        if not listings:
            return {}

        for listing in listings["listings"]:
            if not self.__is_valid_listing(listing, intent, sku, prices):
                continue

            logging.info("found a valid listing")

            # TODO: this only matches the first and stops,
            # maybe do all which have matching price?
            # valid listing, break
            valid_listing = listing
            break

        if not valid_listing:
            return {}

        steam_id = valid_listing["steamid"]

        trade_url = self.db.get_trade_url(steam_id)

        if not trade_url:
            trade_url = self.__get_trade_url(sku, steam_id)

        # TODO: make this nicer, has to be done twice
        if not trade_url:
            logging.info("could not find trade url for user")
            return {}

        valid_listing["trade_url"] = trade_url
        return valid_listing

    def get_lowest_sell(self, sku: str, prices: dict) -> dict:
        return self.__get_valid_listing(sku, "sell", prices)

    def get_highest_buy(self, sku: str, prices: dict) -> dict:
        return self.__get_valid_listing(sku, "buy", prices)
