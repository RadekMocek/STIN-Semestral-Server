import os
import shutil
import sys
import pytest
import pathlib
import yaml
from datetime import datetime
from freezegun import freeze_time
from pyfakefs.fake_filesystem_unittest import Patcher

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import services.payments_service as payments_service
import services.database_service as database_service

DATABASE_PATH = pathlib.Path(__file__).parent.parent / "database"
USERS_PATH = DATABASE_PATH / "users.yaml"
BANK_ACCOUNTS_PATH = DATABASE_PATH / "bank_accounts.yaml"
PAYMENTS_PATH = DATABASE_PATH / "payments.yaml"
EXCHANGE_RATES_PATH = DATABASE_PATH / "exchange_rates.yaml"

rates_dict = {
    "_Date": "12.05.2023",
    "CZK": 1,
    "AUD": 14.481,
}


@pytest.mark.parametrize(
    "amount, currency, expected",
    [
        (0, "CZK", 0),
        (1, "CZK", 1),
        (14.481, "AUD", 209.699361),
    ],
)
def test_currency_to_czk(amount, currency, expected):
    assert payments_service.currency_to_czk(amount, currency, rates_dict) == expected


@freeze_time("2012-01-01")
def test_payment():
    bank_accounts_before = [
        {"balance": 100, "currency": "CZK", "iban": "CZTEST1", "owner": "user1"},
        {"balance": 200, "currency": "CZK", "iban": "CZTEST2", "owner": "user2"},
        {"balance": 300, "currency": "AUD", "iban": "CZTEST3", "owner": "user1"},
    ]
    user_bank_accounts_after = [
        {"balance": 90, "currency": "CZK", "iban": "CZTEST1", "owner": "user1"},
        {"balance": 300, "currency": "AUD", "iban": "CZTEST3", "owner": "user1"},
    ]
    used_account = bank_accounts_before[0]

    # Přes pyfakefs test prochází lokálně ale ne na githubu, takže si soubory vytvořím dočasně na disku
    if not os.path.exists(DATABASE_PATH):
        os.makedirs(DATABASE_PATH)
    else:
        assert False  # Pokud databáze již existuje, tak test ukončíme

    with open(BANK_ACCOUNTS_PATH, "w+", encoding="utf8") as file:
        yaml.dump(bank_accounts_before, file)

    PAYMENTS_PATH.touch()
    # ---

    payments_service.payment_outgoing(used_account, 10)

    assert database_service.get_bank_accounts("user1") == user_bank_accounts_after

    with open(DATABASE_PATH / "payments.yaml", "r", encoding="utf8") as file:
        payments = file.read()
    assert payments == f'- iban: "CZTEST1"\n  value: -10\n  timestamp: {datetime.timestamp(datetime.now())}\n'

    # Celá databáze je na konci testu smazána
    shutil.rmtree(DATABASE_PATH)
