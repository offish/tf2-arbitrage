import logging

from tf2_utils import get_metal, is_metal, map_inventory, to_refined


def get_pure_stock(inventory: dict) -> dict:
    logging.debug("Getting pure in inventory...")

    stock = {"keys": 0}
    scrap = 0

    for item in map_inventory(inventory, add_skus=True, skip_untradable=True):
        sku = item["sku"]

        if sku == "5021;6":
            stock["keys"] += 1

        if is_metal(sku):
            scrap = get_metal(sku)

    stock["metal"] = to_refined(scrap)

    logging.debug(f"Got pure in inventory {stock}")
    return stock


def is_overstocked(stock: dict) -> bool:
    return stock["level"] >= stock["limit"]


def is_in_stock(stock: dict) -> bool:
    return stock["level"] > 0


def has_valid_stock(deal_data: dict, stock: dict) -> bool:
    # make sure they have item in stock
    if deal_data["buy_site"] == "stn":
        if not is_in_stock(stock):
            return False

    # make sure not overstocked
    if deal_data["sell_site"] == "stn":
        if is_overstocked(stock):
            return False

    return True
