#!/usr/bin/env python3
import os
import logging
from typing import Any
from random import randint

from PIL import Image, ImageDraw, ImageFont
from fastapi import status

from src.stage2 import Database, CountryModel


def get_exchange_rate(code: str) -> float:
    exchange = Database.get_exchange_rate()
    if exchange:
        rates: dict[str, Any] = exchange.get("rates")  # type: ignore
        if rates.get(code.upper()):
            return float(rates.get(code.upper()))  # type: ignore
        return 0.0
    raise ValueError(f"{code} not found")


def calculate_estimated_gdp(population: int, exchange_rate: float) -> float:
    return population * randint(1000, 2000) / exchange_rate


async def upload_countries():
    logging.info("Uploading countries on application start")
    all_countries = Database.get_all_countries()
    if len(all_countries) > 0:
        print(all_countries)
        return
    countries = list(
        map(
            lambda x: create_country_model(x),
            Database.get_external_countries(),
        )
    )
    countries = list(filter(lambda x: x != None, countries))
    Database.add_country(countries)
    print("Completed setting up server")
    return


def remove_countries():
    countries = Database.get_all_countries()
    Database.bulk_remove_country(countries)
    print("Country removal for shutdown complete")


def generate_image() -> None:
    img_width, img_height, background_color, text_color, accent_color = (
        600,
        400,
        (254, 247, 250),
        (30, 30, 30),
        (0, 102, 255),
    )
    image_data = Database.get_image_data()
    title_font = text_font = small_font = ImageFont.load_default()

    timestamp: str = str(image_data.get("timestamp"))
    top_countries: list[CountryModel] = image_data.get("top_countries")  # type: ignore
    total_countries: int = image_data.get("total_countries") if image_data.get("total_countries") else 0  # type: ignore

    image = Image.new("RGB", (img_width, img_height), background_color)
    draw = ImageDraw.Draw(image)

    draw.text((20, 20), "🌍 Country Summary:", fill=accent_color, font=title_font)
    draw.text(
        (20, 40), f"Total Countries: {total_countries}", fill=text_color, font=text_font
    )

    y_position = 120
    draw.text(
        (20, y_position), "💰 Top 5 by Estimated GDP", fill=text_color, font=text_font
    )
    y_position += 30

    for i, country in enumerate(top_countries, 1):
        draw.text(
            (40, y_position),
            f"{i}. {country.name} - {country.estimated_gdp:,.2f}",
            fill=(60, 60, 60),
            font=small_font,
        )
        y_position += 25

    draw.text(
        (20, img_height - 40),
        f"🕒 Last Refreshed: {timestamp}",
        fill=(100, 100, 100),
        font=small_font,
    )

    cache_dir = os.path.join(os.curdir, "cache")
    os.makedirs(cache_dir, exist_ok=True)
    image_path = os.path.join(cache_dir, "summary.png")
    image.save(image_path)


def create_country_model(data: dict[str, Any]) -> CountryModel:

    if not data.get("population"):
        # raise ValueError("Population not found")
        return None

    population = data["population"]

    curr = data.get("currencies")

    logging.info(f"Creating country {data['name']}")

    if curr and len(curr) <= 0:
        new_country = CountryModel(
            name=data["name"],
            capital=data.get("capital"),
            region=data.get("region"),
            population=population,
            currency_code=None,
            exchange_rate=None,
            estimated_gdp=0,
            flag_url=data.get("flag"),
        )
        return new_country

    if curr == None:
        new_country = CountryModel(
            name=data["name"],
            capital=data.get("capital"),
            region=data.get("region"),
            population=population,
            currency_code=None,
            exchange_rate=None,
            estimated_gdp=None,
            flag_url=data.get("flag"),
        )
        return new_country

    currency = data["currencies"][0].get("code")
    exchange_rate = get_exchange_rate(currency)
    gdp = calculate_estimated_gdp(population, exchange_rate)

    if exchange_rate == 0:

        new_country = CountryModel(
            name=data["name"],
            capital=data.get("capital"),
            region=data.get("region"),
            population=population,
            currency_code=currency,
            exchange_rate=0,
            estimated_gdp=0,
            flag_url=data.get("flag"),
        )
        return new_country

    new_country = CountryModel(
        name=data["name"],
        capital=data.get("capital"),
        region=data.get("region"),
        population=population,
        currency_code=currency,
        exchange_rate=exchange_rate,
        estimated_gdp=gdp,
        flag_url=data.get("flag"),
    )
    return new_country


def clean_json(model: CountryModel) -> dict[str, Any]:
    return {
        "id": int(model.id),
        "name": model.name,
        "capital": model.capital,
        "region": model.region,
        "population": int(model.population),
        "currency_code": model.currency_code,
        "exchange_rate": round(float(model.exchange_rate), 2),  # type: ignore
        "estimated_gdp": round(float(model.estimated_gdp), 2),  # type: ignore
        "flag_url": model.flag_url,
        "last_refreshed_at": str(model.last_refreshed_at),
    }


class Stage2Exception(Exception):
    def __init__(self, detail: str, status_code: int = status.HTTP_404_NOT_FOUND):
        self.name = "Stage 2 Exception"
        self.detail = detail
        self.status_code = status_code
