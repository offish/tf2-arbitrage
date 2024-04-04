from tf2_arbitrage.utils import compress_message

from unittest import TestCase


class TestSocket(TestCase):
    def test_single_side(self):
        data = {
            "is_deal": True,
            "sku": "767;6",
            "name": "Atomic Accolade",
            "profit": 0.11,
            "sites": ["pricestf", "stn"],
            "buy_site": "pricestf",
            "buy_price": {"keys": 0, "metal": 1.66},
            "sell_site": "stn",
            "sell_price": {"keys": 0, "metal": 1.77},
            "buy_data": {
                "steamid": "76561199127926612",
                "offers": 1,
                "buyout": 1,
                "details": "Selling Atomic Accolade for 1.55 ref - add me and type !buy Atomic Accolade .",  # noqa
                "intent": "sell",
                "timestamp": 1707370149,
                "price": 1.55,
                "item": {
                    "id": 14142018319,
                    "original_id": 11650327339,
                    "defindex": 767,
                    "level": 10,
                    "quality": 6,
                    "inventory": 2147483987,
                    "quantity": 1,
                    "origin": 4,
                    "attributes": [
                        {
                            "defindex": 228,
                            "value": 247008521,
                            "float_value": 4.5618573481965566e-30,
                            "account_info": {
                                "steamid": 76561198207274249,
                                "personaname": "Subpar Gamer",
                            },
                        },
                        {
                            "defindex": 229,
                            "value": 82900,
                            "float_value": 1.1616764269252734e-40,
                        },
                        {"defindex": 746, "value": 1065353216, "float_value": 1},
                        {"defindex": 292, "value": 1115684864, "float_value": 64},
                        {"defindex": 388, "value": 1115684864, "float_value": 64},
                    ],
                },
                "currencies": {"metal": 1.55, "keys": 0},
                "bump": 1708767662,
                "userAgent": {
                    "lastPulse": 1708767662,
                    "client": "Gladiator.tf - Rent your own bot from 6 keys per month",
                },
                "trade_url": "https://steamcommunity.com/tradeoffer/new/?partner=1167660884&token=BtpgN_cq",  # noqa
            },
            "stock": {"level": 24, "limit": 25},
        }

        self.assertEqual(
            compress_message(data),
            {
                "is_deal": True,
                "sku": "767;6",
                "name": "Atomic Accolade",
                "profit": 0.11,
                "sites": ["pricestf", "stn"],
                "buy_site": "pricestf",
                "buy_price": {"keys": 0, "metal": 1.66},
                "sell_site": "stn",
                "sell_price": {"keys": 0, "metal": 1.77},
                "buy_data": {
                    "steamid": "76561199127926612",
                    "trade_url": "https://steamcommunity.com/tradeoffer/new/?partner=1167660884&token=BtpgN_cq",  # noqa
                },
                "stock": {"level": 24, "limit": 25},
            },
        )

    def test_double_side(self):
        data = {
            "is_deal": True,
            "sku": "767;6",
            "name": "Atomic Accolade",
            "profit": 0.11,
            "sites": ["pricestf", "pricestf"],
            "buy_site": "pricestf",
            "buy_price": {"keys": 0, "metal": 1.66},
            "sell_site": "pricestf",
            "sell_price": {"keys": 0, "metal": 1.77},
            "buy_data": {
                "steamid": "76561199127926612",
                "offers": 1,
                "buyout": 1,
                "details": "Selling Atomic Accolade for 1.55 ref - add me and type !buy Atomic Accolade .",  # noqa
                "intent": "sell",
                "timestamp": 1707370149,
                "price": 1.55,
                "item": {
                    "id": 14142018319,
                    "original_id": 11650327339,
                    "defindex": 767,
                    "level": 10,
                    "quality": 6,
                    "inventory": 2147483987,
                    "quantity": 1,
                    "origin": 4,
                    "attributes": [
                        {
                            "defindex": 228,
                            "value": 247008521,
                            "float_value": 4.5618573481965566e-30,
                            "account_info": {
                                "steamid": 76561198207274249,
                                "personaname": "Subpar Gamer",
                            },
                        },
                        {
                            "defindex": 229,
                            "value": 82900,
                            "float_value": 1.1616764269252734e-40,
                        },
                        {"defindex": 746, "value": 1065353216, "float_value": 1},
                        {"defindex": 292, "value": 1115684864, "float_value": 64},
                        {"defindex": 388, "value": 1115684864, "float_value": 64},
                    ],
                },
                "currencies": {"metal": 1.55, "keys": 0},
                "bump": 1708767662,
                "userAgent": {
                    "lastPulse": 1708767662,
                    "client": "Gladiator.tf - Rent your own bot from 6 keys per month",
                },
                "trade_url": "https://steamcommunity.com/tradeoffer/new/?partner=1167660884&token=BtpgN_cq",  # noqa
            },
            "sell_data": {
                "steamid": "76561199127926613",
                "offers": 1,
                "buyout": 1,
                "details": "Buying Atomic Accolade for 1.77 ref - add me and type !sell Atomic Accolade .",  # noqa
                "intent": "buy",
                "timestamp": 1707370149,
                "price": 1.77,
                "item": {
                    "id": 14142018319,
                    "original_id": 11650327339,
                    "defindex": 767,
                    "level": 10,
                    "quality": 6,
                    "inventory": 2147483987,
                    "quantity": 1,
                    "origin": 4,
                    "attributes": [
                        {
                            "defindex": 228,
                            "value": 247008521,
                            "float_value": 4.5618573481965566e-30,
                            "account_info": {
                                "steamid": 76561198207274249,
                                "personaname": "Subpar Gamer",
                            },
                        },
                        {
                            "defindex": 229,
                            "value": 82900,
                            "float_value": 1.1616764269252734e-40,
                        },
                        {"defindex": 746, "value": 1065353216, "float_value": 1},
                        {"defindex": 292, "value": 1115684864, "float_value": 64},
                        {"defindex": 388, "value": 1115684864, "float_value": 64},
                    ],
                },
                "currencies": {"metal": 1.77, "keys": 0},
                "bump": 1708767662,
                "userAgent": {
                    "lastPulse": 1708767662,
                    "client": "Gladiator.tf - Rent your own bot from 6 keys per month",
                },
                "trade_url": "https://steamcommunity.com/tradeoffer/new/?partner=1167660884&token=BtpgN_cq",  # noqa
            },
            "stock": {"level": 24, "limit": 25},
        }

        self.assertEqual(
            compress_message(data),
            {
                "is_deal": True,
                "sku": "767;6",
                "name": "Atomic Accolade",
                "profit": 0.11,
                "sites": ["pricestf", "pricestf"],
                "buy_site": "pricestf",
                "buy_price": {"keys": 0, "metal": 1.66},
                "sell_site": "pricestf",
                "sell_price": {"keys": 0, "metal": 1.77},
                "buy_data": {
                    "steamid": "76561199127926612",
                    "trade_url": "https://steamcommunity.com/tradeoffer/new/?partner=1167660884&token=BtpgN_cq",  # noqa
                },
                "sell_data": {
                    "steamid": "76561199127926613",
                    "trade_url": "https://steamcommunity.com/tradeoffer/new/?partner=1167660884&token=BtpgN_cq",  # noqa
                },
                "stock": {"level": 24, "limit": 25},
            },
        )
