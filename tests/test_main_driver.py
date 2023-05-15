import yaml
import os
import sys
from unittest.mock import mock_open
import base64
import jwt
import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import main_driver
from main_driver import app


def test_login_bad_request(mocker):
    mocker.patch("services.database_service.get_user", return_value={"username": "user", "password": "passwd"})
    response = app.test_client().post("/login", headers={"Authorization": "Basic "})
    assert response.status_code == 400


def test_login_invalid(mocker):
    mocker.patch("services.database_service.get_user", return_value={"username": "user", "password": "passwd"})
    response = app.test_client().post("/login", headers={"Authorization": f'Basic {(base64.b64encode(b"user:invalid")).decode("utf-8")}'})
    assert response.status_code == 401


def test_login_successful(mocker):
    mocker.patch("services.database_service.get_user", return_value={"username": "user", "password": "passwd", "email": "test@example.com"})
    mocker.patch("flask_mail.Message", autospec=True)  # Aby se neodesílal mail
    mocker.patch("flask_mail.Mail.send", autospec=True)  # Aby se neodesílal mail
    response = app.test_client().post("/login", headers={"Authorization": f'Basic {(base64.b64encode(b"user:passwd")).decode("utf-8")}'})
    assert response.status_code == 200
    assert len(main_driver.codes) == 1


def test_authorize_successful():
    username = "user"
    code = "8QPYZDH0WJKOZ8OT"
    expiration = datetime.datetime.utcnow() + datetime.timedelta(minutes=3)
    main_driver.codes[username] = (code, expiration)

    data = {"username": username, "code": code}
    response = app.test_client().post("/authorize", json=data)

    assert response.status_code == 200
    assert "token" in response.json

    token = response.json["token"]
    decoded_token = jwt.decode(token, app.config["SECRET_KEY"], algorithms=["HS256"])
    assert decoded_token["username"] == username


def test_authorize_with_incorrect_code():
    username = "user"
    code = "8QPYZDH0WJKOZ8OT"
    expiration = datetime.datetime.utcnow() + datetime.timedelta(minutes=3)
    main_driver.codes[username] = (code, expiration)

    data = {"username": username, "code": "VRUN9OLD3X9ABH75"}
    response = app.test_client().post("/authorize", json=data)

    assert response.status_code == 401


def test_authorize_with_expired_code():
    username = "user"
    code = "8QPYZDH0WJKOZ8OT"
    expiration = datetime.datetime.utcnow() - datetime.timedelta(minutes=3)
    main_driver.codes[username] = (code, expiration)

    data = {"username": username, "code": code}
    response = app.test_client().post("/authorize", json=data)

    assert response.status_code == 401
