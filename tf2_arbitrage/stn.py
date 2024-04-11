from .utils import is_blacklisted

from stntrading import STN
from tf2_utils import SchemaItemsUtils

import logging


class STNTrading(STN):
    def __init__(self, api_key: str) -> None:
        self.schema_utils = SchemaItemsUtils()
        self.schema = {}
        super().__init__(api_key)

    @staticmethod
    def __filter_items(item_names: list[str]) -> list[str]:
        items = []

        for item_name in item_names:
            if is_blacklisted(item_name):
                continue

            items += [item_name]

        return items

    def __item_name_to_sku(self, item_name: str) -> str:
        return self.schema_utils.name_to_sku(item_name)

    def __sku_to_item_name(self, sku: str) -> str:
        return self.schema.get(sku, "")

    def get_sku_schema(self) -> dict:
        schema = self.get_schema()
        items = self.__filter_items(schema["result"]["schema"])

        for item_name in items:
            sku = self.__item_name_to_sku(item_name)

            # map sku to item name so we can go backwards in sku to name
            self.schema[sku] = item_name

        return self.schema

    def get_prices(self, sku: str) -> dict:
        item_name = self.__sku_to_item_name(sku)

        try:
            return self.get_item_details(item_name)
        except Exception as e:
            logging.error(f"Failed to get prices for {item_name} on stntrading: {e}")
            return {}
