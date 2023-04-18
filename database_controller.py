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
