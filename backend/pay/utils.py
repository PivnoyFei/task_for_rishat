import os
from decimal import Decimal
from functools import lru_cache

import requests
from dotenv import load_dotenv
from payment.settings import URL

load_dotenv()

TypeObject = tuple[Decimal | None, Decimal | None]


@lru_cache(maxsize=10)
def parser_price_now() -> Decimal:
    """Парсит с binance курс доллар рубль."""
    price_now = Decimal('100')
    response = requests.get(f"{URL}USDTRUB")
    if response.status_code == 200:
        price_now = float(response.json()['price'])
        price_now = Decimal(f'{price_now:.2f}')
    return price_now


def translate_price(rub: Decimal, usd: Decimal, currency: str | None = None) -> TypeObject:
    """Считает общую стоймость товаров в каждой валюте."""
    result_rub, result_usd, price_now = None, None, parser_price_now()

    if not currency or currency == "rub":
        result_rub = Decimal(f'{rub + usd * price_now:.2f}')
    if not currency or currency == "usd":
        result_usd = Decimal(f'{usd + rub / price_now:.2f}')
    return result_rub, result_usd


def local_env() -> tuple[str | None, str | None]:
    """Локальные переменные во избежание продлям при запуске без контейнера."""
    load_dotenv('../infra/.env')
    STRIPE_PUBLIC_KEY = os.getenv('STRIPE_PUBLIC_KEY', default=None)
    STRIPE_SECRET_KEY = os.getenv('STRIPE_SECRET_KEY', default=None)
    return STRIPE_PUBLIC_KEY, STRIPE_SECRET_KEY
