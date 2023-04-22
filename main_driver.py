"""Bankovní web API."""
import random
import string
import datetime
from functools import wraps
import jwt
from flask import Flask, jsonify, request
from flask_mail import Mail, Message
import database_controller
import exchange_rates_service


####################################
# Vytvoření a konfigurace aplikace #
####################################

app = Flask(__name__)
app.config["SECRET_KEY"] = "Střeštěná ách mrkev"

# E-mail #

app.config["MAIL_SERVER"] = "smtp.gmail.com"
app.config["MAIL_PORT"] = 587
app.config["MAIL_USE_TLS"] = True
app.config["MAIL_DEFAULT_SENDER"] = "radek.mocek.flask@gmail.com"
app.config["MAIL_USERNAME"] = "radek.mocek.flask@gmail.com"
app.config["MAIL_PASSWORD"] = "pieytppmviphtenl"
mail = Mail(app)
codes = {}  # Slovník e-mail: kód, username, expirace


##############
# Dekorátory #
##############


def token_required(func):
    """
    Endpoint s tímto dekorátorem je spuštěn pouze, pokud dostane v request authorization
    headeru platný token ('Bearer <token>'). Dekorované metodě předá username žadatele.
    """

    @wraps(func)
    def decorated(*args, **kwargs):
        token = None
        if "Authorization" in request.headers:
            auth_header = request.headers["Authorization"]
            token = auth_header.split(" ")[1]
        if not token:
            return jsonify({"message": "Chybějící token."}), 401
        try:
            data = jwt.decode(token, app.config["SECRET_KEY"], algorithms="HS256")
        except:  # pylint: disable=W0702
            return jsonify({"message": "Neplatný token."}), 401
        return func(data["username"], *args, **kwargs)

    return decorated


#############
# Endpointy #
#############

# Kurzy #


@app.route("/exchange_rates")
def get_exchange_rates():
    """Vrátí aktuální kurzy."""
    return jsonify(exchange_rates_service.get_exchange_rates())


# Přihlášení #


@app.route("/login", methods=["POST"])
def login():
    """Přihlášení, používá Basic Auth authorization (username + password). Po úspěšném přihlášení odesílá 2fa kód na e-mail."""
    # Kontrola údajů
    authorization = request.authorization
    if not authorization or not authorization.username or not authorization.password:
        return jsonify({"message": "Nevyplněné údaje."}), 401
    user = database_controller.get_user(authorization.username)
    if not user or user["password"] != authorization.password:
        return jsonify({"message": "Chybné jméno nebo heslo."}), 401
    # Pokud jsou údaje v pořádku, poslat 2fa kód na e-mail
    code = "".join(random.choices(string.ascii_uppercase + string.digits, k=16))
    expiration = datetime.datetime.utcnow() + datetime.timedelta(minutes=3)
    email_message = Message(subject="STIN banka ověření", recipients=[user["email"]])
    email_message.body = f"Váš kód dvoufázového ověření je:\n\n{code}\n\n"
    mail.send(email_message)
    codes[user["email"]] = (code, user["username"], expiration)
    return jsonify({"message": "Na e-mail byl odeslán 2fa kód."}), 200


@app.route("/authorize", methods=["POST"])
def authorize():
    """
    Ověření 2fa kódu z e-mailu a případná generace a poskytnutí jwt tokenu.
    Přijímá data v body v json ve formátu '{"email": "<e-mail>", "code": "<2fa kód>"}'
    """
    # Kontrola kódu
    email = request.json.get("email")
    code = request.json.get("code")
    if email not in codes or codes[email][0] != code:
        return jsonify({"message": "Chybný kód."}), 401
    if datetime.datetime.utcnow() > codes[email][2]:
        del codes[email]
        return jsonify({"message": "Platnost kódu vypršela, přihlašte se znovu."}), 401
    # Generace tokenu
    username = codes[email][1]
    del codes[email]
    token = jwt.encode(
        {
            "username": username,
            "exp": datetime.datetime.utcnow() + datetime.timedelta(minutes=30),
        },
        app.config["SECRET_KEY"],
        algorithm="HS256",
    )
    return jsonify({"token": token})


# Výpis #


@app.route("/accounts")
@token_required
def get_user_bank_accounts(username):
    """Vrací seznam všech účtů (majitel, měna, zůstatek) daného uživatele."""
    return jsonify(database_controller.get_bank_accounts(username))


#########
# Zážeh #
#########

if __name__ == "__main__":
    app.run()
