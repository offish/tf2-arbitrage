# selenium
FIREFOX_PROFILE_PATH = (
    r"C:\Users\USER\AppData\Roaming\Mozilla\Firefox\Profiles\SOME.PROFILE"
)
GECKODRIVER_EXECUTABLE_PATH = r"geckodriver"
HEADLESS = True
STEAM_ID = "76561198828172881"


# api keys
INVENTORY_PROVIDER = "steamcommunity"  # or steamsupply
INVENTORY_API_KEY = ""  # steamcommunity does not require an api key
STN_API_KEY = ""

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
    "Non-Craftable",
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
BACKPACK_TF_PAGES = 3  # how many pages to fetch when getting an item (trade urls also)
TRADING_SITES_INTERVAL = 10 * 60 + 5.19  # ~10 minutes
STN_TIMEOUT = 60.0  # seconds to sleep between rate limits

SKIP_STN_SCHEMA_FETCH = True
STN_SCHEMA_PATH = "./static/stn_schema.json"

SKIP_INVENTORY_FETCH = False
INVENTORY_PURE_STOCK = {"keys": 1, "metal": 52.11}  # if skip_inventory_fetch is True
# SKIP_INVENTORY_FETCH = False
# SKIP_PRICES_TF_FETCH = False
SKIP_PRICES_TF_FETCH = True
# MAX_PRICES_TF_PAGES = 30
MAX_PRICES_TF_PAGES = 180  # -1 for all
MINIMUM_PROFIT_REQUIRED = 0.11
PRICES_TF_FILE = "./prod/1711970722_prices.json"
