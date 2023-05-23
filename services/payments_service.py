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
    payment_incoming(user_account, -amount)


def overdraft_interest(user_account, amount):
    """Jednorázový úrok 'amount'."""
    iban = user_account["iban"]
    account = database_service.get_bank_account_by_iban(iban)
    if len(account) == 0:
        return
    account = account[0]
    interest = -float(Decimal(account["balance"] * amount).quantize(Decimal("1e-6")))
    payment_outgoing(account, interest)
