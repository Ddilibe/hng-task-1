#!/usr/bin/env Python3
# -*- coding: utf-8 -*-
#
# FastAPI application for HNG Stage 1 Task.
# This script defines a single API endpoint that returns user information,
# a timestamp, and a random cat fact fetched from an external API.

import json
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, status
from fastapi.requests import Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response, JSONResponse
from fastapi.exceptions import RequestValidationError

from src import init_db, stage0, stage1, stage2
from src.stage2.utils import Stage2Exception, remove_countries, upload_countries


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Run the table creation function only once when the server starts.
    This prevents the 'Table already defined' error.
    """
    await init_db()
    # try:
    # await upload_countries()
    # except Exception as e:
    # print(f"⚠️ Country upload failed: {e}")
    yield
    # await close_db_connection()


# Initialize the FastAPI application.
app = FastAPI(debug=False, title="HNG Stage 1 Task", lifespan=lifespan)

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


@app.exception_handler(Stage2Exception)
async def custom_exception_handler(request: Request, exc: Stage2Exception):
    return JSONResponse(
        status_code=400,
        content={
            "error": exc.detail,
        },
    )


@app.get("/")
def main_app():
    return Response(
        json.dumps({"status": "Welcome stringsphere API"}),
        status_code=status.HTTP_200_OK,
    )


app.include_router(stage0, tags=["Stage 0"])
app.include_router(stage1, tags=["Stage 1"])
app.include_router(stage2, tags=["Stage 2"])


if __name__ == "__main__":
    uvicorn.run("main:app", reload=True)
