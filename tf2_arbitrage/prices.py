from .options import Options
from .site import SiteEnum


class Prices:
    def __init__(self, options: Options):
        self.options = options
        self.prices = {}
        # {
        #     "stn.tf": {
        #         "263;6": {
        #            "buy": {
        #                "keys": 0,
        #                "metal": 1.44,
        #            },
        #            "sell": {
        #                "keys": 0,
        #                "metal": 1.55,
        #            }
        #         },
        #         ...
        #     },
        #     "prices.tf": {
        #     ...

    def set_prices(self, prices: dict, site: SiteEnum) -> None:
        self.prices[site.value] = prices

    def get_prices(self, site: SiteEnum) -> dict:
        return self.prices[site.value]

    def get_price(self, sku: str, site: SiteEnum) -> dict | None:
        return self.get_prices(site).get(sku)
