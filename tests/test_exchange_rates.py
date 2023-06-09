import os
import sys
from datetime import datetime
import pytz
import pathlib
import requests_mock
from pyfakefs.fake_filesystem_unittest import Patcher
import yaml
from freezegun import freeze_time

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import services.exchange_rates_service as exchange_rates_service


EXCHANGE_RATES_ONLINE_SOURCE = "https://www.cnb.cz/cs/financni-trhy/devizovy-trh/kurzy-devizoveho-trhu/kurzy-devizoveho-trhu/denni_kurz.txt"
TEST_DATA_PATH = pathlib.Path(__file__).parent / "data"
DATABASE_PATH = pathlib.Path(__file__).parent.parent / "database"
EXCHANGE_RATES_OFFLINE_PATH = DATABASE_PATH / "exchange_rates.yaml"


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


EXPECTED_EXCHANGE_RATES_DICT_2023_05_12 = {
    "_Date": "12.05.2023",
    "CZK": 1,
    "AUD": 14.481,
    "BGN": 12.07,
    "BRL": 4.379,
    "CAD": 16.064,
    "CHF": 24.233,
    "CNY": 3.118,
    "DKK": 3.169,
    "EUR": 23.605,
    "GBP": 27.128,
    "HKD": 2.764,
    "HUF": 0.06366,
    "IDR": 0.00147,
    "ILS": 5.944,
    "INR": 0.2637,
    "ISK": 0.15705,
    "JPY": 0.16061,
    "KRW": 0.01622,
    "MXN": 1.23,
    "MYR": 4.84,
    "NOK": 2.031,
    "NZD": 13.49,
    "PHP": 0.38835,
    "PLN": 5.208,
    "RON": 4.785,
    "SEK": 2.1,
    "SGD": 16.245,
    "THB": 0.63785,
    "TRY": 1.106,
    "USD": 21.678,
    "XDR": 29.191,
    "ZAR": 1.127,
}


def test_parse_exchange_rates_from_cnb():
    with open(TEST_DATA_PATH / "denni_kurz_2023_05_12.txt", "r", encoding="utf8") as file:
        input = file.read()
    result = exchange_rates_service.__parse_exchange_rates_from_cnb(input)
    assert result == EXPECTED_EXCHANGE_RATES_DICT_2023_05_12


def test_get_exchange_rates_from_cnb():
    with open(TEST_DATA_PATH / "denni_kurz_2023_05_12.txt", "r", encoding="utf8") as file:
        input = file.read()
    with requests_mock.Mocker() as mocker, Patcher(use_cache=False) as patcher:
        mocker.get(EXCHANGE_RATES_ONLINE_SOURCE, text=input)
        patcher.fs.create_file(EXCHANGE_RATES_OFFLINE_PATH)
        assert exchange_rates_service.__get_exchange_rates_from_cnb() == EXPECTED_EXCHANGE_RATES_DICT_2023_05_12


@freeze_time("2023-05-12")
def test_get_exchange_rates():
    with Patcher(use_cache=False) as patcher:
        patcher.fs.create_file(EXCHANGE_RATES_OFFLINE_PATH)
        with open(EXCHANGE_RATES_OFFLINE_PATH, "w", encoding="utf8") as file:
            yaml.dump(EXPECTED_EXCHANGE_RATES_DICT_2023_05_12, file)
        assert exchange_rates_service.get_exchange_rates() == EXPECTED_EXCHANGE_RATES_DICT_2023_05_12
