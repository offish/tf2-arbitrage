from .sites.sites import Site
from .database import Database
from .metadata import Metadata
from .config import FIREFOX_PROFILE_PATH

import logging
import time


def get_sites_outdated_cookies(db: Database, sites: list[Site]) -> list[Site]:
    oudated_sites = []

    for site in sites:
        cookies = db.get_cookies(site.name)

        if not cookies:
            oudated_sites.append(site)
            continue

        current_time = time.time()

        for cookie in cookies:
            # google tracking cookies
            if "_g" == cookie["name"][:2]:
                continue

            if current_time <= cookie["expiry"]:
                continue

            oudated_sites.append(site)
            break

    return oudated_sites


def get_new_cookies(sites: list[Site]) -> None:
    metadata = Metadata(FIREFOX_PROFILE_PATH)

    for site in sites:
        logging.info(f"getting cookies for {site.name}")
        metadata.get_cookies(site.url, site.name)

    metadata.close()


def set_cookies(sites: list[Site]) -> None:
    db = Database()

    outdated_cookie_sites = get_sites_outdated_cookies(db, sites)

    if outdated_cookie_sites:
        logging.info("some cookies are outdated, getting new ones")
        get_new_cookies(outdated_cookie_sites)

    for site in sites:
        cookies = db.get_cookies(site.name)
        site.set_cookies(cookies)
