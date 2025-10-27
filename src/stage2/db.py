#!/usr/bin/env python3
from typing import Any
from datetime import datetime, timezone

import requests
from sqlmodel import Session, select, col, func
from sqlmodel.ext.asyncio.session import AsyncSession

from src.stage2 import CountryModel


class Database:

    @staticmethod
    def get_all_countries() -> list[CountryModel]:
        from src import engine

        with Session(engine) as session:
            statement = select(CountryModel)
            country = session.exec(statement).all()
            return list(country)
        return []

    @staticmethod
    def get_external_countries() -> list[dict[str, Any]]:
        with requests.get(
            "https://restcountries.com/v2/all?fields=name,capital,region,population,flag,currencies"
        ) as req:
            return req.json()
        return []

    @staticmethod
    def get_exchange_rate() -> dict[str, dict[str, Any] | str | int | float]:
        with requests.get(f"https://open.er-api.com/v6/latest/USD") as req:
            return req.json()
        return []

    @staticmethod
    def add_country(countries: list[CountryModel]) -> bool:
        """Add one or more CountryModel records to the database."""
        from src import engine

        try:
            with Session(engine) as session:
                session.add_all(countries)
                session.commit()
            return True
        except Exception as e:
            # Optional: log error instead of print for production use
            print(f"❌ Failed to add countries: {e}")
            return False

    @staticmethod
    def bulk_remove_country(country: list[CountryModel]) -> bool:
        from src import engine

        with Session(engine) as session:
            [session.delete(i) for i in country]
            session.commit()
            session.refresh(country)
            return True
        return False

    @staticmethod
    def get_country_with_name(name: str) -> CountryModel | None:
        from src import engine

        with Session(engine) as session:
            statement = select(CountryModel).where(CountryModel.name == name)
            country = session.exec(statement).first()
            return country

    @staticmethod
    def delete_country_with_name(name: str) -> bool:
        from src import engine

        with Session(engine) as session:
            statement = select(CountryModel).where(CountryModel.name == name)
            country = session.exec(statement).first()
            if country:
                session.delete(country)
                session.commit()
            return True
        return False

    @staticmethod
    def filter_countries(query: dict[str, Any]) -> list[CountryModel]:
        from src import engine

        with Session(engine) as session:
            statement = select(CountryModel)
            for key, value in query.items():
                if key == "name":
                    statement = statement.where(CountryModel.name == value.captialize())
                if key == "capital":
                    statement = statement.where(
                        CountryModel.capital == value.capitalize()
                    )
                if key == "region":
                    statement = statement.where(
                        CountryModel.region == value.capitalize()
                    )
                if key == "population":
                    statement = statement.where(CountryModel.population == int(value))
                if key == "currency_code":
                    statement = statement.where(CountryModel.currency_code == value)
                if key == "sort":
                    all_vals = value.split("_")
                    if len(all_vals) == 2:
                        if not hasattr(CountryModel, all_vals[0]):
                            continue
                        column_attr = getattr(CountryModel, all_vals[0].lower())
                        colu = (
                            col(column_attr).desc()
                            if all_vals[-1].lower() == "desc"
                            else col(column_attr).asc()
                        )
                        statement = statement.order_by(colu)
                    elif len(all_vals) > 2:
                        *first, second = all_vals
                        first = "_".join(first)
                        if not hasattr(CountryModel, first):
                            continue
                        column_attr = getattr(CountryModel, first)
                        colu = (
                            col(column_attr).desc()
                            if all_vals[-1].lower() == "desc"
                            else col(column_attr).asc()
                        )
                        statement = statement.order_by(colu)

                    else:
                        if not hasattr(CountryModel, all_vals[0]):
                            continue
                        column_attr = getattr(CountryModel, all_vals[0])
                        statement = statement.order_by(col(column_attr))
            data = session.exec(statement).all()
            return list(data)

    @staticmethod
    def get_image_data() -> dict[str, str | list[CountryModel] | int]:
        from src import engine

        with Session(engine) as session:
            statement = (
                select(CountryModel)
                .order_by(col(CountryModel.estimated_gdp).desc())
                .limit(5)
            )
            top_countries = session.exec(statement).all()

            statement = (
                select(CountryModel)
                .order_by(col(CountryModel.last_refreshed_at).desc())
                .limit(1)
            )
            timestamp = session.exec(statement).first()
            timestamp = (
                timestamp.last_refreshed_at if timestamp else datetime.now(timezone.utc)
            )
            timestamp = timestamp.strftime("%d-%m-%yT%H:%M:%S").replace("+00.00", "Z")

            statement = select(func.count()).select_from(CountryModel)
            total_countries = session.exec(statement).one()

            return dict(
                total_countries=total_countries,
                top_countries=list(top_countries),
                timestamp=timestamp,
            )

    @staticmethod
    def update_country(model: CountryModel, new_model: CountryModel) -> None:
        from src import engine

        with Session(engine) as session:

            db_obj = session.get(CountryModel, model.id)

            if not db_obj:
                raise ValueError(f"{model.__name__} with id={model.id} not found")

            new_data = new_model.model_dump(exclude_unset=True)
            db_obj.sqlmodel_update(new_data)

            session.add(db_obj)
            session.commit()
            session.refresh(db_obj)
