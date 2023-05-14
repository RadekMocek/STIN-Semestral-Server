import os
import sys
from datetime import datetime
import pytz

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import services.exchange_rates_service as exchange_rates_service


def test_should_get_exchange_rates_from_cnb_today():
    compare_date = datetime(2023, 5, 12).replace(tzinfo=pytz.timezone("Europe/Prague"))
    cache_date = "12.05.2023"
    result = exchange_rates_service.__should_get_exchange_rates_from_cnb(compare_date, cache_date)
    assert result == False


def test_should_get_exchange_rates_from_cnb_weekend_true():
    compare_date = datetime(2023, 5, 13).replace(tzinfo=pytz.timezone("Europe/Prague"))
    cache_date = "11.05.2023"
    result = exchange_rates_service.__should_get_exchange_rates_from_cnb(compare_date, cache_date)
    assert result == True


def test_should_get_exchange_rates_from_cnb_weekend_false():
    compare_date = datetime(2023, 5, 13).replace(tzinfo=pytz.timezone("Europe/Prague"))
    cache_date = "12.05.2023"
    result = exchange_rates_service.__should_get_exchange_rates_from_cnb(compare_date, cache_date)
    assert result == False


def test_should_get_exchange_rates_from_cnb_latest_1400():
    compare_date = datetime(2023, 5, 15, 14, 0).replace(tzinfo=pytz.timezone("Europe/Prague"))
    cache_date = "12.05.2023"
    result = exchange_rates_service.__should_get_exchange_rates_from_cnb(compare_date, cache_date)
    assert result == False


def test_should_get_exchange_rates_from_cnb_old_1400_monday():
    compare_date = datetime(2023, 5, 15, 14, 0).replace(tzinfo=pytz.timezone("Europe/Prague"))
    cache_date = "05.05.2023"
    result = exchange_rates_service.__should_get_exchange_rates_from_cnb(compare_date, cache_date)
    assert result == True


def test_should_get_exchange_rates_from_cnb_old_1400():
    compare_date = datetime(2023, 5, 17, 14, 0).replace(tzinfo=pytz.timezone("Europe/Prague"))
    cache_date = "15.05.2023"
    result = exchange_rates_service.__should_get_exchange_rates_from_cnb(compare_date, cache_date)
    assert result == True


def test_should_get_exchange_rates_from_cnb_old_1400_false():
    compare_date = datetime(2023, 5, 17, 14, 0).replace(tzinfo=pytz.timezone("Europe/Prague"))
    cache_date = "16.05.2023"
    result = exchange_rates_service.__should_get_exchange_rates_from_cnb(compare_date, cache_date)
    assert result == False


def test_should_get_exchange_rates_from_cnb_1431():
    compare_date = datetime(2023, 5, 15, 14, 31).replace(tzinfo=pytz.timezone("Europe/Prague"))
    cache_date = "12.05.2023"
    result = exchange_rates_service.__should_get_exchange_rates_from_cnb(compare_date, cache_date)
    assert result == True


def test_should_get_exchange_rates_from_cnb_1500():
    compare_date = datetime(2023, 5, 15, 15, 0).replace(tzinfo=pytz.timezone("Europe/Prague"))
    cache_date = "12.05.2023"
    result = exchange_rates_service.__should_get_exchange_rates_from_cnb(compare_date, cache_date)
    assert result == True
