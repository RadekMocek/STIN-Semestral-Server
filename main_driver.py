"""Bankovní web API."""
import requests
from flask import Flask, jsonify, request
import database_controller

#############
# Konstanty #
#############

EXCHANGE_RATE_SOURCE = "https://www.cnb.cz/cs/financni-trhy/devizovy-trh/kurzy-devizoveho-trhu/kurzy-devizoveho-trhu/denni_kurz.txt"

####################################
# Vytvoření a konfigurace aplikace #
####################################

app = Flask(__name__)

#############
# Endpointy #
#############


@app.route("/")
def get_data_from_url():
    """Testovací endpoint získá data z ČNB."""
    return requests.get(EXCHANGE_RATE_SOURCE, timeout=10).text


# Přihlášení #


@app.route("/login", methods=["POST"])
def login():
    """Přihlášení, používá Basic Auth authorization (username + password)."""
    authorization = request.authorization
    if not authorization or not authorization.username or not authorization.password:
        return jsonify({"message": "Nevyplněné údaje"}), 401
    user = database_controller.get_user(authorization.username)
    if not user or user["password"] != authorization.password:
        return jsonify({"message": "Chybné jméno nebo heslo"}), 401
    return jsonify({"message": "TODO: send 2fa email"})


#########
# Zážeh #
#########

if __name__ == "__main__":
    app.run()
