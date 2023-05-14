"""Spravuje yaml databázi."""
import pathlib
import yaml

database_path = pathlib.Path(__file__).parent.parent / "database"
users_path = database_path / "users.yaml"
bank_accounts_path = database_path / "bank_accounts.yaml"
payments_path = database_path / "payments.yaml"
exchange_rates_path = database_path / "exchange_rates.yaml"


def get_user(username):
    """Vrátí uživatele s požadovaným username, pokud existuje."""
    with open(users_path, "r", encoding="utf8") as file:
        users = yaml.safe_load(file)
    for user in users:
        if user["username"] == username:
            return user
    return None


def get_bank_accounts(username):
    """Vrátí seznam všech účtů vlastněných uživatelem s username."""
    with open(bank_accounts_path, "r", encoding="utf8") as file:
        bank_accounts = yaml.safe_load(file)
    return list(filter(lambda bank_account: bank_account["owner"] == username, bank_accounts))


def get_bank_account(username, currency):
    """Vrátí seznam účtů patřících uživateli s 'username' ve měně 'currency'. (Této podmínce by měl vyhovovat jen jeden)."""
    with open(bank_accounts_path, "r", encoding="utf8") as file:
        bank_accounts = yaml.safe_load(file)
    return list(filter(lambda bank_account: bank_account["owner"] == username and bank_account["currency"] == currency, bank_accounts))


def set_bank_account_balance(iban, balance):
    """Nastaví u účtu s konkrétním 'iban' nový zůstatek 'balance'."""
    if not bank_accounts_path.exists():
        return
    with open(bank_accounts_path, "r", encoding="utf8") as file:
        bank_accounts = yaml.safe_load(file)
    for bank_account in bank_accounts:
        if bank_account["iban"] == iban:
            bank_account["balance"] = balance
            break
    with open(bank_accounts_path, "w", encoding="utf8") as file:
        yaml.dump(bank_accounts, file)


def log_payment(iban, amount, timestamp):
    """Zaloguje platbu."""
    print("\ndatabase service database path:", database_path)
    if not payments_path.exists():
        return
    with open(payments_path, "a", encoding="utf8") as file:
        file.write(f'- iban: "{iban}"\n  value: {amount}\n  timestamp: {timestamp}\n')


def get_payment_history(iban):
    """Vrátí historii plateb pro účet s daným 'iban'."""
    with open(payments_path, "r", encoding="utf8") as file:
        payments = yaml.safe_load(file)
    return list(filter(lambda payment: payment["iban"] == iban, payments))


def get_exchange_rates():
    """Vrátí kurzy uložené v souboru (cache)."""
    with open(exchange_rates_path, "r", encoding="utf8") as file:
        rates_dictionary = yaml.safe_load(file)
    return rates_dictionary


def set_exchange_rates(rates_dictionary):
    """Uloží nové kurzy do souboru."""
    with open(exchange_rates_path, "w", encoding="utf8") as file:
        yaml.dump(rates_dictionary, file)
