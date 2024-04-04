# tf2-arbitrage
[![License](https://img.shields.io/github/license/offish/tf2-arbitrage.svg)](https://github.com/offish/tf2-arbitrage/blob/master/LICENSE)
[![Stars](https://img.shields.io/github/stars/offish/tf2-arbitrage.svg)](https://github.com/offish/tf2-arbitrage/stargazers)
[![Issues](https://img.shields.io/github/issues/offish/tf2-arbitrage.svg)](https://github.com/offish/tf2-arbitrage/issues)
[![Size](https://img.shields.io/github/repo-size/offish/tf2-arbitrage.svg)](https://github.com/offish/tf2-arbitrage)
[![Discord](https://img.shields.io/discord/467040686982692865?color=7289da&label=Discord&logo=discord)](https://discord.gg/t8nHSvA)
[![Code style](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

Bot for arbitrating TF2 items on different sites for profit.

This bot will find deals, act on them and notify [tf2-express](https://github.com/offish/tf2-express) to accept.

## Donate
- BTC: `bc1qntlxs7v76j0zpgkwm62f6z0spsvyezhcmsp0z2`
- [Steam Trade Offer](https://steamcommunity.com/tradeoffer/new/?partner=293059984&token=0-l_idZR)

You can reach me at [Steam](https://steamcommunity.com/id/confern), 
my [Discord server](https://discord.gg/t8nHSvA) 
or [Discord profile](https://discord.com/users/252183247843229696>`)

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
- Repeat step 6-16 (fetching Prices.tf is uneccessary when we are connected to their websocket)

## Supported sites
- Backpack.TF
- STNTrading.eu
- Quicksell.store
- Sfuminator.tf (partly)

Scrap.TF is not supported, due to their ToS.

## What do I need?
- A `tf2-express` bot
- Firefox with a custom profile where you are logged into the sites listed above
- `geckodriver` installed and added to PATH
- Premium STN API key 

## Don't have a Premium STN API key?
STN are not accepting new ones, but the endpoints will be publicly available soon.

![image](https://github.com/offish/tf2-utils/assets/30203217/59fe4448-6dc5-4cb5-a41a-a67406cfd54d)

It's also possible to use the [stntrading](./tf2_arbitrage/sites/stntrading.py) version, but they have better detection for automated requests than Quicksell and Sfuminator.
