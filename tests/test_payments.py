import os
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

test_data_path = pathlib.Path(__file__).parent / "data"
database_path = pathlib.Path(__file__).parent.parent / "database"

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


# @freeze_time("2012-01-01")
# def test_payment(fs):
#    account_before_payment = """- balance: 100
#  currency: CZK
#  iban: CZTEST
#  owner: test"""
#
#    account_after_payment = {"balance": 90, "currency": "CZK", "iban": "CZTEST", "owner": "test"}
#
#    fs.create_file(database_path / "bank_accounts.yaml", contents=account_before_payment)
#    fs.create_file(database_path / "payments.yaml")
#
#    payments_service.payment_outgoing({"balance": 100, "currency": "CZK", "iban": "CZTEST", "owner": "test"}, 10)
#
#    with open(database_path / "bank_accounts.yaml", "r", encoding="utf8") as file:
#        bank_accounts = yaml.safe_load(file)
#
#    assert bank_accounts == [account_after_payment]
#
#    with open(database_path / "payments.yaml", "r", encoding="utf8") as file:
#        payments = file.read()
#
#    assert payments == f'- iban: "CZTEST"\n  value: -10\n  timestamp: {datetime.timestamp(datetime.now())}\n'


@freeze_time("2012-01-01")
def test_payment():
    account_before_payment = """- balance: 100
  currency: CZK
  iban: CZTEST
  owner: test"""

    account_after_payment = {"balance": 90, "currency": "CZK", "iban": "CZTEST", "owner": "test"}
    with Patcher(use_cache=False) as patcher:
        patcher.fs.create_file(database_path / "bank_accounts.yaml", contents=account_before_payment)
        patcher.fs.create_file(database_path / "payments.yaml")
        print("Before payment: ", database_service.get_bank_accounts("test"))
        payments_service.payment_outgoing({"balance": 100, "currency": "CZK", "iban": "CZTEST", "owner": "test"}, 10)
    
        with open(database_path / "bank_accounts.yaml", "r", encoding="utf8") as file:
            bank_accounts = yaml.safe_load(file)

        assert bank_accounts == [account_after_payment]

        with open(database_path / "payments.yaml", "r", encoding="utf8") as file:
            payments = file.read()

        assert payments == f'- iban: "CZTEST"\n  value: -10\n  timestamp: {datetime.timestamp(datetime.now())}\n'
