import json
import os
import uuid
from functools import lru_cache
from typing import Annotated

import pandas as pd

# TODO: Use Cloud Secret Manager (https://cloud.google.com/secret-manager) instead of env vars
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Path, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import RedirectResponse
from sqlalchemy import create_engine
from sqlalchemy.dialects import postgresql
from sqlalchemy.engine import URL, Engine

from models import (
    ErrorResponse,
    PoliciesResponse,
    PolicyResponse,
    ZoneResponse,
    ZonesResponse,
)

load_dotenv()


# Schema holding the API views (vw_curb_zones, vw_curb_policies). Set DB_SCHEMA to override.
DB_SCHEMA = os.environ.get("DB_SCHEMA", "public_cds")
_quote_schema = postgresql.dialect().identifier_preparer.quote_schema
ZONES_VIEW = f"{_quote_schema(DB_SCHEMA)}.vw_curb_zones"
POLICIES_VIEW = f"{_quote_schema(DB_SCHEMA)}.vw_curb_policies"


@lru_cache
def get_engine() -> Engine:
    """Create the DB engine on first use so the app can be imported (e.g. to export the OpenAPI spec) without DB settings."""
    url_object = URL.create(
        drivername="postgresql",
        username=os.environ["DB_USER"],
        password=os.environ["DB_PASS"],
        host=os.environ["DB_HOST"],
        database=os.environ["DB_NAME"],
    )
    return create_engine(url_object)


RESPONSE_DEFAULT_PARMS = {
    "version": "1.0",
    "time_zone": "US/Eastern",
    "last_updated": 1767565837844,
    "currency": "USD",
    "author": "City of Boston",
    #   "license_url": "https://creativecommons.org/licenses/by/4.0/", # TODO: License type?
}

API_DESCRIPTION = """
Read-only API for the City of Boston's curb data, following the
[Open Mobility Foundation CDS Curbs API](https://github.com/openmobilityfoundation/curb-data-specification).

* **Zones** are sections of curb with a geometry.
* **Policies** describe the rules, time spans and rates that apply to zones.

All endpoints are `GET`, require no authentication, and wrap results in a common
envelope (`version`, `time_zone`, `last_updated`, `currency`, `author`, `data`).
Timestamps are milliseconds since the Unix epoch.
"""

TAGS_METADATA = [
    {"name": "Zones", "description": "Curb zones and their geometry."},
    {"name": "Policies", "description": "Policies, rules, time spans and rates."},
]

app: FastAPI = FastAPI(
    title="City of Boston Curbs API",
    summary="This is the API for the City of Boston Curb data",
    description=API_DESCRIPTION,
    version="0.1",
    contact={"name": "Office of Emerging Technology", "email": "oet@boston.gov"},
    openapi_tags=TAGS_METADATA,
)

# add compression
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    # allow_origins=[
    # "http://localhost:3000",    # For local development
    # "http://localhost:8080",    # Alternative local port
    # "http://localhost:5173",    # Vite default port
    # "https://oetboston.github.io/curb-atlas", # Might not be necessary, we can remove after testing
    # "https://oetboston.github.io",
    # Add your developer's production frontend URL here when you know it
    # "https://their-map-frontend.boston.gov",
    # ],
    allow_credentials=True,  # Required for IAP authentication
    allow_methods=["*"],  # Allow all HTTP methods
    allow_headers=["*"],  # Allow all headers including Authorization
)


@app.get("/", include_in_schema=False)
async def redirect_to_docs():
    """Redirect the base URL to the /docs documentation page."""
    return RedirectResponse(url="/docs")


# Example request: /curbs/zones?min_lng=-71.04695320129396&min_lat=42.339482118418005&max_lng=-71.05236053466798&max_lat=42.34163915108597
# Example request: /curbs/zones?lng=-71.05052025698136&lat=42.34100193645163&radius=3500
# Example request: /curbs/zones?include_geometry=false&time=1765498738000
@app.get(
    "/curbs/zones",
    tags=["Zones"],
    summary="Query curb zones",
    response_model=ZonesResponse,
    response_model_exclude_unset=True,
    responses={400: {"model": ErrorResponse}},
)
async def query_curb_zones(
    area: Annotated[
        uuid.UUID | None,
        Query(description="Curb area ID. Accepted but currently ignored."),
    ] = None,  # Still need curb_area table
    min_lat: Annotated[
        float | None, Query(description="Bounding box south edge (latitude).")
    ] = None,
    min_lng: Annotated[
        float | None, Query(description="Bounding box west edge (longitude).")
    ] = None,
    max_lat: Annotated[
        float | None, Query(description="Bounding box north edge (latitude).")
    ] = None,
    max_lng: Annotated[
        float | None, Query(description="Bounding box east edge (longitude).")
    ] = None,
    lat: Annotated[
        float | None, Query(description="Latitude of the search circle center.")
    ] = None,
    lng: Annotated[
        float | None, Query(description="Longitude of the search circle center.")
    ] = None,
    radius: Annotated[
        float | None, Query(description="Search circle radius in **centimeters**.")
    ] = None,
    include_geometry: Annotated[
        bool, Query(description="Set to false to omit each zone's `geometry`.")
    ] = True,
    time: Annotated[
        int | None,
        Query(
            description="Only zones valid at this time (milliseconds since the Unix epoch). A null `start_date` or `end_date` counts as unbounded."
        ),
    ] = None,
    limit: Annotated[int, Query(description="Maximum zones to return.")] = 10000,
    offset: Annotated[int, Query(description="Number of zones to skip.")] = 0,
):
    """Return curb zones, optionally filtered by area, bounding box, or radius, and by time.

    * The bounding box parameters (`min_lat`, `min_lng`, `max_lat`, `max_lng`) must be
      given all together or not at all.
    * `lat`, `lng` and `radius` must be given all together or not at all.
    * A value of `0` for any of these is treated as missing.
    * Results are ordered by `curb_zone_id` and paged with `limit` and `offset`.
    """
    if (min_lat or min_lng or max_lat or max_lng) and not (
        min_lat and min_lng and max_lat and max_lng
    ):
        raise HTTPException(
            status_code=400,
            detail="Either all or none of 4 parameters min_lat, min_lng, max_lat and max_lng must be specified",
        )
    if (lat or lng or radius) and not (lat and lng and radius):
        raise HTTPException(
            status_code=400,
            detail="Either all or none of 3 parameters lat, lng and radius must be specified",
        )
    # TODO: Should we allow both (lat and lng and radius) and (min_lat and min_lng and max_lat and max_lng)?

    query = f"""
        SELECT
            curb_zone_id,
            geometry_json::JSON AS geometry,
            curb_policy_ids,
            published_date,
            last_updated_date,
            start_date,
            end_date,
            name,
            description,
            jurisdiction_type,
            owner_name,
            user_zone_id,
            street_name,
            address_number,
            cross_street_start_name,
            length,
            available,
            available_space_lengths,
            availability_time,
            width,
            parking_angle,
            num_spaces,
            street_side,
            median,
            entire_roadway
        FROM {ZONES_VIEW}
        WHERE 1=1"""
    parms = {}

    # TODO area logic

    if min_lat:
        query += " AND geometry::geometry && ST_MakeEnvelope(%(min_lng)s, %(min_lat)s, %(max_lng)s, %(max_lat)s, 4326)"
        parms["min_lng"] = min_lng
        parms["min_lat"] = min_lat
        parms["max_lng"] = max_lng
        parms["max_lat"] = max_lat

    if lat:
        # fully contains?
        # query += ' AND ST_Contains(ST_Buffer(ST_SetSRID(ST_MakePoint(%(lng)s, %(lat)s), 4326)::geography, %(radius)s / 100.0)::geometry, geometry::geometry)'
        # Or just intersects?
        query += " AND ST_Intersects(ST_Buffer(ST_SetSRID(ST_MakePoint(%(lng)s, %(lat)s), 4326)::geography, %(radius)s / 100.0), geometry::geography)"
        parms["lng"] = lng
        parms["lat"] = lat
        parms["radius"] = radius

    if time:
        query += " AND COALESCE(start_date <= TO_TIMESTAMP(%(time)s / 1000.0), TRUE) AND COALESCE(end_date >= TO_TIMESTAMP(%(time)s / 1000.0), TRUE)"
        parms["time"] = time

    query += " ORDER BY curb_zone_id LIMIT %(limit)s OFFSET %(offset)s"
    parms["limit"] = limit
    parms["offset"] = offset

    with get_engine().connect() as conn:
        df = pd.read_sql(query, conn, params=parms)

    if not include_geometry:
        df = df.drop(columns=["geometry"])

    return {
        **RESPONSE_DEFAULT_PARMS,
        "limit": limit,
        "offset": offset,
        "data": {
            "zones": json.loads(df.to_json(orient="records", default_handler=str))
        },
    }


# Example request: /curbs/zones/a5378455-baae-57e4-a76a-6e17925c52bb
# Example request: /curbs/zones/a5378455-baae-57e4-a76a-6e17925c52bb?time=1765498738000
@app.get(
    "/curbs/zones/{id}",
    tags=["Zones"],
    summary="Get a curb zone",
    response_model=ZoneResponse,
    response_model_exclude_unset=True,
)
async def fetch_curb_zone(
    id: Annotated[uuid.UUID, Path(description="Curb zone ID.")],
    time: Annotated[
        int | None,
        Query(
            description="Only return the zone if valid at this time (milliseconds since the Unix epoch)."
        ),
    ] = None,
    show_historic: Annotated[
        bool, Query(description="Accepted but currently ignored.")
    ] = False,
):
    """Return a single curb zone by ID.

    An unknown ID (or a zone not valid at `time`) currently produces a server error rather than a 404.
    """

    # TODO: show_historic??

    query = f"""
        SELECT
            curb_zone_id,
            geometry_json::JSON AS geometry,
            curb_policy_ids,
            published_date,
            last_updated_date,
            start_date,
            end_date,
            name,
            description,
            jurisdiction_type,
            owner_name,
            user_zone_id,
            street_name,
            address_number,
            cross_street_start_name,
            length,
            available,
            available_space_lengths,
            availability_time,
            width,
            parking_angle,
            num_spaces,
            street_side,
            median,
            entire_roadway
        FROM {ZONES_VIEW}
        WHERE curb_zone_id = %(id)s"""
    parms = {"id": id}

    if time:
        query += " AND COALESCE(start_date <= TO_TIMESTAMP(%(time)s / 1000.0), TRUE) AND COALESCE(end_date >= TO_TIMESTAMP(%(time)s / 1000.0), TRUE)"
        parms["time"] = time

    with get_engine().connect() as conn:
        df = pd.read_sql(query, conn, params=parms)

    return {
        **RESPONSE_DEFAULT_PARMS,
        "data": json.loads(df.to_json(orient="records", default_handler=str))[0],
    }


# Example request: /curbs/policies
# Example request: /curbs/policies?ids=0076db6b-7ff1-5aa8-98e0-b36548ace1ca,007b3f23-83b9-51ce-8983-83dc03ebee71
@app.get(
    "/curbs/policies",
    tags=["Policies"],
    summary="Query curb policies",
    response_model=PoliciesResponse,
    response_model_exclude_unset=True,
)
async def query_curb_policies(
    ids: Annotated[
        str | None,
        Query(description="Comma-separated policy IDs. Omit to return all policies."),
    ] = None,
):
    """Return all curb policies, or only those listed in `ids`."""
    query = f"""
        SELECT
            curb_policy_id,
            name,
            description,
            published_date,
            priority,
            rules,
            time_spans,
            policy_color, 
            rates
        FROM {POLICIES_VIEW}
        WHERE 1=1"""
    parms = {}

    if ids:
        query += " AND curb_policy_id IN %(ids)s"
        parms["ids"] = tuple(ids.split(","))

    with get_engine().connect() as conn:
        df = pd.read_sql(query, conn, params=parms)

    return {
        **RESPONSE_DEFAULT_PARMS,
        "data": {
            "policies": json.loads(df.to_json(orient="records", default_handler=str))
        },
    }


# Example request: /curbs/policies/0076db6b-7ff1-5aa8-98e0-b36548ace1ca
@app.get(
    "/curbs/policies/{id}",
    tags=["Policies"],
    summary="Get a curb policy",
    response_model=PolicyResponse,
    response_model_exclude_unset=True,
)
async def fetch_curb_policy(id: Annotated[uuid.UUID, Path(description="Policy ID.")]):
    """Return a single curb policy by ID.

    An unknown ID currently produces a server error rather than a 404.
    """
    query = f"""
        SELECT
            curb_policy_id,
            name,
            description,
            published_date,
            priority,
            rules,
            time_spans,
            policy_color, 
            rates
        FROM {POLICIES_VIEW}
        WHERE curb_policy_id = %(id)s"""
    parms = {"id": id}

    with get_engine().connect() as conn:
        df = pd.read_sql(query, conn, params=parms)

    return {
        **RESPONSE_DEFAULT_PARMS,
        "data": json.loads(df.to_json(orient="records", default_handler=str))[0],
    }
