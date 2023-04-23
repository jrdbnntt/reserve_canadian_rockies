import os.path
import sys

from bcparks import WebReservationAutomator
import config
from selenium import webdriver
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.firefox.options import Options as FireFoxOptions
from datetime import datetime
import traceback


def initialize_selenium_driver() -> WebDriver:
    options = FireFoxOptions()
    return webdriver.Firefox(
        options=options,
        executable_path=config.SELENIUM_FIREFOX_DRIVER_EXE_PATH
    )


def reserve():
    driver = initialize_selenium_driver()
    ready_for_checkout = False
    try:
        wra = WebReservationAutomator(driver=driver)
        wra.open_create_booking_page()
        wra.fill_options_and_search(party_size=config.BCPARKS_PARTY_SIZE)
        while True:
            try:
                wra.save_reservation(nights=config.BCPARKS_NIGHTS, area=config.BCPARKS_RESERVATION_AREA)
            except Exception as e:
                print('Caught exception while trying to save reservation:\n{}'.format(''.join(traceback.format_exception(e))))
                if config.BCPARKS_RETRY_ON_RESERVE_FAIL:
                    print('\n\nRetrying...')
                    continue
                else:
                    raise e
            break
        print('\n\n\nGot it in the cart!!!!!\n\nNeed to check out manually')
        ready_for_checkout = True
    finally:
        if not ready_for_checkout and not config.SELENIUM_KEEP_OPEN:
            driver.close()


if __name__ == '__main__':
    reserve()
