#!/usr/bin/env python3
from typing import Any, Self
from datetime import datetime, timezone

from sqlmodel import SQLModel, Field


class CountryModel(SQLModel, table=True):
    """Database model representing a country and its economic details.

    Attributes:
        id (uuid.UUID): Unique identifier for the country record.
        name (str): Official name of the country.
        capital (str | None): Capital city of the country.
        region (str | None): Geographical region (e.g., Africa, Europe).
        population (int): Total population of the country (must be > 0).
        currency_code (str): Currency code (e.g., NGN, USD).
        exchange_rate (float): Exchange rate against a base currency (must be > 0).
        estimated_gdp (float): Estimated Gross Domestic Product (GDP) (must be ≥ 0).
        flag_url (str | None): URL to the country's flag image.
        last_refreshed_at (datetime): Timestamp when data was last updated.
    """

    id: int = Field(default=None, primary_key=True)
    name: str = Field(title="Country Name", nullable=False, unique=True, index=True)
    capital: str | None = Field(default=None, title="Capital City")
    region: str | None = Field(default=None, title="Region")
    population: int = Field(title="Population", nullable=False)
    currency_code: str | None = Field(
        title="Currency Code", max_length=10, nullable=True
    )
    exchange_rate: float | None = Field(default=0, title="Exchange Rate", nullable=True)
    estimated_gdp: float | None = Field(default=0, title="Estimated GDP", nullable=True)
    flag_url: str | None = Field(default=None, title="Flag URL")

    last_refreshed_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        title="Last Refreshed At",
        sa_column_kwargs={"onupdate": lambda: datetime.now(timezone.utc)},
    )

    def __eq__(self, other: object) -> bool:
        """Checks if two CountryModel instances are equal.

        Args:
            other (object): The object to compare with.

        Returns:
            bool: True if both models have the same data (excluding timestamps and IDs), False otherwise.
        """
        if not isinstance(other, CountryModel):
            return NotImplemented

        return (
            self.name == other.name
            and self.capital == other.capital
            and self.region == other.region
            and self.population == other.population
            and self.currency_code == other.currency_code
            and self.exchange_rate == other.exchange_rate
            and self.estimated_gdp == other.estimated_gdp
            and self.flag_url == other.flag_url
        )
        
    
    def clean_json(self) -> dict[str, Any]:
        return {
            "id": int(self.id),
            "name": self.name,
            "capital": self.capital,
            "region": self.region,
            "population": int(self.population),
            "currency_code": self.currency_code,
            "exchange_rate": round(float(self.exchange_rate), 2),
            "estimated_gdp": round(float(self.estimated_gdp), 2),
            "flag_url": self.flag_url,
            "last_refreshed_at": str(self.last_refreshed_at),
        }

