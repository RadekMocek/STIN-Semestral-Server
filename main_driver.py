"""Bankovní web API."""
import random
import string
import datetime
from decimal import Decimal
from functools import wraps
import jwt
import git
from flask import Flask, jsonify, render_template_string, request
from flask_mail import Mail, Message
from flask_cors import CORS
import services.database_service as database_service
import services.exchange_rates_service as exchange_rates_service
import services.payments_service as payments_service

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
codes = {}  # Slovník username: kód, expirace


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
    return jsonify(exchange_rates_service.get_exchange_rates()), 200


# Přihlášení #


@app.route("/login", methods=["POST"])
def login():
    """Přihlášení, používá Basic Auth authorization (username + password). Po úspěšném přihlášení odesílá 2fa kód na e-mail."""
    # Kontrola údajů
    authorization = request.authorization
    if not authorization or not authorization.username or not authorization.password:
        return jsonify({"message": "Nevyplněné údaje."}), 400
    user = database_service.get_user(authorization.username)
    if not user or user["password"] != authorization.password:
        return jsonify({"message": "Chybné jméno nebo heslo."}), 401
    # Pokud jsou údaje v pořádku, poslat 2fa kód na e-mail
    code = "".join(random.choices(string.ascii_uppercase + string.digits, k=16))
    expiration = datetime.datetime.utcnow() + datetime.timedelta(minutes=3)
    email_message = Message(subject="STIN banka ověření", recipients=[user["email"]])
    email_message.body = f"Váš kód dvoufázového ověření je:\n\n{code}\n\n"
    mail.send(email_message)
    codes[user["username"]] = (code, expiration)
    return jsonify({"message": "Na e-mail byl odeslán 2fa kód."}), 200


@app.route("/authorize", methods=["POST"])
def authorize():
    """
    Ověření 2fa kódu z e-mailu a případná generace a poskytnutí jwt tokenu.
    Přijímá data v body ve formátu json: '{"username": "<username>", "code": "<2fa kód>"}'.
    """
    # Kontrola kódu
    username = request.json.get("username")
    code = request.json.get("code")
    if username not in codes or codes[username][0] != code:
        return jsonify({"message": "Chybný kód."}), 401
    if datetime.datetime.utcnow() > codes[username][1]:
        del codes[username]
        return jsonify({"message": "Platnost kódu vypršela, přihlašte se znovu."}), 401
    # Generace tokenu
    del codes[username]
    token = jwt.encode(
        {
            "username": username,
            "exp": datetime.datetime.utcnow() + datetime.timedelta(minutes=45),
        },
        app.config["SECRET_KEY"],
        algorithm="HS256",
    )
    return jsonify({"token": token}), 200


# Výpis #


@app.route("/user_bank_accounts")
@token_required
def get_user_bank_accounts(username):
    """Vrací seznam všech účtů (majitel, měna, zůstatek) daného uživatele."""
    return jsonify(database_service.get_bank_accounts(username)), 200


# Platby #


@app.route("/payment_incoming", methods=["POST"])
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
    # Kontrola hodnot
    exchange_rates = database_service.get_exchange_rates()
    if __is_payment_arguments_valid(currency, amount, exchange_rates):
        amount = float(amount)
    else:
        return jsonify({"message": "Chybně zadaná částka."}), 422
    # Má uživatel účet v dané měně?
    user_account = database_service.get_bank_account(username, currency)
    additional_message = ""
    if not user_account:
        # Pokud ne, použít převod na CZK.
        user_account = database_service.get_bank_account(username, "CZK")
        if not user_account:
            return jsonify({"message": f"Uživatel nemá účet ani v {currency}, ani v CZK."}), 422
        amount = payments_service.currency_to_czk(amount, currency, exchange_rates)
        additional_message = " s převodem na CZK"
    user_account = user_account[0]  # ("Rozbalení" z jednopoložkového seznamu)
    # Připsat peníze na účet (+ zápis do databáze)
    payments_service.payment_incoming(user_account, amount)
    return jsonify({"message": f"Platba byla provedena{additional_message}."}), 200


@app.route("/payment_outgoing", methods=["POST"])
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
    return __payment_outgoing(username, currency, amount)


def __payment_outgoing(username, currency, amount):
    # Kontrola hodnot
    exchange_rates = database_service.get_exchange_rates()
    if __is_payment_arguments_valid(currency, amount, exchange_rates):
        amount = float(amount)
    else:
        return jsonify({"message": "Chybně zadaná částka."}), 422
    # Může uživatel zaplatit v currency?
    user_account = database_service.get_bank_account(username, currency)
    if __is_account_ready_for_outgoing_payment(user_account, amount):
        payments_service.payment_outgoing(user_account[0], amount)
        return jsonify({"message": "Platba byla provedena."}), 200
    # Může využít kontokorentu?
    if __is_account_ready_for_outgoing_payment_with_overdraft(user_account, amount):
        payments_service.payment_outgoing(user_account[0], amount)
        payments_service.overdraft_interest(user_account[0], 0.1)
        return jsonify({"message": "Platba byla provedena s úrokem za kontokorent."}), 200
    # Může uživatel zaplatit v CZK?
    user_account = database_service.get_bank_account(username, "CZK")
    amount = payments_service.currency_to_czk(amount, currency, exchange_rates)
    if __is_account_ready_for_outgoing_payment(user_account, amount):
        payments_service.payment_outgoing(user_account[0], amount)
        return jsonify({"message": "Platba byla provedena s převodem na CZK."}), 200
    # Může využít CZK kontokorentu?
    if __is_account_ready_for_outgoing_payment_with_overdraft(user_account, amount):
        payments_service.payment_outgoing(user_account[0], amount)
        payments_service.overdraft_interest(user_account[0], 0.1)
        return jsonify({"message": "Platba byla provedena s převodem na CZK a úrokem za kontokorent."}), 200
    return jsonify({"message": "Platba nemohla být provedena."}), 422


def __is_account_ready_for_outgoing_payment(bank_account, amount):
    if len(bank_account) == 0:
        return False
    bank_account = bank_account[0]
    if bank_account["balance"] < amount:
        return False
    return True


def __is_account_ready_for_outgoing_payment_with_overdraft(bank_account, amount):
    if len(bank_account) == 0:
        return False
    bank_account = bank_account[0]
    if amount >= float(Decimal(bank_account["balance"] + bank_account["balance"] * 0.1).quantize(Decimal("1e-6"))):
        return False
    return True


def __is_payment_arguments_valid(currency, amount, exchange_rates):
    # Je částka číslo?
    try:
        float(amount)
    except (ValueError, TypeError):
        return False
    amount = float(amount)
    # Je částka kladná?
    if amount <= 0:
        return False
    # Existuje měna?
    if currency not in exchange_rates or currency == "_Date":
        return False
    # Jinak v pořádku
    return True


# Výpis #


@app.route("/payment_history")
@token_required
def payment_history(username):
    """Vypíše historii pohybů na účtu s konkrétním 'iban', pokud se jedná o účet patřící uživateli s 'username'."""
    # Získat si hodnoty z request body
    iban = request.args.get("iban")
    # Patří účet uživateli?
    user_accounts = database_service.get_bank_accounts(username)
    for user_account in user_accounts:
        if user_account["iban"] == iban:
            return jsonify(database_service.get_payment_history(iban)), 200
    return jsonify({"message": "Tento účet vám nepatří."}), 401


# Index #


@app.route("/")
def index():
    """Informuje uživatele o adrese klientské aplikace."""
    return (
        render_template_string(
            """<p>Aplikace STIN Bank je dostupná na adrese
            <a href="https://radekmocek.github.io/STIN-Semestral-Client/">https://radekmocek.github.io/STIN-Semestral-Client/</a></p>"""
        ),
        200,
    )


# Continuous integration #


@app.route("/deploy", methods=["POST"])
def deploy():
    """Zajišťuje automatické nasazení na PythonAnywhere při pushi do větve main."""
    repo = git.Repo("./STIN-Semestral-Server")
    origin = repo.remotes.origin
    repo.create_head("main", origin.refs.main).set_tracking_branch(origin.refs.main).checkout()
    origin.pull()
    return "", 200


#########
# Zážeh #
#########

if __name__ == "__main__":
    app.run()
