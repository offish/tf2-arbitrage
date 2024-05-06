from .config import STN_API_KEY, BLACKLISTED_INCLUDE

import logging
import json
import time

from stntrading import STN
from tf2_utils import to_refined


key_price_reference = None


def get_stn_key_price() -> float:
    global key_price_reference

    if key_price_reference is not None:
        return key_price_reference

    logging.info("getting key price from stn")
    stn = STN(STN_API_KEY)
    response = stn.get_key_prices()

    if not response["success"]:
        raise ValueError("could not get key price from stn")

    buy_price = response["result"]["pricing"]["buyPrice"]
    key_price_reference = to_refined(buy_price)
    return key_price_reference


def can_afford_price(price: dict, stock: dict) -> bool:
    key_price = get_stn_key_price()

    # we have more keys
    if stock["keys"] > price["keys"]:
        return True

    # same amount of keys, but equal or more in metal
    if stock["keys"] == price["keys"] and stock["metal"] >= price["metal"]:
        return True

    if (
        stock["keys"] * key_price + stock["metal"]
        >= price["keys"] * key_price + price["metal"]
    ):
        return True

    return False


def is_blacklisted(item_name: str) -> bool:
    """if item name includes a blacklisted word"""
    for tag in BLACKLISTED_INCLUDE:
        if tag in item_name:
            return True

    return False


def worth_less_than(price: dict, metal: float) -> bool:
    # we have more keys
    key_price = get_stn_key_price()

    return price["keys"] * key_price + price["metal"] < metal


def their_is_less_or_equal(their: dict, our: dict) -> bool:
    key_price = get_stn_key_price()

    return (
        their["keys"] * key_price + their["metal"]
        <= our["keys"] * key_price + our["metal"]
    )


def their_is_more_or_equal(their: dict, our: dict) -> bool:
    key_price = get_stn_key_price()

    return (
        their["keys"] * key_price + their["metal"]
        >= our["keys"] * key_price + our["metal"]
    )


def has_invalid_defindex(sku: str) -> bool:
    return sku.split(";")[0] == "-1"


def get_file_name(identifier: str) -> str:
    return f"./prod/{int(time.time())}_{identifier}.json"


def dump_to_json_file(data: dict | list, path: str) -> None:
    file = open(path, "w")
    json.dump(data, file, indent=4)
    file.close()


def read_json_file(path: str) -> dict | list:
    data = None

    with open(path, "r") as file:
        data = json.loads(file.read())

    return data


def encode_data(data: dict) -> bytes:
    return (json.dumps(data) + "NEW_DATA").encode()


def decode_data(data: bytes) -> list[dict]:
    return [json.loads(doc) for doc in data.decode().split("NEW_DATA") if doc]


def remove_unnecessary_data(data: dict, intent: str) -> dict:
    compressed = data.copy()
    keys_to_delete = []

    for key in data.get(intent, {}):
        if key not in ["trade_url", "steamid"]:
            keys_to_delete.append(key)

    for key in keys_to_delete:
        del compressed[intent][key]

    return compressed


def compress_message(data: dict) -> dict:
    compressed = data.copy()

    compressed = remove_unnecessary_data(compressed, "buy_data")
    compressed = remove_unnecessary_data(compressed, "sell_data")

    return compressed
