from unittest import TestCase
import bcparks
from datetime import datetime

DATE_FORMAT = "%Y-%m-%d"

class Test(TestCase):
    def test_build_url_create_booking_page(self):
        self.assertEqual(
            bcparks.build_url_create_booking_page(
                resource_location_id=-2147483569,
                map_id=-2147483480,
                search_tab_group_id=3,
                booking_category_id=4,
                start_date=datetime.strptime("2023-08-21", DATE_FORMAT),
                is_reserving=True
            ),
            'https://camping.bcparks.ca/create-booking/results?resourceLocationId=-2147483569&mapId=-2147483480&searchTabGroupId=3&bookingCategoryId=4&startDate=2023-08-21&isReserving=true'
        )
        self.assertEqual(
            bcparks.build_url_create_booking_page(start_date=datetime.strptime("2023-08-21", DATE_FORMAT)),
            'https://camping.bcparks.ca/create-booking/results?resourceLocationId=-2147483569&mapId=-2147483480&searchTabGroupId=3&bookingCategoryId=4&startDate=2023-08-21&isReserving=true'
        )

    def test_next_possible_available_start_date(self):
        from_date = datetime.strptime("2023-04-21", DATE_FORMAT)
        expected = datetime.strptime("2023-08-22", DATE_FORMAT)
        actual = bcparks.next_possible_available_start_date(from_date)
        self.assertEqual(expected.strftime(DATE_FORMAT), actual.strftime(DATE_FORMAT))

        from_date = datetime.strptime("2023-04-30", DATE_FORMAT)
        expected = datetime.strptime("2023-08-31", DATE_FORMAT)
        actual = bcparks.next_possible_available_start_date(from_date)
        self.assertEqual(expected.strftime(DATE_FORMAT), actual.strftime(DATE_FORMAT))

        from_date = datetime.strptime("2023-04-21", DATE_FORMAT)
        expected = datetime.strptime("2023-08-21", DATE_FORMAT)
        now_local_hour = bcparks.RESERVATION_CHECK_TZ.localize(datetime.now()).hour
        open_hour = bcparks.RESERVATION_OPEN_HOUR if now_local_hour < bcparks.RESERVATION_OPEN_HOUR else now_local_hour + 1
        actual = bcparks.next_possible_available_start_date(from_date, open_hour=open_hour)
        self.assertEqual(expected.strftime(DATE_FORMAT), actual.strftime(DATE_FORMAT))

        # Unclear how this behaves with BC Parks, have not observed this case yet. Will leave in if we reach it.
        # from_date = datetime.strptime("2023-05-01", DATE_FORMAT)
        # expected = datetime.strptime("2023-09-01", DATE_FORMAT)
        # actual = bcparks.next_possible_available_start_date(from_date)
        # self.assertEqual(expected.strftime(DATE_FORMAT), actual.strftime(DATE_FORMAT))
