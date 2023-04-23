"""Bankovní web API."""
import random
import string
import datetime
from functools import wraps
import jwt
from flask import Flask, jsonify, request
from flask_mail import Mail, Message
from flask_cors import CORS
import database_controller
import exchange_rates_service
import payments_service

####################################
# Vytvoření a konfigurace aplikace #
####################################

app = Flask(__name__)
CORS(app)
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
        except jwt.exceptions.InvalidTokenError:
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
    Přijímá data v body ve formátu json: '{"email": "<e-mail>", "code": "<2fa kód>"}'.
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


@app.route("/user_bank_accounts")
@token_required
def get_user_bank_accounts(username):
    """Vrací seznam všech účtů (majitel, měna, zůstatek) daného uživatele."""
    return jsonify(database_controller.get_bank_accounts(username))


# Platby #


@app.route("/payment_incoming")
@token_required
def payment_incoming(username):
    """
    Připíše uživateli na účet ve měně 'currency' částku 'amount' a zaloguje.
    Pokud uživatel nemá účet v dané měně, je platba převedena na CZK.
    Přijímá data v body ve formátu json: '{"currency": "<měna>", "amount": "<částka>"}'.
    """
    # Získat si hodnoty z request body
    currency = request.json.get("currency")
    amount = request.json.get("amount")
    # Je částka číslo?
    try:
        float(amount)
    except ValueError:
        return jsonify({"message": "Chybně zadaná částka."}), 401
    amount = float(amount)
    # Je částka kladná?
    if amount <= 0:
        return jsonify({"message": "Příchozí platba musí být kladná částka."}), 401
    exchange_rates = database_controller.get_exchange_rates()
    # Existuje měna?
    if currency not in exchange_rates or currency == "_Date":
        return jsonify({"message": "Zadaná měna neexistuje."}), 401
    # Má uživatel účet v dané měně?
    user_account = database_controller.get_bank_account(username, currency)
    additional_message = ""
    if not user_account:
        # Pokud ne, použít převod na CZK.
        user_account = database_controller.get_bank_account(username, "CZK")
        if not user_account:
            return jsonify({"message": f"Uživatel nemá účet ani v {currency}, ani v CZK."}), 401
        amount = payments_service.currency_to_czk(amount, currency, exchange_rates)
        additional_message = " s převodem na CZK"
    user_account = user_account[0]  # ("Rozbalení" z jednopoložkového seznamu)
    # Připsat peníze na účet (+ zápis do databáze)
    payments_service.payment_incoming(user_account, amount)
    return jsonify({"message": f"Platba byla provedena{additional_message}."}), 200


@app.route("/payment_outgoing")
@token_required
def payment_outgoing(username):
    """
    Pokud má uživatel 'username' na účtě s měnou 'currency' dostatek prostředků 'amount',
    je provedena odchozí platba – částka se odečte z účtu a platba je zalogována.
    Pokud nemá účet v dané měně nebo nemá dostatek prostředků, převedene se 'amount' na CZK a
    a platba se stejným způsobem pokusí provést v CZK.
    Přijímá data v body ve formátu json: '{"currency": "<měna>", "amount": "<částka>"}'.
    """
    # Získat si hodnoty z request body
    currency = request.json.get("currency")
    amount = request.json.get("amount")
    # Je částka číslo?
    try:
        float(amount)
    except ValueError:
        return jsonify({"message": "Chybně zadaná částka."}), 401
    amount = float(amount)
    # Je částka kladná?
    if amount <= 0:
        return jsonify({"message": "Odchozí platba musí být kladná částka."}), 401
    exchange_rates = database_controller.get_exchange_rates()
    # Existuje měna?
    if currency not in exchange_rates or currency == "_Date":
        return jsonify({"message": "Zadaná měna neexistuje."}), 401
    # Může uživatel zaplatit v currency?
    user_account = database_controller.get_bank_account(username, currency)
    if __is_account_ready_for_outgoing_payment(user_account, amount):
        payments_service.payment_outgoing(user_account[0], amount)
        return jsonify({"message": "Platba byla provedena."}), 200
    user_account = database_controller.get_bank_account(username, "CZK")
    amount = payments_service.currency_to_czk(amount, currency, exchange_rates)
    if __is_account_ready_for_outgoing_payment(user_account, amount):
        payments_service.payment_outgoing(user_account[0], amount)
        return jsonify({"message": "Platba byla provedena s převodem na CZK."}), 200
    return jsonify({"message": "Platba nemohla být provedena."}), 401


def __is_account_ready_for_outgoing_payment(bank_account, amount):
    if len(bank_account) == 0:
        return False
    bank_account = bank_account[0]
    if bank_account["balance"] < amount:
        return False
    return True


#########
# Zážeh #
#########

if __name__ == "__main__":
    app.run()
