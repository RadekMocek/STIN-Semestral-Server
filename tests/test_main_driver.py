import os
import sys
import base64
import jwt
import datetime
import pytest
from pyfakefs.fake_filesystem_unittest import Patcher
import pathlib
import yaml

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import main_driver
from main_driver import app
import services.database_service as database_service

DATABASE_PATH = pathlib.Path(__file__).parent.parent / "database"
USERS_PATH = DATABASE_PATH / "users.yaml"
BANK_ACCOUNTS_PATH = DATABASE_PATH / "bank_accounts.yaml"
PAYMENTS_PATH = DATABASE_PATH / "payments.yaml"
EXCHANGE_RATES_PATH = DATABASE_PATH / "exchange_rates.yaml"


def test_login_bad_request(mocker):
    mocker.patch("services.database_service.get_user", return_value={"username": "user", "password": "passwd"})
    response = app.test_client().post("/login", headers={"Authorization": "Basic "})
    assert response.status_code == 400


def test_login_invalid(mocker):
    mocker.patch("services.database_service.get_user", return_value={"username": "user", "password": "passwd"})
    response = app.test_client().post("/login", headers={"Authorization": f'Basic {(base64.b64encode(b"user:invalid")).decode("utf-8")}'})
    assert response.status_code == 401


def test_login_successful(mocker):
    mocker.patch("services.database_service.get_user", return_value={"username": "user", "password": "passwd", "email": "test@example.com"})
    mocker.patch("flask_mail.Message", autospec=True)  # Aby se neodesílal mail
    mocker.patch("flask_mail.Mail.send", autospec=True)  # Aby se neodesílal mail
    response = app.test_client().post("/login", headers={"Authorization": f'Basic {(base64.b64encode(b"user:passwd")).decode("utf-8")}'})
    assert response.status_code == 200
    assert len(main_driver.codes) == 1


def test_authorize_successful():
    username = "user"
    code = "8QPYZDH0WJKOZ8OT"
    expiration = datetime.datetime.utcnow() + datetime.timedelta(minutes=3)
    main_driver.codes[username] = (code, expiration)

    data = {"username": username, "code": code}
    response = app.test_client().post("/authorize", json=data)

    assert response.status_code == 200
    assert "token" in response.json

    token = response.json["token"]
    decoded_token = jwt.decode(token, app.config["SECRET_KEY"], algorithms=["HS256"])
    assert decoded_token["username"] == username


def test_authorize_with_incorrect_code():
    username = "user"
    code = "8QPYZDH0WJKOZ8OT"
    expiration = datetime.datetime.utcnow() + datetime.timedelta(minutes=3)
    main_driver.codes[username] = (code, expiration)

    data = {"username": username, "code": "VRUN9OLD3X9ABH75"}
    response = app.test_client().post("/authorize", json=data)

    assert response.status_code == 401


def test_authorize_with_expired_code():
    username = "user"
    code = "8QPYZDH0WJKOZ8OT"
    expiration = datetime.datetime.utcnow() - datetime.timedelta(minutes=3)
    main_driver.codes[username] = (code, expiration)

    data = {"username": username, "code": code}
    response = app.test_client().post("/authorize", json=data)

    assert response.status_code == 401


def test_no_token():
    response = app.test_client().post("/payment_outgoing")
    assert response.json["message"] == "Chybějící token."
    assert response.status_code == 401


def test_bad_token():
    response = app.test_client().post("/payment_outgoing", headers={"Authorization": f"Bearer abcdefg"})
    assert response.json["message"] == "Neplatný token."
    assert response.status_code == 401


@pytest.mark.parametrize(
    "currency, amount, exchange_rates, expected",
    [
        ("CZK", 10, ["CZK"], True),
        ("_Date", 10, ["CZK"], False),
        ("_AUD", 10, ["CZK"], False),
        ("CZK", -10, ["CZK"], False),
        ("CZK", 0, ["CZK"], False),
        (10, 10, ["CZK"], False),
        (10, "CZK", ["CZK"], False),
    ],
)
def test_is_payment_arguments_valid(currency, amount, exchange_rates, expected):
    assert main_driver.__is_payment_arguments_valid(currency, amount, exchange_rates) == expected


EXCHANGE_RATES_DICT_2023_05_12 = {
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


def test_payment_outgoing_with_coversion_to_czk_and_overdraft():
    bank_accounts = [{"balance": 14, "currency": "CZK", "iban": "TEST", "owner": "test_user"}]
    bank_accounts_after = [{"balance": -0.5291, "currency": "CZK", "iban": "TEST", "owner": "test_user"}]
    with Patcher(use_cache=False) as patcher:
        # "Mock" cached exchange rates
        patcher.fs.create_file(EXCHANGE_RATES_PATH)
        with open(EXCHANGE_RATES_PATH, "w", encoding="utf8") as file:
            yaml.dump(EXCHANGE_RATES_DICT_2023_05_12, file)
        # "Mock" bank account
        with open(BANK_ACCOUNTS_PATH, "w", encoding="utf8") as file:
            yaml.dump(bank_accounts, file)
        # Run test
        with app.app_context():
            main_driver.__payment_outgoing("test_user", "AUD", 1)
        assert database_service.get_bank_account_by_iban("TEST") == bank_accounts_after
