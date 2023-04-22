from unittest import TestCase
import bcparks
from datetime import datetime


class Test(TestCase):
    def test_build_url_create_booking_page(self):
        self.assertEqual(
            bcparks.build_url_create_booking_page(
                resource_location_id=-2147483569,
                map_id=-2147483480,
                search_tab_group_id=3,
                booking_category_id=4,
                start_date=datetime.strptime("2023-08-21", "%Y-%m-%d"),
                end_date=datetime.strptime("2023-08-24", "%Y-%m-%d"),
                nights=3,
                is_reserving=True,
                party_size=4
            ),
            'https://camping.bcparks.ca/create-booking/results?resourceLocationId=-2147483569&mapId=-2147483480&searchTabGroupId=3&bookingCategoryId=4&startDate=2023-08-21&endDate=2023-08-24&nights=3&isReserving=true&partySize=4'
        )
        self.assertEqual(
            bcparks.build_url_create_booking_page(
                party_size=4,
                start_date=datetime.strptime("2023-08-21", "%Y-%m-%d"),
                nights=3,
            ),
            'https://camping.bcparks.ca/create-booking/results?resourceLocationId=-2147483569&mapId=-2147483480&searchTabGroupId=3&bookingCategoryId=4&startDate=2023-08-21&endDate=2023-08-24&nights=3&isReserving=true&partySize=4'
        )
