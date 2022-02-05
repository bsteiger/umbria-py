from dataclasses import dataclass
from enum import Enum
from typing import List
import requests
from argparse import ArgumentParser


class Networks(Enum):
    MATIC = "matic"
    ETH = "ethereum"
    AVAX = "avax"
    BSC = "binancesmartchain"

    def __str__(self):
        return self.value

    def __repr__(self):
        return self.value

    def __eq__(self, __o: object) -> bool:
        return self.value == __o


ADDRESSES = {}
ADDRESSES[Networks.MATIC.value] = {
    "0x1bfd67037b42cf73acf2047067bd4f2c47d9bfd6": "WBTC",
    "0x2791bca1f2de4661ed88a30c99a7a9449aa84174": "USDC",
    "0x2e4b0Fb46a46C90CB410FE676f24E466753B469f": "UMBR",
    "0x385eeac5cb85a38a9a07a70c73e0a3271cfb54a7": "GHST",
    "0x7ceb23fd6bc0add59e62ac25578270cff1b9f619": "ETH",
    "0xc2132d05d31c914a87c6611c10748aeb04b58e8f": "USDT",
    "0xMATIC": "MATIC",
}


@dataclass
class UmbriaPool:
    coin: str = None
    apy: float = None  # average for past 24hrs
    tvl: float = None
    network: str = None
    liquidity_fee: float = 0.002

    def is_umbr(self) -> bool:
        return self.coin.lower() == "umbr"

    def calculate_daily_volume(self) -> float:
        apr = apy_to_apr(self.apy, n=365)
        fees_per_year = apr * self.tvl
        bridge_fee = self.liquidity_fee
        return 0 if self.is_umbr() else fees_per_year / bridge_fee / 365


class UmbriaApi:
    base_url = "https://bridgeapi.umbria.network"
    apys: dict = {}
    tvls: dict = {}

    def update_apys_on(self, network: Networks):
        self.apys[network.value] = self.get_apys_on(network)

    def update_tvls_on(self, network: Networks):
        self.tvls[network.value] = self.get_tvls_on(network)

    def get_umbria_apy(self, network: Networks) -> float:
        if not self.apys.get(network.value):
            self.update_apys_on(network)

        if not self.tvls.get(network.value):
            self.update_tvls_on(network)

        apys = self.apys[network.value]
        tvls = self.tvls[network.value]

        coins = set([*apys.keys(), *tvls.keys()])

        pools = [
            UmbriaPool(coin=coin,
                       apy=apys.get(coin),
                       tvl=tvls.get(coin),
                       network=network) for coin in coins
        ]
        umbria = [p for p in pools if p.coin == "UMBR"][0]

        daily_umbr_rewards = sum([
            0.003 * p.calculate_daily_volume() for p in pools
            if p.coin != "UMBR"
        ])

        apr = daily_umbr_rewards * 365 / umbria.tvl
        return apr_to_apy(apr)

    def get_apys_on(self, network: Networks) -> dict:
        endpoint = f"{self.base_url}/api/pool/getApyAll/?network={network}"
        resp = requests.get(endpoint)
        apys = resp.json()
        return {
            ADDRESSES.get(network.value).get(k, k): float(v)
            for k, v in apys.items()
        }

    def get_tvls_on(self, network: Networks) -> dict:
        endpoint = f"{self.base_url}/api/pool/getTvlAll/?network={network}"
        resp = requests.get(endpoint)

        tvls = resp.json()
        return {k: float(v) for k, v in tvls.get("assets").items()}

    def get_all_staked(self, address) -> dict:
        """Get all staked token amounts across all chains
        
        Returns:
            dict {token_symbol: balance}
        """

        staked_bal = {}
        for network in Networks:
            tokens = ADDRESSES.get(network.value)
            if tokens is None:
                continue
            for token in tokens:
                token_name = ADDRESSES.get(network.value).get(token)
                endpoint = f"{self.base_url}/api/pool/getStaked/?tokenAddress={token}&userAddress={address}&network={network.value}"
                resp = requests.get(endpoint).json()
                staked_bal[token_name] = staked_bal.get(
                    token_name, 0) + float(resp['amount']) / 10e17
        return staked_bal


def apy_to_apr(apy, n: float = 365) -> float:
    """Convert compounded apy to annual rate

    Args:
        apy (float): Annual Percentage Yield
        n (float): number of compounds per year
    Returns:
        float: simple interest apr

    """
    apyinput = (apy) + 1

    inverseperiods = 1 / n
    apr = apyinput**inverseperiods
    apr = (apr - 1) * n
    return apr


def apr_to_apy(apr, n: float = 365) -> float:
    """Convert simple annual rate to compound yield

    Args:
        apr (float): simple interest APR
        n (float): number of compounds per year
    Returns:
        float: compounded apy

    """
    apy = (1 + (apr / n))**n - 1
    return apy


def main():
    api = UmbriaApi()
    network = Networks.MATIC
    umbr_apy = api.get_umbria_apy(network)

    print("-------------------------------------------")
    print(f"Umbr APY on {network}: {umbr_apy*100:.2f}%")
    print("-------------------------------------------\n")


if __name__ == "__main__":
    main()
