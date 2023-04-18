"""Bankovní web API"""
import requests
from flask import Flask

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
    """Testovací endpoint získá data z ČNB"""
    return requests.get(EXCHANGE_RATE_SOURCE, timeout=10).text


#########
# Zážeh #
#########

if __name__ == "__main__":
    app.run()
