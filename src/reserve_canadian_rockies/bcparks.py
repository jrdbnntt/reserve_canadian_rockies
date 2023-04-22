from datetime import datetime, timedelta

URL_TEMPLATE_CREATE_BOOKING_PAGE = 'https://camping.bcparks.ca/create-booking/results?' \
                                   'resourceLocationId={resource_location_id}' \
                                   '&mapId={map_id}' \
                                   '&searchTabGroupId={search_tab_group_id}' \
                                   '&bookingCategoryId={booking_category_id}' \
                                   '&startDate={start_date}' \
                                   '&endDate={end_date}' \
                                   '&nights={nights}' \
                                   '&isReserving={is_reserving}' \
                                   '&partySize={party_size}'
URL_DATE_FORMAT = '%Y-%m-%d'

def build_url_create_booking_page(
        party_size: int,
        start_date: datetime,
        nights: int,
        end_date: datetime = None,
        resource_location_id: int = -2147483569,
        map_id: int = -2147483480,
        search_tab_group_id: int = 3,
        booking_category_id: int = 4,
        is_reserving: bool = True
) -> str:
    if party_size <= 0:
        raise ValueError("party_size must be greater than 0")
    if start_date is None or start_date < datetime.now():
        raise ValueError("start_date is required and must be in the future")
    if nights <= 0:
        raise ValueError("nights must be greater than 0")
    if end_date is None:
        end_date = start_date + timedelta(days=nights)
    elif end_date < start_date:
        raise ValueError("end_date must be after start_date")
    elif end_date.date() != (start_date + timedelta(days=nights)).date():
        raise ValueError("nights is set to {}, but end_date is {} days after the start_date".format(
            nights,
            (end_date - start_date).days)
        )
    return URL_TEMPLATE_CREATE_BOOKING_PAGE.format(
        party_size=party_size,
        start_date=start_date.strftime(URL_DATE_FORMAT),
        nights=nights,
        end_date=end_date.strftime(URL_DATE_FORMAT),
        resource_location_id=resource_location_id,
        map_id=map_id,
        search_tab_group_id=search_tab_group_id,
        booking_category_id=booking_category_id,
        is_reserving=str(is_reserving).lower()
    )
