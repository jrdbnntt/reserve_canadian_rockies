from datetime import datetime, timedelta

import selenium.common.exceptions
from pytz import timezone
from dateutil.relativedelta import relativedelta
from selenium.webdriver.remote.webdriver import WebDriver, WebElement
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import NoSuchElementException, TimeoutException, StaleElementReferenceException, ElementClickInterceptedException, MoveTargetOutOfBoundsException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver import Keys
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


class FormError(Exception):
    _ERROR_MESSAGE_NOT_YET_READY = 'Reserving these dates is not yet allowed.'

    def __init__(self, message: str):
        super().__init__(message.strip())

    def is_not_ready(self) -> bool:
        return self.message.startswith(FormError._ERROR_MESSAGE_NOT_YET_READY)


class WebReservationAutomator:
    """
    Automates saving reservations to a cart on the BC Parks website. Once a reservation has been saved to cart
    successfully, it should be manually purchased in the browser this program opens.
    """

    # Other paths.
    _XPATH_CONSENT_BTN = '//button[@id="consentButton"]'
    _XPATH_RESERVATION_DETAILS_PAGE_TITLE = '//h1[@id="pageTitle" and contains(./text(), "Review Reservation Details")]'

    # Search form paths.
    _XPATH_SEARCH_FORM = '//app-search-criteria/div/form/mat-tab-group/div/mat-tab-body[4]'
    _XPATH_SEARCH_BTN = "//div/div/fieldset/div[2]/button"
    _XPATH_PARTY_SIZE_INPUT = '//app-number-stepper-control[@controlid="party-size-field"]/div/div/mat-form-field/div/div[1]/div[3]/input'
    _XPATH_TENT_PADS_INPUT = '//app-number-stepper-control[@controlid="equipment-capacity-field"]/div/div/mat-form-field/div/div[1]/div[3]/input'

    # Build your stay form paths.
    _XPATH_BUILD_YOUR_STAY_FORM = '//app-build-your-stay/div/form'
    _XPATH_NIGHTS_INPUT = '//input[@id="itinerary-nights-field-1"]'
    _XPATH_AVAILABLE_AREAS_INPUT = '//input[@id="itinerary-blocker-autocomplete"]'
    _XPATH_AVAILABLE_AREAS_OPTION_FORMAT = '//mat-option[contains(.//span[@class="mat-option-text"], "{}")]'
    _XPATH_ERROR_MESSAGE_SPAN = '//mat-error/span'
    _XPATH_SAVE_RESERVATION_BTN = '//button[@id="addToItineraryButton"]'
    _XPATH_RESERVE_BTN = '//button[@id="reserve-itinerary-btn"]'
    _XPATH_ITINERARY_ITEM = '//app-itinerary-blocker-item[contains(@class, "itinerary-row")]'

    def __init__(self, driver: WebDriver):
        self.driver = driver

    def move_to_and_click_element(self, element :WebElement):
        ActionChains(self.driver).move_to_element(element).click(element).perform()

    def open_create_booking_page(self, start_date: str = None, **kwargs):
        """
        Launch browser and open the page.
        """
        # Resolve start date
        if start_date is None:
            start_date_dt = next_possible_available_start_date()
        else:
            start_date_dt = RESERVATION_CHECK_TZ.localize(datetime.strptime(start_date, "%Y-%m-%d"))

        # Load page.
        page_url = build_url_create_booking_page(start_date=start_date_dt, **kwargs)
        self.driver.get(page_url)

        # Wait for page to load search form.
        def find_search_btn(driver: WebDriver) -> WebElement:
            return driver\
                .find_element(By.XPATH, WebReservationAutomator._XPATH_SEARCH_FORM)\
                .find_element(By.XPATH, WebReservationAutomator._XPATH_SEARCH_BTN)
        WebDriverWait(self.driver, 10).until(find_search_btn)

        # Get the consent button out of the way if it's there.
        try:
            self.driver.find_element(By.XPATH, WebReservationAutomator._XPATH_CONSENT_BTN).click()
        except Exception:
            pass

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
        self.move_to_and_click_element(party_size_input)
        party_size_input.send_keys(Keys.BACKSPACE)
        party_size_input.send_keys(str(party_size))

        # Input tent pads amount.
        self.move_to_and_click_element(tent_pads_input)
        tent_pads_input.send_keys(Keys.BACKSPACE)
        tent_pads_input.send_keys(str(tent_pads))

        # Click search to submit form.
        self.move_to_and_click_element(search_btn)

        # Wait for results to appear.
        WebDriverWait(self.driver, 10)\
            .until(lambda d: d.find_element(By.XPATH, WebReservationAutomator._XPATH_BUILD_YOUR_STAY_FORM))

    def save_reservation(self, nights: int, area: str):
        """
        Attempt to save a reservation in the "Build Your Stay" component. This can fail due to a lot of different
        reasons, known and unknown, and should be polled until it succeeds or times out. If this succeeds, it is
        expected that the reservation should be saved in the cart for 15 minutes and is ready for manual user checkout,
        which should be done ASAP to avoid potential checkout timeout/duplication on the BC Parks' end.
        """
        poll_frequency = .1

        # Find elements
        build_your_stay_form = self.driver.find_element(By.XPATH, WebReservationAutomator._XPATH_BUILD_YOUR_STAY_FORM)
        nights_input = build_your_stay_form.find_element(By.XPATH, WebReservationAutomator._XPATH_NIGHTS_INPUT)
        area_input = build_your_stay_form.find_element(By.XPATH, WebReservationAutomator._XPATH_AVAILABLE_AREAS_INPUT)
        save_btn = build_your_stay_form.find_element(By.XPATH, WebReservationAutomator._XPATH_SAVE_RESERVATION_BTN)
        reserve_btn = build_your_stay_form.find_element(By.XPATH, WebReservationAutomator._XPATH_RESERVE_BTN)

        # Input nights.
        nights_input.clear()
        nights_input.send_keys(str(nights))

        # Input area.
        area_input.clear()
        self.move_to_and_click_element(area_input)

        area_option = None

        def find_area_option(d):
            nonlocal area_option
            area_option = d.find_element(By.XPATH, WebReservationAutomator._XPATH_AVAILABLE_AREAS_OPTION_FORMAT.format(area))
            return area_option
        try:
            WebDriverWait(self.driver, 2, poll_frequency=poll_frequency).until(find_area_option)
        except TimeoutException as e:
            raise Exception('Failed to find area option element for "{}"'.format(area)) from e
        if isinstance(area_option, WebElement):
            self.move_to_and_click_element(area_option)
        else:
            raise Exception('area_option not set by WebDriverWait')

        # Check for error message. One will appear if it's too early or there is no availability.
        self.check_for_build_your_stay_error(build_your_stay_form)

        # So far so good, let's try to save the reservation.
        self.move_to_and_click_element(save_btn)
        self.check_for_build_your_stay_error(build_your_stay_form)

        reserve_err = None

        def form_error_or_itinerary_item_found(d):
            nonlocal reserve_err
            try:
                self.check_for_build_your_stay_error(build_your_stay_form)
                return build_your_stay_form.find_element(By.XPATH, WebReservationAutomator._XPATH_ITINERARY_ITEM)
            except FormError as er:
                reserve_err = er

        WebDriverWait(self.driver, 2, poll_frequency=poll_frequency).until(form_error_or_itinerary_item_found)
        if reserve_err is not None:
            raise reserve_err

        def wait_for_reservation_confirmation(d):
            try:
                return d.find_element(By.XPATH, WebReservationAutomator._XPATH_RESERVATION_DETAILS_PAGE_TITLE)
            except NoSuchElementException:
                pass
            try:
                self.move_to_and_click_element(reserve_btn)
            except (StaleElementReferenceException, ElementClickInterceptedException, MoveTargetOutOfBoundsException):
                pass

        WebDriverWait(self.driver, 3, poll_frequency=poll_frequency).until(wait_for_reservation_confirmation)

    @staticmethod
    def check_for_build_your_stay_error(build_your_stay_form: WebElement):
        error_message = None
        try:
            error_message_span = build_your_stay_form.find_element(By.XPATH, WebReservationAutomator._XPATH_ERROR_MESSAGE_SPAN)
            error_message = error_message_span.text
        except Exception:
            pass
        if error_message is not None:
            raise FormError(message=error_message)
