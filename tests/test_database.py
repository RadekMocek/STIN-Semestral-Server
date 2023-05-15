import os
import sys
import pathlib
import yaml
from pyfakefs.fake_filesystem_unittest import Patcher

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import services.database_service as database_service

database_path = pathlib.Path(__file__).parent.parent / "database"
users_path = database_path / "users.yaml"
bank_accounts_path = database_path / "bank_accounts.yaml"
payments_path = database_path / "payments.yaml"
exchange_rates_path = database_path / "exchange_rates.yaml"


def test_database_test():
    users = [{"username": "user", "name": "Test User", "email": "test@example.com", "password": "passwd"}]
    with Patcher(use_cache=False) as patcher:
        patcher.fs.create_file(users_path)
        with open(users_path, "w", encoding="utf8") as file:
            yaml.dump(users, file)
        assert database_service.get_user("user") == users[0]
