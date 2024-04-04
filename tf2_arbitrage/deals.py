from .config import MINIMUM_PROFIT_REQUIRED
from .utils import can_afford_price, has_invalid_defindex, get_stn_key_price

import logging

from tf2_utils import to_refined, to_scrap


class Deals:
    def __init__(self) -> None:
        self.global_prices = {}
        self.pure_stock = {}
        self.sites = []

    def get_prices(self) -> dict:
        return self.global_prices

    def is_in_prices(self, sku: str) -> bool:
        return sku in self.global_prices

    def clear_prices(self) -> None:
        self.global_prices = {}
        logging.info("cleared prices")

    def update_price(self, sku: str, prices: dict) -> None:
        """only pricestf prices"""
        self.global_prices[sku]["pricestf"] = prices

    def add_prices(self, prices: dict, site: str) -> None:
        # TODO: what if an item has been sold on a site
        # its no longer available but still in the priceslist
        # either delete before adding or do something else

        logging.info(f"adding prices for {site}")

        if site not in self.sites:
            self.sites.append(site)

        for sku in prices:
            if has_invalid_defindex(sku):
                continue

            if sku not in self.global_prices:
                self.global_prices[sku] = {}

            price = prices[sku]

            if "buy" not in price:
                logging.warning(f"no buy price for {sku} on {site}")
                continue

            # pricestf does not have name
            if "name" not in self.global_prices and "name" in price:
                self.global_prices[sku]["name"] = price["name"]

            self.global_prices[sku][site] = {
                "buy": price["buy"],
            }

            # not all sites give a sell price, like quicksell, sfuminator
            if "sell" in price:
                self.global_prices[sku][site]["sell"] = price["sell"]

    def __get_deal_data(self, sku: str) -> dict:
        """checks wheter or not if its a deal."""
        sell_prices = []
        buy_prices = []

        item = self.global_prices[sku]

        for site in item:
            if site == "name":
                continue

            key_price = get_stn_key_price()
            key_scrap_price = to_scrap(key_price)

            if site != "pricestf":
                item_sell = item[site].get("buy")
                item_buy = item[site].get("sell")
            else:
                item_sell = item[site].get("sell")
                item_buy = item[site].get("buy")

            if item_buy:
                buy_price = item_buy["keys"] * key_scrap_price + to_scrap(
                    item_buy["metal"]
                )
                buy_prices.append((buy_price, site, item_buy))

            if item_sell:
                sell_price = item_sell["keys"] * key_scrap_price + to_scrap(
                    item_sell["metal"]
                )
                sell_prices.append((sell_price, site, item_sell))

        # either one has 0 length
        if not (sell_prices and buy_prices):
            return {"is_deal": False}

        lowest_sell = min(sell_prices)
        highest_buy = max(buy_prices)

        difference = to_refined(highest_buy[0] - lowest_sell[0])

        # more than a scrap in difference
        is_deal = difference >= MINIMUM_PROFIT_REQUIRED

        buy_site = lowest_sell[1]
        sell_site = highest_buy[1]

        return {
            "is_deal": is_deal,
            "sku": sku,
            "name": item["name"],
            "profit": difference,
            "sites": [buy_site, sell_site],
            "buy_site": buy_site,
            # original price
            "buy_price": lowest_sell[2],
            "sell_site": sell_site,
            # original price
            "sell_price": highest_buy[2],
        }

    def get_deal(self, sku: str) -> dict:
        site_counter = 0

        for site in self.sites:
            if site not in self.global_prices[sku]:
                continue

            site_counter += 1

        if site_counter <= 1:
            return {}

        deal_data = self.__get_deal_data(sku)

        if not deal_data["is_deal"]:
            return {}

        if not can_afford_price(deal_data["buy_price"], self.pure_stock):
            return {}

        return deal_data

    def new_deal(self, sku: str, prices: dict, site: str = "stn") -> dict:
        self.global_prices[sku][site] = prices

        deal_data = self.get_deal(sku)

        del self.global_prices[sku][site]

        return deal_data
