from .database import Database
from .config import HEADLESS, GECKODRIVER_EXECUTABLE_PATH

import random
import time

from selenium.webdriver import Firefox, FirefoxOptions, FirefoxProfile, FirefoxService


class Metadata:
    def __init__(self, firefox_profile: str, headless: bool = HEADLESS):
        options = FirefoxOptions()
        service = FirefoxService(GECKODRIVER_EXECUTABLE_PATH)

        if headless:
            options.add_argument("--headless")

        options.profile = FirefoxProfile(firefox_profile)

        self.db = Database()
        self.driver = Firefox(options=options, service=service)

    def get_cookies(self, url: str, name: str) -> list[dict]:
        """Gets cookies for given URL"""
        self.driver.get(url)

        random_delay = random.randint(20, 90) / 10
        time.sleep(random_delay)

        cookies = self.driver.get_cookies()

        self.db.save_cookies({"name": name, "cookies": cookies})

        return cookies

    def close(self) -> None:
        self.driver.quit()
