import os
import sys
import pathlib
import yaml
from pyfakefs.fake_filesystem_unittest import Patcher

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import services.database_service as database_service

database_path = pathlib.Path(__file__).parent.parent / "database"
USERS_PATH = database_path / "users.yaml"
BANK_ACCOUNTS_PATH = database_path / "bank_accounts.yaml"
PAYMENTS_PATH = database_path / "payments.yaml"
EXCHANGE_RATES_PATH = database_path / "exchange_rates.yaml"


def test_get_user_existant():
    users = [{"username": "user", "name": "Test User", "email": "test@example.com", "password": "passwd"}]
    with Patcher(use_cache=False) as patcher:
        patcher.fs.create_file(USERS_PATH)
        with open(USERS_PATH, "w", encoding="utf8") as file:
            yaml.dump(users, file)
        assert database_service.get_user("user") == users[0]


def test_get_user_none():
    users = [{"username": "user", "name": "Test User", "email": "test@example.com", "password": "passwd"}]
    with Patcher(use_cache=False) as patcher:
        patcher.fs.create_file(USERS_PATH)
        with open(USERS_PATH, "w", encoding="utf8") as file:
            yaml.dump(users, file)
        assert database_service.get_user("non_user") == None


def test_get_bank_accounts():
    bank_accounts = [
        {"balance": 10, "currency": "CZK", "iban": "CZTEST1", "owner": "user1"},
        {"balance": 20, "currency": "CZK", "iban": "CZTEST2", "owner": "user2"},
        {"balance": 30, "currency": "AUD", "iban": "CZTEST3", "owner": "user1"},
    ]
    user_accounts = [
        {"balance": 10, "currency": "CZK", "iban": "CZTEST1", "owner": "user1"},
        {"balance": 30, "currency": "AUD", "iban": "CZTEST3", "owner": "user1"},
    ]
    with Patcher(use_cache=False) as patcher:
        patcher.fs.create_file(BANK_ACCOUNTS_PATH)
        with open(BANK_ACCOUNTS_PATH, "w", encoding="utf8") as file:
            yaml.dump(bank_accounts, file)
        assert database_service.get_bank_accounts("user1") == user_accounts
        assert database_service.get_bank_accounts("user2") == [bank_accounts[1]]


def test_get_bank_account():
    bank_accounts = [
        {"balance": 10, "currency": "CZK", "iban": "CZTEST1", "owner": "user1"},
        {"balance": 20, "currency": "AUD", "iban": "CZTEST2", "owner": "user2"},
        {"balance": 30, "currency": "AUD", "iban": "CZTEST3", "owner": "user1"},
    ]
    with Patcher(use_cache=False) as patcher:
        patcher.fs.create_file(BANK_ACCOUNTS_PATH)
        with open(BANK_ACCOUNTS_PATH, "w", encoding="utf8") as file:
            yaml.dump(bank_accounts, file)
        assert database_service.get_bank_account("user1", "AUD") == [bank_accounts[2]]


def test_get_payment_history():
    payments = [
        {"iban": "CZTEST1", "value": 10, "timestamp": 10},
        {"iban": "CZTEST2", "value": 20, "timestamp": 20},
        {"iban": "CZTEST1", "value": 30, "timestamp": 30},
    ]
    iban_payments = [
        {"iban": "CZTEST1", "value": 10, "timestamp": 10},
        {"iban": "CZTEST1", "value": 30, "timestamp": 30},
    ]
    with Patcher(use_cache=False) as patcher:
        patcher.fs.create_file(PAYMENTS_PATH)
        with open(PAYMENTS_PATH, "w", encoding="utf8") as file:
            yaml.dump(payments, file)
        assert database_service.get_payment_history("CZTEST1") == iban_payments
        assert database_service.get_payment_history("CZTEST2") == [payments[1]]
