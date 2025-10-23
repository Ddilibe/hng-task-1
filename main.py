#!/usr/bin/env Python3
# -*- coding: utf-8 -*-
#
# FastAPI application for HNG Stage 1 Task.
# This script defines a single API endpoint that returns user information,
# a timestamp, and a random cat fact fetched from an external API.

import json
import uuid
import hashlib
from typing import Any, Dict
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone

from fastapi import FastAPI, status
from fastapi.requests import Request
from fastapi.exceptions import HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response, JSONResponse
from fastapi.exceptions import RequestValidationError

from sqlmodel import JSON, Column, SQLModel, Field, create_engine, Session, select

import spacy
from spacy.matcher import Matcher
from spacy.language import Language

import uvicorn
import requests
from decouple import config


##########################################################################
# Natural Language filter class
##########################################################################
class NaturalLangFilter:
    """
    Natural Language Filter Parser and Context Extractor.

    Supports:
        - Detecting palindromes
        - Extracting numeric conditions (word_count, max_length, min_length)
        - Detecting character filters (contains_character)
        - Basic comparison word detection
    """

    # --- Pattern definitions ---
    pattern_palindrome = [
        {"LOWER": {"IN": ["check", "is", "test", "determine"]}, "OP": "?"},
        {"LOWER": "palindrome"},
    ]
    pattern_word_count = [
        {"LOWER": {"IN": ["count", "number", "how", "many"]}},
        {"LOWER": {"IN": ["words", "word"]}},
    ]
    pattern_max_length = [
        {"LOWER": {"IN": ["longest", "max", "maximum", "longer"]}},
        {"LOWER": {"IN": ["word", "length", "size", "characters"]}},
    ]
    pattern_min_length = [
        {"LOWER": {"IN": ["shortest", "min", "minimum", "shorter"]}},
        {"LOWER": {"IN": ["word", "length", "size", "characters"]}},
    ]
    pattern_contains_char = [
        {"LOWER": {"IN": ["contain", "contains", "have", "includes", "including"]}},
        {"LOWER": {"IN": ["char", "character", "letter", "symbol"]}, "OP": "?"},
    ]

    def __init__(self):
        try:
            self.nlp: Language = spacy.load("en_core_web_sm")
        except OSError:
            print(
                "Downloading 'en_core_web_sm' model. Run: python -m spacy download en_core_web_sm"
            )
            raise

        self.matcher = Matcher(self.nlp.vocab)
        self._setup_patterns()

        self.SYMBOLS = {
            "greater": ">",
            "more": ">",
            "above": ">",
            "higher": ">",
            "less": "<",
            "smaller": "<",
            "below": "<",
            "under": "<",
            "equal": "=",
            "equals": "=",
            "same": "=",
            "not": "≠",
            "different": "≠",
            "unequal": "≠",
        }

    def _setup_patterns(self):
        """Setup patterns for context extraction"""
        self.matcher.add("IS_PALINDROME", [self.pattern_palindrome])
        self.matcher.add("WORD_COUNT", [self.pattern_word_count])
        self.matcher.add("MAX_LENGTH", [self.pattern_max_length])
        self.matcher.add("MIN_LENGTH", [self.pattern_min_length])
        self.matcher.add("CONTAINS_CHARACTER", [self.pattern_contains_char])

    def extract_context(self, text: str) -> dict:
        """
        Extracts structured data from a natural language query.

        Example:
            "show strings longer than 10 characters" →
            {'max_length': 10}
        """
        doc = self.nlp(text)
        matches = self.matcher(doc)
        extracted_data = {}

        for match_id, start, end in matches:
            label = self.nlp.vocab.strings[match_id]

            if label == "IS_PALINDROME":
                extracted_data["is_palindrome"] = True

            elif label == "WORD_COUNT":
                extracted_data["word_count"] = self._extract_number(doc) or True

            elif label == "MAX_LENGTH":
                extracted_data["max_length"] = self._extract_number(doc)

            elif label == "MIN_LENGTH":
                extracted_data["min_length"] = self._extract_number(doc)

            elif label == "CONTAINS_CHARACTER":
                char = self._extract_character(doc)
                if char:
                    extracted_data["contains_character"] = char.lower()

        op = self.parse_filter_command(text)
        if op:
            extracted_data["filter_symbol"] = op

        return extracted_data

    def _extract_number(self, doc) -> int | None:
        """Extract numeric value from text"""
        for token in doc:
            if token.like_num:
                try:
                    return int(token.text)
                except ValueError:
                    pass
        return None

    def _extract_character(self, doc) -> str | None:
        """Extract a single character (like 'a' or 'z')"""
        for token in doc:
            if (
                len(token.text) == 1
                and token.is_alpha
                and not token.is_space
                and not token.is_punct
            ):
                return token.text
        return None

    def parse_filter_command(self, text: str) -> str | None:
        """Parse simple comparison words (no compound filters)"""
        doc = self.nlp(text.lower())
        for token in doc:
            lemma = token.lemma_
            if lemma in self.SYMBOLS:
                return self.SYMBOLS[lemma]
        return None


# Initialize the FastAPI application.
app = FastAPI(
    debug=False,
    title="HNG Stage 1 Task",
)
nfilter = NaturalLangFilter()

# Configure Cross-Origin Resource Sharing (CORS) middleware.
# This allows the API to be accessed from any domain and with any method,
# which is common for public APIs or development environments.
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_headers=["*"],
    allow_origins=["*"],
    allow_methods=["*"],
)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(req: Request, exc: RequestValidationError):
    """Handles validation errors for incoming requests.

    This exception handler is triggered when a request fails FastAPI's
    validation process—typically when the input data type or structure
    does not match the expected schema.

    Args:
        req (Request): The incoming HTTP request object.
        exc (RequestValidationError): The validation error raised by FastAPI.

    Returns:
        JSONResponse: A JSON response with a 422 Unprocessable Entity status code
        and a descriptive error message indicating that the 'value' field
        must be a string.
    """
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        content={"detail": "invalid datatype for 'value' (must be string) "},
    )


@dataclass
class User:
    """Represents the user's details for the API response."""

    email: str
    name: str
    stack: str

    def model_dump_json(self):
        """
        Dumps the User object data into a JSON-compatible dictionary.

        Returns:
            dict: The user's information.
        """
        return {"email": self.email, "name": self.name, "stack": self.stack}


@dataclass
class MeResponse:
    """Represents the structure of the final JSON response body."""

    status: str
    user: User
    timestamp: str
    fact: str

    def model_dump_json(self):
        """
        Dumps the MeResponse object data into a JSON-compatible dictionary.
        It recursively calls the model_dump_json method on the nested User object.

        Returns:
            dict: The complete response data.
        """
        return {
            "status": self.status,
            "user": self.user.model_dump_json(),
            "timestamp": self.timestamp,
            "fact": self.fact,
        }

    def to_json(self):
        """
        Serializes the response dictionary to a JSON string.

        Returns:
            str: The final JSON string for the API response.
        """
        return json.dumps(self.model_dump_json())


@app.get("/me", response_model=MeResponse)
async def me():
    """
    Handles the GET /me endpoint.

    Fetches a random fact from an external API, compiles the user data,
    and returns a structured JSON response.

    Returns:
        fastapi.responses.Response: The structured JSON response with status 200.

    Raises:
        HTTPException: If the external Cat Fact API request fails.
    """
    try:
        req: requests.Response = requests.get("https://catfact.ninja/fact")
        req.raise_for_status()
        cat_response: str = req.json().get("fact")

        current_datetime = datetime.now(timezone.utc)

        data = MeResponse(
            status="success",
            user=User(
                email="franklinfidelugwuowo@gmail.com",
                name="Fidelugwuowo Dilibe",
                stack="Python/FastAPI",
            ),
            fact=cat_response,
            timestamp=current_datetime.isoformat(
                sep="T", timespec="milliseconds"
            ).replace("+00:00", "Z"),
        )

        return Response(
            data.to_json(),
            status_code=200,
            headers={"Content-Type": "application/json"},
        )
    except requests.HTTPError:
        raise HTTPException(
            status_code=404,
            detail="Random Cat server is down. Try again after a while ",
        )


##########################################################################
# DB Table
##########################################################################


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

    def __init__(self, name: str, **kwargs):
        super().__init__(name=name, **kwargs)
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
# Database Setup
##########################################################################
# Define the name of the SQLite database file
# database_name = config("DATABASE_NAME", "database.db")

# Construct the full SQLite database URL using the defined file name
# sqlite_url = "sqlite:///%s" % database_name
sqlite_url = str(config("DATABASE_NAME", "sqlite:///database.db"))

# Create a SQLAlchemy engine instance for connecting to the SQLite database
# Setting echo=True enables SQL logging for debugging and visibility
engine = create_engine(sqlite_url, echo=True)

# Create all database tables defined in the SQLModel metadata
# This ensures that any models mapped to the database are initialized
SQLModel.metadata.create_all(engine)


##########################################################################
# DB Operation
##########################################################################
class Database:
    """Handles database operations for String records.

    This class provides static methods to add, retrieve, and delete
    string entries in the database using SQLModel sessions.
    """

    @staticmethod
    def add_string(value: str) -> String | None:
        """Adds a new string to the database if it does not already exist.

        Args:
            value (str): The string value to be added to the database.

        Returns:
            String | None: Returns the newly added String object if successful,
            otherwise returns None if the string already exists.
        """
        if Database.get_string(value) is None:
            new_string = String(name=value)
            with Session(engine) as session:
                session.add(new_string)
                session.commit()
                return new_string
        return None

    @staticmethod
    def get_string(value: str) -> String | None:
        """Retrieves a string record from the database.

        Args:
            value (str): The string value to look up in the database.

        Returns:
            String | None: Returns the String object if found, otherwise None.
        """
        with Session(engine) as session:
            statement = select(String).where(String.name == value)
            results = session.exec(statement).first()
            return results if results else None
        return None

    @staticmethod
    def delete_string(value: str) -> bool:
        """Deletes a string record from the database.

        Args:
            value (str): The string value to be deleted.

        Returns:
            bool: Returns True if the record was successfully deleted,
            otherwise False.
        """
        with Session(engine) as session:
            statement = select(String).where(String.name == value)
            results = session.exec(statement).first()
            if results:
                session.delete(results)
                session.commit()
                # session.refresh(results)
                return True
        return False

    @staticmethod
    def query_string(query: Dict[str, str | int | bool]) -> list[String]:
        """
        Dynamically builds and executes a query against the String table based on
        key-value filters provided in the 'query' dictionary.

        Args:
            query: A dictionary where keys are filter names and values are strings
                from the request query parameters.

        Returns:
            List[String]: A list of String model instances matching the criteria.
        """

        with Session(engine) as session:
            statement = select(String)
            if val := query.get("is_palindrome"):
                lower_val = str(val).lower()
                if lower_val not in ["true", "false", "1", "0"]:
                    raise ValueError(
                        f"Invalid value for 'is_palindrome': '{val}'. Must be true/false/1/0."
                    )
                is_pali = lower_val in ["true", "1"]
                statement = statement.where(String.is_palindrome == is_pali)
            if val := query.get("max_length"):
                try:
                    statement = statement.where(String.length <= int(val))
                except ValueError:
                    raise ValueError(
                        f"Invalid value for 'max_length': '{val}'. Must be an integer."
                    )
            if val := query.get("min_length"):
                try:
                    statement = statement.where(String.length >= int(val))
                except ValueError:
                    raise ValueError(
                        f"Invalid value for 'min_length': '{val}'. Must be an integer."
                    )
            if val := query.get("word_count"):
                try:
                    statement = statement.where(String.word_count == int(val))
                except ValueError:
                    raise ValueError(
                        f"Invalid value for 'word_count': '{val}'. Must be an integer."
                    )

            if val := query.get("contains_character"):
                if not isinstance(val, str) or len(val) != 1:
                    raise ValueError(
                        "The 'contains_character' filter requires exactly one character."
                    )
                statement = statement.where(
                    String.character_frequency_map[val].as_integer() >= 1
                )
            results = session.exec(statement).all()
            return list(results)


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


#############################################################################
#               Endpoints Sections
#############################################################################
@app.get("/")
def aapp():
    return Response(
        json.dumps({"status": "Welcome stringsphere API"}),
        status_code=status.HTTP_200_OK,
    )


@app.post(
    "/strings",
    response_model=PostStringResponseModel,
    responses={
        422: {"detail": " Invalid data type for 'value' (must be string)"},
        400: {"detail": "Invalid request body or missing 'value' field"},
        409: {"detail": "String already exists in the system"},
    },
)
async def post_strings(payload: RequestString):
    """Handles POST requests for adding new strings to the database.

    This endpoint receives a string value from the client, validates it,
    stores it in the database (if it doesn't already exist), and returns
    a structured JSON response with metadata about the created record.

    Args:
        payload (RequestString): The incoming request body containing
            the string value to be added.

    Returns:
        Response: A JSON response containing details of the newly created string,
            including its ID, value, and creation timestamp.

    Raises:
        HTTPException:
            - 400: If the input data type is invalid or the request body is malformed.
            - 409: If the string already exists in the database.
            - 422: If the request validation fails (e.g., incorrect input type).
    """
    value = payload.value
    if Database.add_string(value):
        try:
            response = Database.get_string(value)
            if not response:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="invalid datatype for 'value' (must be string) ",
                )
            data = PostStringResponseModel(
                id=response.id,
                value=value,
                properties=response,
                created_at=response.created_at,
            )
            return Response(
                data.to_json(),
                status_code=status.HTTP_201_CREATED,
                headers={"Content-Type": "application/json"},
            )
        except AssertionError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="invalid datatype for 'value' (must be string) ",
            )
    raise HTTPException(status_code=409, detail="String already exists in the system")


@app.get(
    "/strings",
    response_model=QueryResponseModel,
    responses={
        422: {"detail": " Invalid data type for 'value' (must be string)"},
        400: {"details": "Invalid request body or missing 'value' field"},
    },
)
async def query_strings(
    req: Request,
):
    """Handles GET requests for querying strings based on filters.

    This endpoint allows clients to retrieve strings from the database using
    supported query parameters (e.g., `is_palindrome`, `min_length`, etc.).
    It validates the query parameters, performs filtering, and returns the
    matching records along with metadata such as count and applied filters.

    Args:
        req (Request): The incoming HTTP request containing query parameters.

    Returns:
        Response: A JSON response containing the queried string data, count,
        and filters applied to the search.

    Raises:
        HTTPException:
            - 400: If invalid query parameters or values are provided.
            - 422: If the query data type is invalid.
    """
    try:
        query: dict[str, str | int | bool] = dict(req.query_params.items())
        query_set = set(query.keys())
        super_set = {
            "is_palindrome",
            "min_length",
            "max_length",
            "word_count",
            "contains_character",
        }
        if super_set.issuperset(query_set):
            data = [
                PostStringResponseModel(
                    id=d.id, value=d.name, properties=d, created_at=d.created_at
                )
                for d in Database.query_string(query)
            ]
            response = QueryResponseModel(
                data=data, count=len(data), filters_applied=query
            )
            return Response(
                response.to_json(),
                status_code=status.HTTP_200_OK,
                media_type="application/json",
            )
        raise AssertionError
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid query parameter values or types",
        )


@app.delete(
    "/strings/{string}",
    responses={
        422: {"detail": " Invalid data type for 'value' (must be string)"},
        400: {"details": "Invalid request body or missing 'value' field"},
    },
)
async def delete_strings(string: str):
    """Handles DELETE requests for removing a string record from the database.

    This endpoint deletes a specific string if it exists in the system.

    Args:
        string (str): The string value to be deleted.

    Returns:
        Response: An empty response with HTTP 204 No Content on successful deletion.

    Raises:
        HTTPException:
            - 404: If the specified string does not exist in the database.
            - 422: If the provided value is of an invalid data type.
    """
    if Database.delete_string(string):
        return Response("", status_code=status.HTTP_204_NO_CONTENT)
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="String does not exist in the system",
    )


@app.get(
    "/strings/filter-by-natural-language",
    response_model=NaturalLangResponseModel,
    responses={
        422: {"detail": " Invalid data type for 'value' (must be string)"},
        400: {"details": "Invalid request body or missing 'value' field"},
    },
)
async def natural_language_parsing(req: Request) -> Response:
    """Handles GET requests for filtering strings using natural language queries.

    This endpoint interprets natural language input (e.g.,
    "all single word palindromic strings") and converts it into
    structured filters that can be applied to query the database.

    The system supports predefined phrases through a lookup dictionary,
    and falls back to the Natural Language Filter (`nfilter`) when
    a query is not directly recognized.

    Args:
        req (Request): The incoming HTTP request containing a natural language query
            passed as a query parameter named `query`.

    Returns:
        Response: A JSON response containing the interpreted filters,
        matching data, and metadata (count and interpreted query).

    Raises:
        HTTPException:
            - 400: If no query is provided or the input cannot be parsed.
            - 422: If the query parsing results in invalid or conflicting filters.
    """
    natural_dict: dict[str, dict[str, str | bool | int]] = {
        "all single word palindromic strings": {"word_count": 1, "is_palindrome": True},
        "strings longer than 10 characters": {"min_length": 11},
        "palindromic strings that contain the first vowel": {
            "is_palindrome": True,
            "contains_character": "a",
        },
        "strings containing the letter z": {"contains_character": "z"},
    }
    query: str | None = req.query_params.get("query")
    if query and query.strip() != "":
        try:
            filters: Any = (
                natural_dict.get(query.lower())
                if natural_dict.get(query.lower())
                else nfilter.extract_context(query)
            )
            data = Database.query_string(filters)
            response = NaturalLangResponseModel(
                data=data,
                count=len(data),
                interpreted_query=InterpretedQueryModel(
                    original=query, parsed_filters=filters
                ),
            )
            return Response(response.to_json(), status_code=status.HTTP_200_OK)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail="Query parsed ut resulting in conflicting filters",
            )
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Unable to parse natural language query",
    )


@app.get(
    "/strings/{string_value}",
    response_model=PostStringResponseModel,
    responses={
        422: {"detail": " Invalid data type for 'value' (must be string)"},
        400: {"details": "Invalid request body or missing 'value' field"},
    },
)
async def get_strings(req: Request, string_value: str) -> Response:
    """Handles GET requests for retrieving a specific string record.

    This endpoint looks up a string in the database using its value.
    If the string exists, it returns a structured JSON response containing
    its metadata and properties. Otherwise, it raises a 404 error.

    Args:
        req (Request): The incoming HTTP request object.
        string_value (str): The string value to be retrieved from the database.

    Returns:
        Response: A JSON response containing the string details,
        including ID, value, and creation timestamp.

    Raises:
        HTTPException:
            - 404: If the string does not exist in the system.
            - 422: If the provided value is of an invalid data type.
    """
    if response := Database.get_string(string_value):
        data = PostStringResponseModel(
            id=response.id,
            value=string_value,
            properties=response,
            created_at=response.created_at,
        )
        return Response(
            data.to_json(),
            status_code=201,
            headers={"Content-Type": "application/json"},
        )
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="String does not exist in the system",
    )


if __name__ == "__main__":
    uvicorn.run("main:app", reload=True)
