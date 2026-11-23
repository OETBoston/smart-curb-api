"""Response models for the Curbs API.

Field descriptions follow the CDS Curbs specification (see docs/CURBS.md). Most
fields are optional and loosely typed because the views return NULLs for
attributes the City does not publish.
"""

import uuid
from typing import Annotated, Any

from pydantic import BaseModel, BeforeValidator, ConfigDict, Field, TypeAdapter


def _split_commas(v: Any) -> Any:
    """Turn "a,b" into ["a", "b"], dropping blanks. Non-strings pass through for pydantic to reject."""
    if isinstance(v, str):
        return [p.strip() for p in v.split(",") if p.strip()]
    return v


# Comma-separated query value validated as a list of UUIDs.
PolicyIds = Annotated[list[uuid.UUID], BeforeValidator(_split_commas)]
policy_ids_adapter = TypeAdapter(PolicyIds)


class Envelope(BaseModel):
    """Metadata returned with every successful response."""

    version: str = Field(description="CDS Curbs spec version.", examples=["1.0"])
    time_zone: str = Field(
        description="IANA time zone of local times in the data.",
        examples=["US/Eastern"],
    )
    last_updated: int = Field(
        description="Last data update, in milliseconds since the Unix epoch.",
        examples=[1767565837844],
    )
    currency: str = Field(description="ISO 4217 currency for rates.", examples=["USD"])
    author: str = Field(
        description="Publisher of the data.", examples=["City of Boston"]
    )


class Zone(BaseModel):
    """A curb zone: a section of curb with a geometry and attached policies."""

    model_config = ConfigDict(extra="allow")

    curb_zone_id: str = Field(description="Unique ID of the zone.")
    geometry: dict[str, Any] | None = Field(
        default=None,
        description="GeoJSON geometry. Omitted when `include_geometry=false`.",
    )
    curb_policy_ids: list[str] | None = Field(
        default=None, description="IDs of the policies that apply to this zone."
    )
    published_date: int | str | None = Field(
        default=None, description="When the zone was published."
    )
    last_updated_date: int | str | None = Field(
        default=None, description="When the zone was last updated."
    )
    start_date: int | str | None = Field(
        default=None, description="Start of validity. Null means unbounded."
    )
    end_date: int | str | None = Field(
        default=None, description="End of validity. Null means unbounded."
    )
    name: str | None = Field(default=None, description="Human-readable name.")
    description: str | None = Field(default=None, description="Free-text description.")
    jurisdiction_type: str | None = Field(
        default=None, description="Type of jurisdiction owning the zone."
    )
    owner_name: str | None = Field(default=None, description="Name of the zone owner.")
    user_zone_id: str | None = Field(
        default=None, description="Owner's own identifier for the zone."
    )
    street_name: str | None = Field(default=None, description="Street the zone is on.")
    address_number: str | None = Field(
        default=None, description="Nearest address number."
    )
    cross_street_start_name: str | None = Field(
        default=None, description="Cross street at the start of the zone."
    )
    length: int | None = Field(default=None, description="Length of the zone.")
    available: bool | None = Field(
        default=None, description="Whether the zone currently has availability."
    )
    available_space_lengths: list[int] | None = Field(
        default=None, description="Lengths of the available spaces."
    )
    availability_time: int | str | None = Field(
        default=None, description="When availability was measured."
    )
    width: int | None = Field(default=None, description="Width of the zone.")
    parking_angle: str | None = Field(
        default=None, description="Parking angle, e.g. parallel or angled."
    )
    num_spaces: int | None = Field(
        default=None, description="Number of spaces in the zone."
    )
    street_side: str | None = Field(default=None, description="Side of the street.")
    median: bool | None = Field(
        default=None, description="Whether the zone is on a median."
    )
    entire_roadway: bool | None = Field(
        default=None, description="Whether the zone covers the entire roadway."
    )


class Policy(BaseModel):
    """A curb policy: rules, time spans and rates that apply to zones."""

    model_config = ConfigDict(extra="allow")

    curb_policy_id: str = Field(description="Unique ID of the policy.")
    name: str | None = Field(default=None, description="Human-readable name.")
    description: str | None = Field(default=None, description="Free-text description.")
    published_date: int | str | None = Field(
        default=None, description="When the policy was published."
    )
    priority: int | None = Field(
        default=None, description="Priority when policies overlap. Lower wins."
    )
    rules: Any = Field(
        default=None, description="Rules (activity, user classes, purposes, ...)."
    )
    time_spans: Any = Field(default=None, description="When the policy applies.")
    policy_color: Any = Field(default=None, description="Display color for maps.")
    rates: Any = Field(default=None, description="Pricing, if any.")


class ZoneList(BaseModel):
    zones: list[Zone]


class PolicyList(BaseModel):
    policies: list[Policy]


class ZonesResponse(Envelope):
    limit: int = Field(description="Page size used for this request.")
    offset: int = Field(description="Offset used for this request.")
    data: ZoneList


class ZoneResponse(Envelope):
    data: Zone


class PoliciesResponse(Envelope):
    data: PolicyList


class PolicyResponse(Envelope):
    data: Policy


class ErrorResponse(BaseModel):
    detail: str = Field(description="What went wrong.")
