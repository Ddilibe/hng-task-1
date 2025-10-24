#!/usr/bin/env python3

from dataclasses import dataclass
import uuid
import json
import hashlib
from typing import Any, Dict
from collections import Counter
from datetime import datetime, timezone

from sqlmodel import JSON, Column, Field, SQLModel


class String(SQLModel, table=True):
    """
    The class 'StringModel' inherits from SQLModel, making it a database table.

    Args:
        id (uuid): It uses a default value that generates a unique UUID (as a string)
            when a new record is created and none is provided.
        name (str): This column will store a simple string value.
    """

    __tablename__ = "strings"  # type: ignore
    __table_args__ = {"extend_existing": True}

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    name: str
    created_at: str
    length: int
    is_palindrome: bool
    unique_characters: int
    word_count: int
    sha256_hash: str
    character_frequency_map: Dict[str, Any] = Field(default={}, sa_column=Column(JSON))

    def __init__(self, name: str, *args, **kwargs):
        super().__init__(name=name, *args, **kwargs)
        if not self.length:
            self._calculate_properties()

    def _calculate_properties(self):
        """Calculates dynamic properties and sets them on the instance."""

        reversed_name = self.name[::-1]
        char_count = Counter(self.name)

        current_time = datetime.now(timezone.utc)
        created_at = current_time.isoformat(sep="T", timespec="milliseconds").replace(
            "+00:00", "Z"
        )

        self.created_at = created_at
        self.length = len(self.name)
        self.is_palindrome = self.name == reversed_name
        self.unique_characters = len(char_count)
        self.word_count = len(self.name.split())
        self.sha256_hash = hashlib.sha256(self.name.encode("utf-8")).hexdigest()
        self.character_frequency_map = dict(char_count)

    def get_reverse(self) -> str:
        """Returns the reversed version of the string's name."""
        return self.name[::-1]

    def __repr__(self) -> str:
        """Standard Python representation for debugging/logging."""
        return self.__str__()

    def __str__(self) -> str:
        """Human-readable string representation of the object."""
        return (
            f"\nI am '{self.name}'\n"
            f"I was created at {self.created_at}\n"
            f"I am {self.length} characters long\n"
        )

    def to_dict(self) -> dict:
        return {
            "length": self.length,
            "is_palindrome": self.is_palindrome,
            "unique_characters": self.unique_characters,
            "word_count": self.word_count,
            "sha256_hash": self.sha256_hash,
            "character_frequency_map": self.character_frequency_map,
        }

    def to_json(self):
        """
        Serializes the response dictionary to a JSON string.

        Returns:
            str: The final JSON string for the API response.
        """
        return json.dumps(self.to_dict())


##########################################################################
# Request Models
##########################################################################
class RequestString(SQLModel):
    """Represents a request model for string input.

    This model is used to validate and structure incoming request data
    containing a single string field.

    Attributes:
        value (str): The string value provided in the request.
    """

    value: str


##########################################################################
# Response Models
##########################################################################
@dataclass
class PostStringResponseModel:
    """Represents the response model for a POST request that creates a new string entry.

    Attributes:
        id (str): The unique identifier of the stored string.
        value (str): The string value that was added to the database.
        properties (String): The associated properties or metadata of the string.
        created_at (str): The timestamp when the string record was created.
    """

    id: str
    value: str
    properties: String
    created_at: str

    def to_dict(self):
        """Converts the response model to a dictionary representation.

        Returns:
            dict: A dictionary containing all model fields formatted for API output.
        """
        return {
            "id": self.id,
            "value": self.value,
            "properties": self.properties.to_dict(),
            "created_at": self.created_at,
        }

    def to_json(self):
        """Serializes the response model to a JSON string.

        Returns:
            str: The JSON-formatted string representation of the response model.
        """
        return json.dumps(self.to_dict())


@dataclass
class QueryResponseModel:
    """Represents the response model for queries retrieving multiple string records.

    Attributes:
        data (list[String]): The list of retrieved string objects.
        count (int): The total number of records that matched the query.
        filters_applied (dict[str, str]): The filters used in the query execution.
    """

    data: list[PostStringResponseModel]
    count: int
    filters_applied: dict[str, str | int | bool]

    def to_dict(self):
        """Converts the query response model to a dictionary.

        Returns:
            dict: A dictionary representation of the query response,
            including serialized string data and applied filters.
        """
        return {
            "data": list(map(lambda x: x.to_dict(), self.data)),
            "count": self.count,
            "filters_applied": self.filters_applied,
        }

    def to_json(self):
        """Serializes the query response to a JSON string.

        Returns:
            str: The JSON-formatted string representation of the query response.
        """
        return json.dumps(self.to_dict())


@dataclass
class InterpretedQueryModel:
    """Represents an interpreted natural language query.

    Attributes:
        original (str): The original natural language query provided by the user.
        parsed_filters (dict[str, str | int | bool]): The extracted filters or parameters
            derived from interpreting the original query.
    """

    original: str
    parsed_filters: dict[str, str | int | bool]

    def to_dict(self):
        """Converts the interpreted query model to a dictionary.

        Returns:
            dict: A dictionary containing the original query and parsed filters.
        """
        return {"original": self.original, "parsed_filters": self.parsed_filters}

    def to_json(self):
        """Serializes the interpreted query model to a JSON string.

        Returns:
            str: The JSON-formatted string representation of the interpreted query.
        """
        return json.dumps(self.to_dict())


@dataclass
class NaturalLangResponseModel:
    """Represents the response model for natural language queries.

    Attributes:
        data (list[String]): The list of strings matching the interpreted query.
        count (int): The total number of matching records.
        interpreted_query (InterpretedQueryModel): The interpreted version of the user’s query.
    """

    data: list[String]
    count: int
    interpreted_query: InterpretedQueryModel

    def to_dict(self):
        """Converts the natural language response model to a dictionary.

        Returns:
            dict: A dictionary containing data, count, and interpreted query details.
        """
        return {
            "data": list(map(lambda x: x.to_dict(), self.data)),
            "count": self.count,
            "filters_applied": self.interpreted_query.to_dict(),
        }

    def to_json(self):
        """Serializes the natural language response model to a JSON string.

        Returns:
            str: The JSON-formatted string representation of the response model.
        """
        return json.dumps(self.to_dict())
