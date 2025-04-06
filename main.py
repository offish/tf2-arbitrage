import asyncio
import logging
import sys

from dotenv import load_dotenv

from tf2_arbitrage.arbitrage import Arbitrage
from tf2_arbitrage.options import Options
from tf2_arbitrage.utils import (
    ArbitrageFileFormatter,
    ArbitrageFormatter,
    create_and_get_log_file,
    get_config,
)

load_dotenv()


formatter = ArbitrageFormatter()
stream_handler = logging.StreamHandler(sys.stdout)

log_file = create_and_get_log_file()
file_handler = logging.FileHandler(log_file, encoding="utf-8")

logging.getLogger("pymongo").setLevel(logging.INFO)
logging.getLogger("websockets").setLevel(logging.INFO)
logging.basicConfig(level=logging.DEBUG, handlers=[stream_handler, file_handler])

# only want to see info and above in console
stream_handler.setLevel(logging.INFO)
# stream_handler.setLevel(logging.DEBUG)
stream_handler.setFormatter(ArbitrageFormatter())

# want to have everything in the log file
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(ArbitrageFileFormatter())


config = get_config()
options = Options(**config)
arbitrage = Arbitrage(options)

if __name__ == "__main__":
    asyncio.run(arbitrage.start())
