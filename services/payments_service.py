"""Služba pro provádění plateb."""
from decimal import Decimal
from datetime import datetime
from services import database_service


def currency_to_czk(amount, currency, exchange_rates):
    """Převod částky 'amount' z 'currency' na CZK podle 'exchange_rates'."""
    return float(Decimal(amount * exchange_rates[currency]).quantize(Decimal("1e-6")))


def payment_incoming(user_account, amount):
    """Připíše na 'user_account' částku 'amount' a uloží do databáze."""
    iban = user_account["iban"]
    balance = float(Decimal(user_account["balance"] + amount).quantize(Decimal("1e-6")))
    timestamp = datetime.timestamp(datetime.now())
    database_service.set_bank_account_balance(iban, balance)
    database_service.log_payment(iban, amount, timestamp)


def payment_outgoing(user_account, amount):
    """Odečte z 'user_account' částku 'amount' a uloží do databáze."""
    print("Before payment outgoing: ", database_service.get_bank_accounts("test"))
    payment_incoming(user_account, -amount)
    print("After payment outgoing: ", database_service.get_bank_accounts("test"))