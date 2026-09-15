import json
import os
import uuid

from fastapi import FastAPI, HTTPException
from fastapi.responses import RedirectResponse
import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware

# TODO: Use Cloud Secret Manager (https://cloud.google.com/secret-manager) instead of env vars
from dotenv import load_dotenv
load_dotenv()
url_object = URL.create(
    drivername="postgresql",
    username=os.environ['DB_USER'],
    password=os.environ['DB_PASS'],
    host=os.environ['DB_HOST'],
    database=os.environ['DB_NAME']
)
ENGINE = create_engine(url_object)

RESPONSE_DEFAULT_PARMS = {
  "version": "1.0",
  "time_zone": "US/Eastern",
  "last_updated": 1767565837844,
  "currency": "USD",
  "author": "City of Boston",
#   "license_url": "https://creativecommons.org/licenses/by/4.0/", # TODO: License type?
}

app = FastAPI()

#schema selection NOT AVAILABLE ON PUBLIC CDS 
ALLOWED_SCHEMAS = {"public_cds", "chinatown_cds", "seaport_cds"}  # add/remove as neighborhoods are in progress

def get_schema(schema: str | None) -> str:
    if schema is None:
        return "public_cds"
    if schema not in ALLOWED_SCHEMAS:
        raise HTTPException(status_code=400, detail=f"Unknown schema: {schema}")
    return schema

# add compression
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    #allow_origins=[
        #"http://localhost:3000",    # For local development
        #"http://localhost:8080",    # Alternative local port
        #"http://localhost:5173",    # Vite default port
        #"https://oetboston.github.io/curb-atlas", # Might not be necessary, we can remove after testing
        #"https://oetboston.github.io",
        # Add your developer's production frontend URL here when you know it
        # "https://their-map-frontend.boston.gov",
    #],
    allow_credentials=True,  # Required for IAP authentication
    allow_methods=["*"],     # Allow all HTTP methods
    allow_headers=["*"],     # Allow all headers including Authorization
)


@app.get("/")
async def redirect_to_docs():
    """Redirect the base URL to the /docs documentation page."""
    return RedirectResponse(url="/docs")

# Example request: /curbs/zones?min_lng=-71.04695320129396&min_lat=42.339482118418005&max_lng=-71.05236053466798&max_lat=42.34163915108597
# Example request: /curbs/zones?lng=-71.05052025698136&lat=42.34100193645163&radius=3500
# Example request: /curbs/zones?include_geometry=false&time=1765498738000
@app.get("/curbs/zones")
async def query_curb_zones(
    area: uuid.UUID = None, # Still need curb_area table
    min_lat: float = None,
    min_lng: float = None,
    max_lat: float = None,
    max_lng: float = None,
    lat: float = None,
    lng: float = None,
    radius: float = None, # centimeters
    include_geometry: bool = True,
    time: int = None, # milliseconds # Is this optional?
    limit: int = 10000,
    offset: int = 0,
    schema: str = None
):

    schema = get_schema(schema)

    if (min_lat or min_lng or max_lat or max_lng) and not (min_lat and min_lng and max_lat and max_lng):
        raise HTTPException(
                status_code=400,
                detail="Either all or none of 4 parameters min_lat, min_lng, max_lat and max_lng must be specified"
            )
    if (lat or lng or radius) and not (lat and lng and radius):
        raise HTTPException(
                status_code=400,
                detail="Either all or none of 3 parameters lat, lng and radius must be specified"
            )
    # TODO: Should we allow both (lat and lng and radius) and (min_lat and min_lng and max_lat and max_lng)?

    query = """
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
        FROM vw_curb_zones
        WHERE 1=1"""
    parms = {}

    # TODO area logic

    if min_lat:
        query += ' AND geometry::geometry && ST_MakeEnvelope(%(min_lng)s, %(min_lat)s, %(max_lng)s, %(max_lat)s, 4326)'
        parms['min_lng'] = min_lng
        parms['min_lat'] = min_lat
        parms['max_lng'] = max_lng
        parms['max_lat'] = max_lat

    if lat:
        # fully contains?
        # query += ' AND ST_Contains(ST_Buffer(ST_SetSRID(ST_MakePoint(%(lng)s, %(lat)s), 4326)::geography, %(radius)s / 100.0)::geometry, geometry::geometry)'
        # Or just intersects?
        query += ' AND ST_Intersects(ST_Buffer(ST_SetSRID(ST_MakePoint(%(lng)s, %(lat)s), 4326)::geography, %(radius)s / 100.0), geometry::geography)'
        parms['lng'] = lng
        parms['lat'] = lat
        parms['radius'] = radius

    if time:
        query += ' AND COALESCE(start_date <= TO_TIMESTAMP(%(time)s / 1000.0), TRUE) AND COALESCE(end_date >= TO_TIMESTAMP(%(time)s / 1000.0), TRUE)'
        parms['time'] = time

    query += ' ORDER BY curb_zone_id LIMIT %(limit)s OFFSET %(offset)s'
    parms['limit'] = limit
    parms['offset'] = offset

    with ENGINE.connect() as conn:
        conn.execute(text(f"SET search_path TO {schema}"))
        df = pd.read_sql(query, conn, params=parms)

    if not include_geometry:
        df = df.drop(columns=['geometry'])

    return {
        **RESPONSE_DEFAULT_PARMS,
        "limit": limit,
        "offset": offset,
        "data": {"zones": json.loads(df.to_json(orient='records', default_handler=str))}
    }


# Example request: /curbs/zones/a5378455-baae-57e4-a76a-6e17925c52bb
# Example request: /curbs/zones/a5378455-baae-57e4-a76a-6e17925c52bb?time=1765498738000
@app.get("/curbs/zones/{id}")
async def fetch_curb_zone(
    id: uuid.UUID,
    time: int = None, # milliseconds # Is this optional?
    show_historic: bool = False, 
    schema: str = None
):

    schema = get_schema(schema)

    # TODO: show_historic??

    query = """
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
        FROM vw_curb_zones
        WHERE curb_zone_id = %(id)s"""
    parms = {'id': id}

    if time:
        query += ' AND COALESCE(start_date <= TO_TIMESTAMP(%(time)s / 1000.0), TRUE) AND COALESCE(end_date >= TO_TIMESTAMP(%(time)s / 1000.0), TRUE)'
        parms['time'] = time

    with ENGINE.connect() as conn:
        conn.execute(text(f"SET search_path TO {schema}"))
        df = pd.read_sql(query, conn, params=parms)

    return {
        **RESPONSE_DEFAULT_PARMS,
        "data": json.loads(df.to_json(orient='records', default_handler=str))[0]
    }


# Example request: /curbs/policies
# Example request: /curbs/policies?ids=0076db6b-7ff1-5aa8-98e0-b36548ace1ca,007b3f23-83b9-51ce-8983-83dc03ebee71
@app.get("/curbs/policies")
async def query_curb_policies(
    ids: str = None, 
    schema: str = None
    ):
    schema = get_schema(schema)

    query = """
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
        FROM vw_curb_policies
        WHERE 1=1"""
    parms = {}

    if ids:
        query += ' AND curb_policy_id IN %(ids)s'
        parms['ids'] = tuple(ids.split(','))

    with ENGINE.connect() as conn:
        conn.execute(text(f"SET search_path TO {schema}"))
        df = pd.read_sql(query, conn, params=parms)

    return {
        **RESPONSE_DEFAULT_PARMS,
        "data": {"policies": json.loads(df.to_json(orient='records', default_handler=str))}
    }


# Example request: /curbs/policies/0076db6b-7ff1-5aa8-98e0-b36548ace1ca
@app.get("/curbs/policies/{id}")
async def fetch_curb_policy(
    id: uuid.UUID,
    schema: str = None):

    schema = get_schema(schema)

    query = """
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
        FROM vw_curb_policies
        WHERE curb_policy_id = %(id)s"""
    parms = {'id': id}

    with ENGINE.connect() as conn:
        conn.execute(text(f"SET search_path TO {schema}"))
        df = pd.read_sql(query, conn, params=parms)

    return {
        **RESPONSE_DEFAULT_PARMS,
        "data": json.loads(df.to_json(orient='records', default_handler=str))[0]
    }