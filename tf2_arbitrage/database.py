from .config import DB_HOST, DB_PORT

from pymongo import MongoClient


class Database:
    def __init__(self, host: str = DB_HOST, port: int = DB_PORT) -> None:
        self._client = MongoClient(host=host, port=port)
        self.db = self._client["odysseus"]

        self.cookies = self.db["cookies"]
        self.prices = self.db["prices"]
        self.trade_urls = self.db["trade_urls"]

    def add_trade_url(self, steam_id: str, account_id: str, token: str) -> None:
        self.trade_urls.replace_one(
            {"steam_id": steam_id},
            {"steam_id": steam_id, "account_id": account_id, "token": token},
            True,
        )

    def get_trade_url(self, steam_id: str) -> str:
        document = self.trade_urls.find_one({"steam_id": steam_id})

        if not document:
            return ""

        trade_url = "https://steamcommunity.com/tradeoffer/new/?partner={}&token={}"
        return trade_url.format(document["account_id"], document["token"])

    def save_cookies(self, data: dict) -> None:
        self.cookies.replace_one({"name": data["name"]}, data, True)

    def get_cookies(self, name: str) -> list[dict]:
        document = self.cookies.find_one({"name": name})

        if not document:
            return []

        return document["cookies"]
