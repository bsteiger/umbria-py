from distutils.log import warn
from urllib import response
import requests
from typing import List
from dataclasses import dataclass


@dataclass
class Coin:
    id: str
    symbol: str
    name: str


def get_id_from_symbol(list: List[Coin], symbol: str):
    return [c.id for c in list if c.symbol.lower() == symbol.lower()]


class CoinGeckoApi:
    base_url = "https://api.coingecko.com/api/v3"
    coins_list: List[Coin] = None

    def __init__(self) -> None:
        self.get_coins_list()

    def ping(self) -> bool:
        endpoint = f"{self.base_url}/ping"
        resp = requests.get(endpoint)
        return True if resp.status_code == 200 else False

    def get_coins_list(self):
        endpoint = f"{self.base_url}/coins/list"
        resp = requests.get(endpoint)
        self.coins_list = [Coin(**c) for c in resp.json()]

    def get_token_price_by_id(self, id: str, currency="usd") -> float:
        endpoint = f"{self.base_url}/simple/price?ids={id}&vs_currencies=usd"
        resp = requests.get(endpoint)
        return resp.json()[id][currency]

    def get_token_price_by_symbol(self, symbol: str, currency="usd") -> float:
        ids = get_id_from_symbol(self.coins_list, symbol)
        if len(ids) > 1:
            warn(f"Multiple ids found for {symbol}: {ids} using {ids[0]}")
        return self.get_token_price_by_id(ids[0])


if __name__ == "__main__":
    cg = CoinGeckoApi()
    print("$", cg.get_token_price_by_symbol("UMBR"))
