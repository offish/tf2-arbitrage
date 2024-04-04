# selenium
FIREFOX_PROFILE_PATH = (
    r"C:\Users\USER\AppData\Roaming\Mozilla\Firefox\Profiles\SOME.PROFILE"
)
HEADLESS = True


# api keys
STEAMSUPPLY_API_KEY = ""
STN_API_KEY = ""
STEAM_ID = "76561198828172881"

# database
DB_HOST = "localhost"
DB_PORT = 27017

# other
BLACKLISTED_INCLUDE = [
    "(Factory New)",
    "(Minimal Wear)",
    "(Field-Tested)",
    "(Well-Worn)",
    "(Battle Scarred)",
    "Unusual",
    # "Vintage",
    "Killstreak",
    "Haunted",
    "#",
    "Strange Part:",
    "Case",
    "Crate",
    "Key",
    "Non-Craftable",  # soon supported
    "Australium",
]
BLACKLISTED_LISTING_DETAIL = [
    "spell",
    "paint",
    "lvl",
    "level",
    "black",
    "white",
    "pink",
    "lime",
    "gold",
    "#",
    "craft #",  # not craft since non-crafatble or uncraftable
    "number",
    "voices",
    "footprints",
    "halloween",
]
MAX_LAST_BUMP = 60.0  # minutes since last bump
BACKPACK_TF_PAGES = 3
TRADING_SITES_INTERVAL = 10 * 60 + 5.19  # ~15 minutes
STN_TIMEOUT = 60.0

SKIP_INVENTORY_FETCH = True
# SKIP_INVENTORY_FETCH = False
SKIP_PRICES_TF_FETCH = False
# SKIP_PRICES_TF_FETCH = True
# MAX_PRICES_TF_PAGES = 30
MAX_PRICES_TF_PAGES = 180  # -1 for all
MINIMUM_PROFIT_REQUIRED = 0.11
PRICES_TF_FILE = "./prod/1709979305_prices.json"
