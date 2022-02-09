from umbria import UmbriaApi, Networks
from coingecko import CoinGeckoApi
from argparse import ArgumentParser


def parse_args():
    parser = ArgumentParser()
    parser.add_argument(
        "-w", dest="wallet_address", help="get balances for a given wallet address"
    )
    args = parser.parse_args()
    return args


def print_umbria_apr(umbria: UmbriaApi, coingecko: CoinGeckoApi, network: Networks):
    (umbr_apr, itemized_aprs) = umbria.get_umbria_apr(network)
    print("\n-------------------------------------------")
    print(f"Umbr APR on {network} network: {umbr_apr*100:.2f}%")
    print("-------------------------------------------\n")
    print("APR Breakdown------------------------------")
    for (apr, coin) in itemized_aprs:
        print(f"{coin}:\t{apr*100:.2f}%")

    print("\n-------------------------------------------")

    for symbol in ["UMBR", "WETH", "MATIC"]:
        print(
            f"Current {symbol} price: ${coingecko.get_token_price_by_symbol(symbol):.2f}"
        )
    print("-------------------------------------------\n")


def print_balances_for_wallet(wallet_address, umbria, coingecko, network):
    tokens = set(umbria.apys[network.value].keys())
    token_prices = {
        token: coingecko.get_token_price_by_symbol(token) for token in tokens
    }
    staked_bal = umbria.get_all_staked(wallet_address)
    staked_bal_usd = {
        token: bal * token_prices[token] for token, bal in staked_bal.items()
    }
    print("\nCurrent Token Balances on Umbria:")
    for token, bal in staked_bal_usd.items():
        print(f"{token}:\t${bal:.2f}")
    print(f"-------------------")
    print(f"Total:\t${sum([v for _,v in staked_bal_usd.items()]):.2f}")
    print()


def main(wallet_address: str = None):
    umbria = UmbriaApi()
    coingecko = CoinGeckoApi()
    network = Networks.MATIC
    print_umbria_apr(umbria, coingecko, network)
    if wallet_address:
        print_balances_for_wallet(wallet_address, umbria, coingecko, network)


if __name__ == "__main__":
    args = parse_args()
    main(wallet_address=args.wallet_address)
