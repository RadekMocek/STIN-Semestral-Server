"""Spravuje yaml databázi."""
import yaml


def get_user(username):
    """Vrátí uživatele s požadovaným username, pokud existuje."""
    with open("database/users.yaml", "r", encoding="utf8") as file:
        users = yaml.safe_load(file)
    for user in users:
        if user["username"] == username:
            return user
    return None


def get_bank_accounts(username):
    """Vrátí seznam všech účtů vlastněných uživatelem s username."""
    with open("database/bank_accounts.yaml", "r", encoding="utf8") as file:
        bank_accounts = yaml.safe_load(file)
    return list(filter(lambda bank_account: bank_account["owner"] == username, bank_accounts))


def get_bank_account(username, currency):
    """Vrátí seznam účtů patřících uživateli s 'username' ve měně 'currency'. (Této podmínce by měl vyhovovat jen jeden)."""
    with open("database/bank_accounts.yaml", "r", encoding="utf8") as file:
        bank_accounts = yaml.safe_load(file)
    return list(filter(lambda bank_account: bank_account["owner"] == username and bank_account["currency"] == currency, bank_accounts))


def set_bank_account_balance(iban, balance):
    """Nastaví u účtu s konkrétním 'iban' nový zůstatek 'balance'."""
    with open("database/bank_accounts.yaml", "r", encoding="utf8") as file:
        bank_accounts = yaml.safe_load(file)
    for bank_account in bank_accounts:
        if bank_account["iban"] == iban:
            bank_account["balance"] = balance
            break
    with open("database/bank_accounts.yaml", "w", encoding="utf8") as file:
        yaml.dump(bank_accounts, file)


def log_payment(iban, amount, timestamp):
    """Zaloguje platbu."""
    with open("database/payments.yaml", "a", encoding="utf8") as file:
        file.write(f'- iban: "{iban}"\n  value: {amount}\n  timestamp: {timestamp}\n')


def get_exchange_rates():
    """Vrátí kurzy uložené v souboru (cache)."""
    with open("database/exchange_rates.yaml", "r", encoding="utf8") as file:
        rates_dictionary = yaml.safe_load(file)
    return rates_dictionary


def set_exchange_rates(rates_dictionary):
    """Uloží nové kurzy do souboru."""
    with open("database/exchange_rates.yaml", "w", encoding="utf8") as file:
        yaml.dump(rates_dictionary, file)
