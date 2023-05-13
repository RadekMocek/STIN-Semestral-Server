import os
import sys
from unittest.mock import mock_open

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main_driver import app


def test_if_tests_are_working(monkeypatch):
    # Mock exchange rates
    mock_file_content = """
    AUD: 14.481
    CZK: 1
    _Date: 12.05.2023
    """
    monkeypatch.setattr('builtins.open', mock_open(read_data=mock_file_content))

    response = app.test_client().get("/exchange_rates")
    assert response.status_code == 200
