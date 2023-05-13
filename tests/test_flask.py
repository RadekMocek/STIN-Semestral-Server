import pytest
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main_driver import app


def test_if_tests_are_working():
    response = app.test_client().get("/exchange_rates")
    assert response.status_code == 200
