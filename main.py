from tf2_arbitrage.arbitrage import Arbitrage
from offish import Formatter, FileFormatter

from threading import Thread
import logging
import sys

from tf2_utils import PricesTFSocket


stream_handler = logging.StreamHandler(sys.stdout)
file_handler = logging.FileHandler("./logs.log", encoding="utf-8")

# selenium spams the logs
logger = logging.getLogger("selenium.webdriver.remote.remote_connection")
logger.setLevel(logging.INFO)

logging.basicConfig(
    level=logging.DEBUG,
    handlers=[
        stream_handler,
        file_handler,
    ],
)

formatter = Formatter()
formatter.application = "tf2-arbitrage"

stream_handler.setLevel(logging.INFO)
stream_handler.setFormatter(formatter)

file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(FileFormatter())

arbitrage = Arbitrage()


def on_socket_data(data: dict) -> None:
    arbitrage.on_socket_data(data)


if __name__ == "__main__":
    prices_socket = PricesTFSocket(on_socket_data)
    prices_socket_thread = Thread(target=prices_socket.listen, daemon=True)
    prices_socket_thread.start()
    arbitrage.run()
    prices_socket_thread.join()
