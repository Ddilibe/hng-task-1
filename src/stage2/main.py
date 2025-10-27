#!/usr/bin/env python3
import os
import json
from typing import Any
from pathlib import Path
from copy import deepcopy
from datetime import datetime, timezone

from fastapi import HTTPException
from fastapi.requests import Request
from fastapi import APIRouter, status
from fastapi.responses import Response, FileResponse, JSONResponse

from src.stage2 import Database, CountryModel, generate_image, create_country_model
from src.stage2.utils import Stage2Exception


app = APIRouter(prefix="/countries")


@app.post("/refresh")
async def post_refresh():

    external_countries = Database.get_external_countries()
    update_countries: list[list[CountryModel]] = []
    create_countries: list[CountryModel] = []
    for i in external_countries:
        try:
            new_country = create_country_model(i)
            country_name: str = str(i.get("name")) if i.get("name") else ""
            old_country = Database.get_country_with_name(country_name)
            if old_country == None and new_country != None:
                create_countries.append(new_country)
                continue

            if (
                new_country != None
                and old_country != None
                and new_country != old_country
            ):
                update_countries.append([old_country, new_country])

        except Exception as e:
            continue
    Database.add_country(create_countries)
    map(lambda x: Database.update_country(x[0], x[1]), update_countries)
    generate_image()
    return Response()


@app.get("", response_model=list[CountryModel])
async def get_countries(req: Request):
    query = dict(req.query_params)
    cols = deepcopy(list(query.keys()))
    if "sort" in cols:
        cols.remove("sort")
    if not set(CountryModel.__dict__.keys()).issuperset(cols):
        raise

    data = list(map(lambda x: x.clean_json(), Database.filter_countries(query)))
    return JSONResponse(
        content=data,
        status_code=status.HTTP_200_OK,
    )


@app.get("/status")
async def get_status():
    data = Database.get_all_countries()
    latest = (
        sorted(data, key=lambda x: x.last_refreshed_at, reverse=True)[
            0
        ].last_refreshed_at
        if len(data) > 0
        else datetime.now(timezone.utc)
    )
    response = {
        "total_countries": len(data),
        "last_refreshed_at": latest.strftime(
            "%d-%m-%YT%H:%M:%S",
        ).replace("+00:00", "Z"),
    }
    return Response(
        content=json.dumps(response),
        status_code=status.HTTP_200_OK,
        headers={"Content-Type": "application/json"},
    )


@app.get("/image")
async def get_image():
    generate_image()
    image_path = Path("cache/summary.png")
    if image_path.exists():
        return FileResponse(
            path=image_path,
            status_code=status.HTTP_200_OK,
            media_type="image/png",
            filename=image_path.name,
        )
    raise Stage2Exception(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Summary image not found",
    )


@app.get("/{name}")
async def get_country(name: str) -> Response:
    country = Database.get_country_with_name(name)
    if country:
        return Response(
            content=json.dumps(country.clean_json()),
            status_code=status.HTTP_200_OK,
            headers={"Content-Type": "application/json"},
        )
    raise Stage2Exception(
        detail="Country not found", status_code=status.HTTP_404_NOT_FOUND
    )


@app.delete("/{name}")
async def delete_country(name: str) -> Response:
    country = Database.delete_country_with_name(name)
    if country:
        return Response(
            content=None,
            headers={"Content-Type": "application/json"},
            status_code=status.HTTP_204_NO_CONTENT,
        )
    raise Stage2Exception(
        detail="Country not found", status_code=status.HTTP_404_NOT_FOUND
    )
