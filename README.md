# tf2-arbitrage
[![License](https://img.shields.io/github/license/offish/tf2-arbitrage.svg)](https://github.com/offish/tf2-arbitrage/blob/master/LICENSE)
[![Stars](https://img.shields.io/github/stars/offish/tf2-arbitrage.svg)](https://github.com/offish/tf2-arbitrage/stargazers)
[![Issues](https://img.shields.io/github/issues/offish/tf2-arbitrage.svg)](https://github.com/offish/tf2-arbitrage/issues)
[![Size](https://img.shields.io/github/repo-size/offish/tf2-arbitrage.svg)](https://github.com/offish/tf2-arbitrage)
[![Discord](https://img.shields.io/discord/467040686982692865?color=7289da&label=Discord&logo=discord)](https://discord.gg/t8nHSvA)
[![Code style](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

Bot for arbitraging TF2 items on different sites for profit.

This bot will find deals, request trades and notify [tf2-express](https://github.com/offish/tf2-express) to accept.

## Donate
- BTC: `bc1qntlxs7v76j0zpgkwm62f6z0spsvyezhcmsp0z2`
- [Steam Trade Offer](https://steamcommunity.com/tradeoffer/new/?partner=293059984&token=0-l_idZR)

You can reach me at [Steam](https://steamcommunity.com/id/confern), 
my [Discord server](https://discord.gg/t8nHSvA) 
or [Discord profile](https://discord.com/users/252183247843229696>`).

## How does it work?
- Using a Firefox profile, login to the sites listed below
- Will check MongoDB for saved cookies
- If outdated, get new cookies using `Selenium`
- Save cookies, such that `requests` can imitate a legitimate internal API request 
- Fetches prices from Prices.tf as a comparison basis
- Fetches prices from STN, taking stock into consideration
- Fetches prices from Quicksell.store
- Fetches prices from Sfuminator
- Compares prices between sites, and finds deals
- If a Prices.tf price is included in a deal, check Backpack.TF for buyers/sellers with a matching price
- If buyer/seller is from Backpack.TF, get their Trade URL
- Save up to 3 pages of classifieds for Trade URLs, so they can be used later (can skip fetching)
- Send deals using a TCP socket so `tf2-express` can act on the trades
- When `tf2-express` has accepted a "buy deal" trade offer, send the "sell deal" request to one of the trading sites (different for Backpack.TF)
- Repeat step 6-16 (fetching Prices.tf is uneccessary when we are connected to the websocket)

## Supported sites
- Backpack.TF
- STNTrading.eu
- Quicksell.store
- Sfuminator.tf

Scrap.TF is not supported, due to their ToS.

## Installation
- Clone the repo and install the packages `pip install -r requirements.txt`
- The bot uses MongoDB, so `pymongo` needs to work
- Install `geckodriver`

## Setup
- Have a `tf2-express` bot setup and ready to go
- If `geckodriver` is not added to PATH, this needs to be specified in `GECKODRIVER_EXECUTABLE_PATH` in the [config](/tf2_arbitrage/config.py). If it is in PATH, do not change this value
- Create a new Firefox profile and login to all the sites listed above (STN is not neccessary). Copy the `Root Directory` of this Firefox profile. This is your `FIREFOX_PROFILE_PATH` in the [config](/tf2_arbitrage/config.py)
- Register a STN API key at https://stntrading.eu/dev/apikey
- Make sure you have credits for your API calls. This can be increased at https://stntrading.eu/dev/credits

## Configuration
- Specify `STEAM_ID` in the [config](/tf2_arbitrage/config.py), this has to match the SteamID64 for the owner of the STN API key 
- Other optional modifications to the [config](/tf2_arbitrage/config.py)

## Running
- Start `tf2-arbitrage` by running `python main.py`
- Start a `tf2-express` instance
