from os import getenv

from pymongo import MongoClient


class Database:
    def __init__(self) -> None:
        host = getenv("DATABASE_HOST", "localhost")
        port = int(getenv("DATABASE_PORT", 27017))

        client = MongoClient(host=host, port=port)
        db = client["tf2-arbitrage"]

        self.cookies = db["cookies"]
        self.prices = db["prices"]
        self.trade_urls = db["trade_urls"]

    def get_prices_tf_prices(self) -> dict:
        return self.prices_tf_prices.find_one({})

    def get_stn_schema(self) -> dict:
        return self.stn_schema.find_one({})

    def add_trade_url(self, steam_id: str, account_id: str, token: str) -> None:
        self.trade_urls.replace_one(
            {"steam_id": steam_id},
            {"steam_id": steam_id, "account_id": account_id, "token": token},
            upsert=True,
        )

    def get_trade_url(self, steam_id: str) -> str | None:
        document = self.trade_urls.find_one({"steam_id": steam_id})

        if not document:
            return

        account_id = document["account_id"]
        token = document["token"]
        trade_url = "https://steamcommunity.com/tradeoffer/new/?partner={}&token={}"

        return trade_url.format(account_id, token)

    def save_cookies(self, data: dict) -> None:
        self.cookies.replace_one({"name": data["name"]}, data, True)

    def get_cookies(self, name: str) -> list[dict]:
        document = self.cookies.find_one({"name": name})

        if not document:
            return []

        return document["cookies"]
