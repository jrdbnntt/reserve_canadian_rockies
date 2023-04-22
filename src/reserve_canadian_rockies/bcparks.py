from datetime import datetime, timedelta
from pytz import timezone
from dateutil.relativedelta import relativedelta
from selenium.webdriver.remote.webdriver import WebDriver, WebElement
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.common.by import By

URL_TEMPLATE_CREATE_BOOKING_PAGE = 'https://camping.bcparks.ca/create-booking/results?' \
                                   'resourceLocationId={resource_location_id}' \
                                   '&mapId={map_id}' \
                                   '&searchTabGroupId={search_tab_group_id}' \
                                   '&bookingCategoryId={booking_category_id}' \
                                   '&startDate={start_date}' \
                                   '&isReserving={is_reserving}'
URL_DATE_FORMAT = '%Y-%m-%d'

MAX_ADVANCE_RESERVATION_MONTHS = 4
RESERVATION_CHECK_TZ = timezone("US/Pacific")
RESERVATION_OPEN_HOUR = 7  # PDT


def next_possible_available_start_date(from_date: datetime = None, open_hour: int = RESERVATION_OPEN_HOUR) -> datetime:
    if from_date is None:
        from_date = datetime.now()
    else:
        now_dt = RESERVATION_CHECK_TZ.localize(datetime.now())
        from_date += relativedelta(hour=now_dt.hour, minute=now_dt.minute, second=0, microsecond=0)
    from_date = RESERVATION_CHECK_TZ.localize(from_date)
    day_offset = 0 if from_date.hour < open_hour else 1
    return from_date + relativedelta(months=MAX_ADVANCE_RESERVATION_MONTHS, days=day_offset, hour=0, minute=0, second=0, microsecond=0)


def build_url_create_booking_page(
        start_date: datetime,
        resource_location_id: int = -2147483569,
        map_id: int = -2147483480,
        search_tab_group_id: int = 3,
        booking_category_id: int = 4,
        is_reserving: bool = True
) -> str:
    return URL_TEMPLATE_CREATE_BOOKING_PAGE.format(
        start_date=start_date.strftime(URL_DATE_FORMAT),
        resource_location_id=resource_location_id,
        map_id=map_id,
        search_tab_group_id=search_tab_group_id,
        booking_category_id=booking_category_id,
        is_reserving=str(is_reserving).lower()
    )


class WebReservationAutomator:
    """
    Automates saving reservations to a cart on the BC Parks website. Once a reservation has been saved to cart
    successfully, it should be manually purchased in the browser this program opens.
    """

    _XPATH_SEARCH_FORM = '//app-search-criteria/div/form/mat-tab-group/div/mat-tab-body[4]'
    _XPATH_SEARCH_BTN = "//div/div/fieldset/div[2]/button"
    _XPATH_PARTY_SIZE_INPUT = '//app-number-stepper-control[@controlid="party-size-field"]/div/div/mat-form-field/div/div[1]/div[3]/input'
    _XPATH_TENT_PADS_INPUT = '//app-number-stepper-control[@controlid="equipment-capacity-field"]/div/div/mat-form-field/div/div[1]/div[3]/input'

    def __init__(self, driver: WebDriver):
        self.driver = driver

    def open_create_booking_page(self, start_date: datetime = None, **kwargs):
        """
        Launch browser and open the page.
        """
        if start_date is None:
            start_date = next_possible_available_start_date()
        page_url = build_url_create_booking_page(start_date=start_date, **kwargs)
        self.driver.get(page_url)
        WebDriverWait(self.driver, 10).until(self.find_search_btn)

    @staticmethod
    def find_search_btn(driver: WebDriver) -> WebElement:
        return driver.find_element(By.XPATH, WebReservationAutomator._XPATH_SEARCH_FORM).find_element(By.XPATH, WebReservationAutomator._XPATH_SEARCH_BTN)

    def fill_options_and_search(self, party_size: int, tent_pads: int = 1):
        """
        Fills out the "Backcountry" search form and clicks the "Search" button.
        Expects the "Backcountry Reservation" option to be selected and the Park and Arrival inputs to be prefilled on
        page load from URL query parameters.
        """
        # Find elements.
        search_form = self.driver.find_element(By.XPATH, WebReservationAutomator._XPATH_SEARCH_FORM)
        search_btn = search_form.find_element(By.XPATH, WebReservationAutomator._XPATH_SEARCH_BTN)
        party_size_input = search_form.find_element(By.XPATH, WebReservationAutomator._XPATH_PARTY_SIZE_INPUT)
        tent_pads_input = search_form.find_element(By.XPATH, WebReservationAutomator._XPATH_TENT_PADS_INPUT)

        # Input party size.
        party_size_input.clear()
        party_size_input.send_keys(str(party_size))

        # Input tent pads amount.
        tent_pads_input.clear()
        tent_pads_input.send_keys(str(tent_pads))

        # Click search to submit form.
        search_btn.click()


    def save_reservation(self, nights: int, area: str):
        """
        Attempt to save a reservation in the "Build Your Stay" component. This can fail due to a lot of different
        reasons, known and unknown, and should be polled until it succeeds or times out. If this succeeds, it is
        expected that the reservation should be saved in the cart for 15 minutes and is ready for manual user checkout,
        which should be done ASAP to avoid potential checkout timeout/duplication on the BC Parks' end.
        """
        pass
