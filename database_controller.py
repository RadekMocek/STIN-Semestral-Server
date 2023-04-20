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
