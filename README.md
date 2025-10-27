# StringSphere Backend API: HNG Challenge Solution 🌐

## Overview
This project delivers a robust backend API built with FastAPI, addressing multiple stages of the HNG challenge. It encompasses user information retrieval, string analysis with natural language processing, and comprehensive country data management, including external API integrations and dynamic image generation. The API is designed for high performance, scalability, and ease of use, leveraging modern Python paradigms and a relational database for data persistence.

## Features
- **User Information Endpoint**: Provides personal details and integrates a fun, random cat fact from an external API.
- **Advanced String Analysis Service**: Computes properties like length, palindrome status, unique characters, word count, SHA-256 hash, and character frequency for any given string.
- **Natural Language Querying for Strings**: Interprets human-readable queries (e.g., "all single word palindromic strings") to filter string data dynamically using Google's GenAI.
- **Comprehensive Country Data Management**: Fetches, caches, and provides CRUD operations for country-specific information, including population, currency, exchange rates, and estimated GDP.
- **Dynamic Image Generation**: Automatically creates and serves a summary image after country data refreshes, displaying total countries and top GDP performers.
- **Flexible Data Filtering & Sorting**: Supports detailed query parameters for both string and country data, enabling powerful data exploration.
- **Robust Error Handling**: Implements consistent JSON-based error responses for various scenarios, including validation failures, conflicts, and external service unavailability.
- **Database Persistence**: Utilizes SQLModel with SQLite to store and manage string analysis results and cached country data.

## Getting Started
To get a copy of this project up and running on your local machine, follow these steps.

### Installation
1.  **Clone the Repository**:
    ```bash
    git clone git@github.com:Ddilibe/hng-task-1.git
    cd hng-task-1
    ```
2.  **Create and Activate a Virtual Environment**:
    ```bash
    python -m venv venv
    # On Linux/macOS:
    source venv/bin/activate
    # On Windows:
    venv\Scripts\activate
    ```
3.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

### Environment Variables
The application requires the following environment variables. Create a `.env` file in the root directory and populate it as follows:

-   `DATABASE_NAME`: Specifies the database connection string. Defaults to an SQLite file.
    *   **Example**: `DATABASE_NAME="sqlite:///database.db"`
-   `GOOGLE_GEN_API_KEY`: Your API key for Google's Generative AI services, used for natural language processing in Stage 1.
    *   **Example**: `GOOGLE_GEN_API_KEY="YOUR_GOOGLE_GEN_AI_KEY"`

## API Documentation

### Base URL
The API is typically accessible at `http://127.0.0.1:8000` when running locally, or at the deployed domain.

### Endpoints

#### GET /
**Overview**: A basic health check endpoint to confirm the API is operational.
**Request**:
None

**Response**:
```json
{
  "status": "Welcome stringsphere API"
}
```

**Errors**:
None

#### GET /me
**Overview**: Retrieves personal information about the author and a random cat fact from an external API.
**Request**:
None

**Response**:
```json
{
  "status": "success",
  "user": {
    "email": "franklinfidelugwuowo@gmail.com",
    "name": "Fidelugwuowo Dilibe",
    "stack": "Python/FastAPI"
  },
  "timestamp": "2025-10-17T20:00:00.123Z",
  "fact": "Cats dislike citrus scent"
}
```

**Errors**:
-   `404 Not Found`: The external Cat Fact API is unreachable or returns an error.
    ```json
    {
      "detail": "Random Cat server is down. Try again after a while"
    }
    ```

#### POST /strings
**Overview**: Analyzes a given string and stores its properties in the database.
**Request**:
```json
{
  "value": "string to analyze"
}
```

**Response**:
```json
{
  "id": "a1b2c3d4-e5f6-7890-1234-567890abcdef",
  "value": "string to analyze",
  "properties": {
    "length": 17,
    "is_palindrome": false,
    "unique_characters": 12,
    "word_count": 3,
    "sha256_hash": "c0ffee...beef",
    "character_frequency_map": {
      "s": 2,
      "t": 3,
      "r": 2,
      "i": 1,
      "n": 1,
      "g": 1,
      " ": 1,
      "o": 1,
      "a": 2,
      "l": 1,
      "y": 1,
      "z": 1,
      "e": 1
    }
  },
  "created_at": "2025-08-27T10:00:00.000Z"
}
```

**Errors**:
-   `400 Bad Request`: Invalid request body or the `value` field is missing.
-   `409 Conflict`: The provided string already exists in the system.
-   `422 Unprocessable Entity`: The `value` field is not a string.

#### GET /strings/{string_value}
**Overview**: Retrieves the detailed properties of a specific string by its value.
**Request**:
None. The string value is provided as a path parameter.

**Response**:
(Same as POST /strings success response)
```json
{
  "id": "a1b2c3d4-e5f6-7890-1234-567890abcdef",
  "value": "requested string",
  "properties": {
    "length": 16,
    "is_palindrome": false,
    "unique_characters": 11,
    "word_count": 2,
    "sha256_hash": "abcdef...123456",
    "character_frequency_map": {
      "r": 2, "e": 2, "q": 1, "u": 1, "s": 2, "t": 2, "d": 1, " ": 1, "i": 1, "n": 1, "g": 1
    }
  },
  "created_at": "2025-08-27T10:00:00Z"
}
```

**Errors**:
-   `404 Not Found`: The specified string does not exist in the system.
-   `422 Unprocessable Entity`: The `string_value` path parameter is not a string.

#### GET /strings
**Overview**: Retrieves a list of strings from the database, allowing filtering by various properties.
**Request**:
Query Parameters:
-   `is_palindrome` (optional): `boolean` (`true`, `false`, `1`, `0`). Filters for palindromic or non-palindromic strings.
-   `min_length` (optional): `integer`. Filters for strings with a minimum character length.
-   `max_length` (optional): `integer`. Filters for strings with a maximum character length.
-   `word_count` (optional): `integer`. Filters for strings with an exact word count.
-   `contains_character` (optional): `string` (single character). Filters for strings containing a specific character.

**Response**:
```json
{
  "data": [
    {
      "id": "uuid-string-1",
      "value": "madam",
      "properties": {
        "length": 5,
        "is_palindrome": true,
        "unique_characters": 3,
        "word_count": 1,
        "sha256_hash": "somehashvalue1",
        "character_frequency_map": { "m": 2, "a": 2, "d": 1 }
      },
      "created_at": "2025-08-27T10:00:00Z"
    },
    {
      "id": "uuid-string-2",
      "value": "level",
      "properties": {
        "length": 5,
        "is_palindrome": true,
        "unique_characters": 3,
        "word_count": 1,
        "sha256_hash": "somehashvalue2",
        "character_frequency_map": { "l": 2, "e": 2, "v": 1 }
      },
      "created_at": "2025-08-27T10:01:00Z"
    }
  ],
  "count": 2,
  "filters_applied": {
    "is_palindrome": true,
    "min_length": 5,
    "word_count": 1
  }
}
```

**Errors**:
-   `400 Bad Request`: Invalid query parameter values or types (e.g., `min_length` is not an integer).
-   `422 Unprocessable Entity`: Invalid query parameter values or types.

#### GET /strings/filter-by-natural-language
**Overview**: Filters string records based on a natural language query, which is interpreted into structured filters.
**Request**:
Query Parameters:
-   `query`: `string`. A natural language query (e.g., "all single word palindromic strings").

**Response**:
```json
{
  "data": [
    {
      "id": "uuid-string-3",
      "value": "racecar",
      "properties": {
        "length": 7,
        "is_palindrome": true,
        "unique_characters": 4,
        "word_count": 1,
        "sha256_hash": "somehashvalue3",
        "character_frequency_map": { "r": 2, "a": 2, "c": 2, "e": 1 }
      },
      "created_at": "2025-08-27T10:02:00Z"
    }
  ],
  "count": 1,
  "interpreted_query": {
    "original": "all single word palindromic strings",
    "parsed_filters": {
      "word_count": 1,
      "is_palindrome": true
    }
  }
}
```

**Errors**:
-   `400 Bad Request`: The natural language query is malformed or cannot be parsed.
-   `422 Unprocessable Entity`: The parsed natural language query results in conflicting or invalid filters.

#### DELETE /strings/{string}
**Overview**: Deletes a specific string record from the database.
**Request**:
None. The string value is provided as a path parameter.

**Response**:
(Empty response body with HTTP 204 status code)

**Errors**:
-   `404 Not Found`: The specified string does not exist in the system.
-   `422 Unprocessable Entity`: The `string` path parameter is not a string.

#### POST /countries/refresh
**Overview**: Fetches fresh country data and exchange rates from external APIs, then updates or inserts records into the database. Also triggers summary image generation.
**Request**:
None

**Response**:
(Empty response body with HTTP 200 status code)

**Errors**:
-   `503 Service Unavailable`: An external API (restcountries.com or open.er-api.com) failed or timed out during data fetching.
    ```json
    {
      "error": "External data source unavailable",
      "details": "Could not fetch data from [API name]"
    }
    ```

#### GET /countries
**Overview**: Retrieves all cached country records, supporting filtering and sorting.
**Request**:
Query Parameters (optional):
-   `name`: `string`. Filters by country name (case-sensitive).
-   `capital`: `string`. Filters by capital city.
-   `region`: `string`. Filters by geographical region (e.g., "Africa").
-   `population`: `integer`. Filters by exact population count.
-   `currency_code`: `string`. Filters by currency code (e.g., "NGN").
-   `sort`: `string`. Sorts results by a specific field (`estimated_gdp`, `population`, `name`, `last_refreshed_at`) in ascending (`_asc`) or descending (`_desc`) order.
    *   **Example**: `sort=estimated_gdp_desc` (Note: The provided code's `filter_countries` method does not yet implement sorting directly via query parameter, but the homework implied it. Sorting might need to be applied client-side or implemented in the `Database` layer.)

**Response**:
```json
[
  {
    "id": "uuid-string-1",
    "name": "Nigeria",
    "capital": "Abuja",
    "region": "Africa",
    "population": 206139589,
    "currency_code": "NGN",
    "exchange_rate": 1600.23,
    "estimated_gdp": 25767448125.2,
    "flag_url": "https://flagcdn.com/ng.svg",
    "last_refreshed_at": "2025-10-22T18:00:00Z"
  },
  {
    "id": "uuid-string-2",
    "name": "Ghana",
    "capital": "Accra",
    "region": "Africa",
    "population": 31072940,
    "currency_code": "GHS",
    "exchange_rate": 15.34,
    "estimated_gdp": 3029834520.6,
    "flag_url": "https://flagcdn.com/gh.svg",
    "last_refreshed_at": "2025-10-22T18:00:00Z"
  }
]
```

**Errors**:
-   `400 Bad Request`: Invalid query parameters or types provided (e.g., filtering by an unsupported field).

#### GET /countries/status
**Overview**: Provides a summary of the cached country data, including the total count and the timestamp of the last refresh.
**Request**:
None

**Response**:
```json
{
  "total_countries": 250,
  "last_refreshed_at": "2025-10-22T18:00:00Z"
}
```

**Errors**:
None. (Assumes at least one country entry exists for `last_refreshed_at` to be meaningful).

#### GET /countries/image
**Overview**: Serves a dynamically generated summary image (PNG) containing country statistics.
**Request**:
None

**Response**:
(Binary PNG image data)

**Errors**:
-   `400 Bad Request`: The summary image (`cache/summary.png`) does not exist or could not be found.
    ```json
    {
      "error": "Summary image not found"
    }
    ```

#### GET /countries/{name}
**Overview**: Retrieves a specific country record by its official name.
**Request**:
None. The country name is provided as a path parameter.

**Response**:
```json
{
  "id": "uuid-string-1",
  "name": "Nigeria",
  "capital": "Abuja",
  "region": "Africa",
  "population": 206139589,
  "currency_code": "NGN",
  "exchange_rate": 1600.23,
  "estimated_gdp": 25767448125.2,
  "flag_url": "https://flagcdn.com/ng.svg",
  "last_refreshed_at": "2025-10-22T18:00:00Z"
}
```

**Errors**:
-   `400 Bad Request`: The specified country was not found in the database.
    ```json
    { "error": "Country not found" }
    ```
    (Note: The homework specified 404 Not Found for this scenario, but the current implementation returns 400. Documenting based on code's behavior.)

#### DELETE /countries/{name}
**Overview**: Deletes a specific country record from the database by its official name.
**Request**:
None. The country name is provided as a path parameter.

**Response**:
(Empty response body with HTTP 200 status code upon successful deletion in current code, but homework specified 204 No Content. Following homework specs for consistency in API design.)

**Errors**:
-   `400 Bad Request`: The specified country was not found in the database.
    ```json
    { "error": "Country not found" }
    ```
    (Note: The homework specified 404 Not Found for this scenario, but the current implementation returns 400. Documenting based on code's behavior.)

## Technologies Used

| Component Type       | Component                 | Description                                                                 | Link                                                     |
| :------------------- | :------------------------ | :-------------------------------------------------------------------------- | :------------------------------------------------------- |
| **Framework**        | **FastAPI**               | High-performance Python web framework for building APIs.                    | [![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=flat-square&logo=fastapi)](https://fastapi.tiangolo.com/) |
| **Server**           | **Uvicorn**               | Lightning-fast ASGI server for running FastAPI applications.                | [![Uvicorn](https://img.shields.io/badge/Uvicorn-F00000?style=flat-square&logo=uvicorn)](https://www.uvicorn.org/) |
| **ORM & Database**   | **SQLModel**              | SQL-driven Pythonic models for SQL databases, built on SQLAlchemy and Pydantic. | [![SQLModel](https://img.shields.io/badge/SQLModel-FF5733?style=flat-square&logo=sqlmodel)](https://sqlmodel.tiangolo.com/) |
| **Data Validation**  | **Pydantic**              | Data parsing and validation library with type hints.                        | [![Pydantic](https://img.shields.io/badge/Pydantic-E92063?style=flat-square&logo=pydantic)](https://docs.pydantic.dev/latest/) |
| **HTTP Client**      | **Requests**              | Elegant and simple HTTP library for Python.                                | [![Requests](https://img.shields.io/badge/Requests-007FFF?style=flat-square&logo=requests)](https://requests.readthedocs.io/en/latest/) |
| **Configuration**    | **Python-Decouple**       | Manages environment variables and configuration settings.                   | [![Python-Decouple](https://img.shields.io/badge/Decouple-008080?style=flat-square&logo=python)](https://pypi.org/project/python-decouple/) |
| **AI/NLP**           | **Google GenAI**          | Integrates Google's Generative AI for natural language processing.          | [![Google GenAI](https://img.shields.io/badge/Google%20GenAI-4285F4?style=flat-square&logo=google)](https://ai.google.dev/docs/gemini_api_overview) |
| **Image Processing** | **Pillow**                | Python Imaging Library fork for image manipulation and generation.          | [![Pillow](https://img.shields.io/badge/Pillow-4285F4?style=flat-square&logo=python)](https://python-pillow.org/) |
| **Language**         | **Python 3.12**           | The primary programming language used.                                      | [![Python](https://img.shields.io/badge/Python-3776AB?style=flat-square&logo=python)](https://www.python.org/) |

## Author Info

**Fidelugwuowo Dilibe**

Connect with me:
- **LinkedIn**: [Your LinkedIn Profile](https://linkedin.com/in/fidelugwuowo)
- **Twitter**: [Your Twitter Handle](https://twitter.com/your_twitter_handle)

---
![Python 3.12](https://img.shields.io/badge/Python-3.12-blue?style=flat-square&logo=python)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=flat-square&logo=fastapi)
![SQLModel](https://img.shields.io/badge/SQLModel-FF5733?style=flat-square&logo=sqlmodel)
![Uvicorn](https://img.shields.io/badge/Uvicorn-F00000?style=flat-square&logo=uvicorn)

[![Readme was generated by Dokugen](https://img.shields.io/badge/Readme%20was%20generated%20by-Dokugen-brightgreen)](https://www.npmjs.com/package/dokugen)