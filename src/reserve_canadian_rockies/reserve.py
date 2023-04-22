import os.path

from bcparks import WebReservationAutomator
import config
from selenium import webdriver
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.firefox.options import Options as FireFoxOptions
from datetime import datetime


def initialize_selenium_driver() -> WebDriver:
    options = FireFoxOptions()
    return webdriver.Firefox(
        options=options,
        executable_path=config.SELENIUM_FIREFOX_DRIVER_EXE_PATH
    )


def reserve():
    driver = initialize_selenium_driver()
    try:
        wra = WebReservationAutomator(driver=driver)
        wra.open_create_booking_page()
        wra.fill_options_and_search(party_size=4)
    finally:
        if not config.SELENIUM_KEEP_OPEN:
            driver.close()


if __name__ == '__main__':
    reserve()
