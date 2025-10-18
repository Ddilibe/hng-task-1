#!/usr/bin/env Python3
# -*- coding: utf-8 -*-
#
# FastAPI application for HNG Stage 1 Task.
# This script defines a single API endpoint that returns user information,
# a timestamp, and a random cat fact fetched from an external API.

import json
from dataclasses import dataclass
from datetime import datetime, timezone

from fastapi import FastAPI
from fastapi.responses import Response
from fastapi.exceptions import HTTPException
from fastapi.middleware.cors import CORSMiddleware

import requests
import uvicorn

# Initialize the FastAPI application.
app = FastAPI(
    debug=False,
    title="HNG Stage 1 Task",
)

# Configure Cross-Origin Resource Sharing (CORS) middleware.
# This allows the API to be accessed from any domain and with any method,
# which is common for public APIs or development environments.
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_headers=["*"],
    allow_origins=["*"],
    allow_methods=["GET"],
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


if __name__ == "__main__":
    uvicorn.run("main:app", reload=True)
