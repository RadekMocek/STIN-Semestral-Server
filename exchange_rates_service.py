"""Poskytuje aktuální měnové kurzy."""
from datetime import datetime
from decimal import Decimal
import pytz
import requests
import database_controller

EXCHANGE_RATES_SOURCE = "https://www.cnb.cz/cs/financni-trhy/devizovy-trh/kurzy-devizoveho-trhu/kurzy-devizoveho-trhu/denni_kurz.txt"
EXCHANGE_RATES_REFRESH_HOUR = 14
EXCHANGE_RATES_REFRESH_MINUTE = 30
EXCHANGE_RATES_REFRESH_WEEKDAYS = [0, 1, 2, 3, 4]
TIMEZONE = pytz.timezone("Europe/Prague")


def get_exchange_rates():
    """Vrací slovník měnových kurzů buď z cache nebo volá __get_exchange_rates_from_cnb."""
    # Načtení nacachovaných kurzů
    rates_dictionary = database_controller.get_exchange_rates()
    cache_date = rates_dictionary["_Date"]
    # Aktuální datetime
    current_datetime = datetime.now(TIMEZONE)
    # Jsou nacachované kurzy staré?
    if __should_get_exchange_rates_from_cnb(current_datetime, cache_date):
        # Pokud ano, zkusíme načíst a vrátit nové kurzy z ČNB
        new_rates = __get_exchange_rates_from_cnb()
        if new_rates:
            return new_rates
    # Jinak vracíme staré kurzy
    return rates_dictionary


def __should_get_exchange_rates_from_cnb(current_datetime, cache_date):
    """Měli bychom se pokusit získat nové kurzy z ČNB na základě akutálního a nacachovaného datumu?"""
    if current_datetime.strftime("%d.%m.%Y") == cache_date:
        # Máme kurzy z dneška
        return False
    # Nemáme kurzy z dneška
    cache_datetime = datetime.strptime(cache_date, "%d.%m.%Y").replace(tzinfo=TIMEZONE)
    if current_datetime.weekday() not in EXCHANGE_RATES_REFRESH_WEEKDAYS:
        # Je víkend
        if cache_datetime.weekday() == EXCHANGE_RATES_REFRESH_WEEKDAYS[-1] and (current_datetime - cache_datetime).days <= 2:
            # a máme kurzy z posledního pátku
            return False
        # Je víkend ale nemáme kurzy z posledního pátku
        return True
    # Není víkend
    if (
        current_datetime.hour == EXCHANGE_RATES_REFRESH_HOUR and current_datetime.minute > EXCHANGE_RATES_REFRESH_MINUTE
    ) or current_datetime.hour > EXCHANGE_RATES_REFRESH_HOUR:
        # Je po 14:30
        return True
    # Není po 14:30
    return False


def __get_exchange_rates_from_cnb():
    """Pokusí se získat měnové kurzy z ČNB a uložit je do cache."""
    try:
        rates_text = requests.get(EXCHANGE_RATES_SOURCE, timeout=10).text
    except requests.exceptions.RequestException:
        return None
    rates = rates_text.split("\n")
    rates_dictionary = {}
    rates_dictionary["CZK"] = 1
    # Předpokládáme, že první řádek začíná datem ve formátu 'dd.mm.yyyy'
    rates_dictionary["_Date"] = rates[0][:10]
    # Vynechat hlavičku a poslední prázdný řádek (předpokládáme, že jednotlivé měny jsou od třetího řádku do posledního řádku)
    for rate in rates[2:-1]:
        # Předpokládáme formát 'xxx|yyy|množství|kód|kurz'
        rate_sections = rate.split("|")
        # Použití decimal, abychom se vyhli float nepřesnostem
        rates_dictionary[rate_sections[3]] = float(Decimal(float(rate_sections[4].replace(",", ".")) / int(rate_sections[2])).quantize(Decimal("1e-6")))
    # Nacachovat nové kurzy a vrátit je
    database_controller.set_exchange_rates(rates_dictionary)
    return rates_dictionary
