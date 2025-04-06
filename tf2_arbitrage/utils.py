import json
import logging
from datetime import datetime
from pathlib import Path

from stntrading import STN
from tf2_utils import to_refined

from .config import BLACKLISTED_INCLUDE, STN_API_KEY
from .exceptions import NoConfigFound, NoFileFound

key_price_reference = None


def create_and_get_log_file() -> Path:
    current_date = datetime.today().strftime("%Y-%m-%d")
    file_path = Path(__file__).parent.parent / f"logs/arbitrage-{current_date}.log"

    if not file_path.exists():
        file_path.touch()

    return file_path


def dump_to_json_file(data: dict | list, path: Path | str) -> None:
    with open(path, "w") as file:
        json.dump(data, file, indent=4)


def read_json_file(path: Path | str) -> dict | list:
    data = None

    with open(path, "r") as file:
        data = json.loads(file.read())

    return data


def get_config() -> dict:
    path = Path(__file__).parent / "config.json"

    if not path.exists():
        raise NoConfigFound("No config.json file in the tf2_arbitrage directory!")

    return read_json_file(path)


def get_files_path() -> Path:
    return Path(__file__).parent.parent / "files"


def get_file_path(name: str) -> Path:
    path = get_files_path() / f"{name}.json"

    if not path.exists():
        raise NoFileFound(f"No {name} file in the tf2_arbitrage/files directory!")

    return path


def get_file_content(name: str) -> dict:
    path = get_file_path(name)
    return read_json_file(path)


def dump_to_file(name: str, data: dict | list) -> None:
    path = get_file_path(name)
    dump_to_json_file(data, path)


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


class ArbitrageFormatter(logging.Formatter):
    _format = "tf2-arbitrage | %(asctime)s - [%(levelname)s]: %(message)s"

    FORMATS = {
        logging.DEBUG: _format,
        logging.INFO: _format,
        logging.WARNING: _format,
        logging.ERROR: _format + "(%(filename)s:%(lineno)d)",
        logging.CRITICAL: _format + "(%(filename)s:%(lineno)d)",
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt, datefmt="%H:%M:%S")
        return formatter.format(record)


class ArbitrageFileFormatter(logging.Formatter):
    _format = "%(filename)s %(asctime)s - [%(levelname)s]: %(message)s"

    FORMATS = {
        logging.DEBUG: _format,
        logging.INFO: _format,
        logging.WARNING: _format,
        logging.ERROR: _format + "(%(filename)s:%(lineno)d)",
        logging.CRITICAL: _format + "(%(filename)s:%(lineno)d)",
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt, datefmt="%d/%m/%Y %H:%M:%S")
        return formatter.format(record)
