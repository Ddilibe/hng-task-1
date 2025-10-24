#!/usr/bin/env python3
from typing import Any
from src.stage1.db import Database
from src.stage1.models import (
    InterpretedQueryModel,
    NaturalLangResponseModel,
    PostStringResponseModel,
    QueryResponseModel,
    RequestString,
)

from fastapi import status
from fastapi.requests import Request
from fastapi.routing import APIRouter
from fastapi.responses import Response
from fastapi.exceptions import HTTPException
from src.stage1.utils import NaturalLangFilter


app = APIRouter(prefix="/strings")
nfilter = NaturalLangFilter()


@app.post(
    "/",
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
    "/",
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
    "/{string}",
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
    "/filter-by-natural-language",
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
    "/{string_value}",
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
