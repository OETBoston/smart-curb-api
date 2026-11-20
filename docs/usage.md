# Curbs API usage guide

## Getting zones
A [Curb Zone](reference/cds.md#curb-zone) is a contiguous region of curb space on a single block face that is regulated in a particular way.


Use `GET /v1/curbs/zones` to retrieve curb zones. A call without parameters will return all available curb zones. This call supports two spatial filters:

- **Bounding box**: `min_lat`, `min_lng`, `max_lat`, `max_lng` (all four or none).
- **Radius**: `lat`, `lng`, `radius` (all three or none). `radius` is in **centimeters**.
- 
Partial sets return `400`. A value of `0` is treated as missing. Use `include_geometry=false` for lighter responses.

Use `GET /v1/curbs/zones/{id}` to retrieve a single curb zone by ID.

<!-- TODO: behaviour when both filters are given; zone vs. street-side semantics; map screenshot -->

## Getting policies and rules

A [Curb Policy](reference/cds.md#policy) A Policy is a rule that allows or prohibits a particular set of users from using a particular curb at a particular time or times

Each zone lists `curb_policy_ids`. Resolve them with `GET /v1/curbs/policies?ids=a,b` or `GET /v1/curbs/policies/{id}`. A policy carries `rules`, `time_spans`, `rates`, a `priority` and a `policy_color`.

See the [CDS Curbs spec](reference/cds.md) for the meaning of rule fields.

<!-- TODO: worked example resolving "can I park here at 3pm Tuesday?" -->

## Time filtering

`time` is milliseconds since the Unix epoch. Only zones whose `start_date`/`end_date` window contains that instant are returned; a null `start_date` or `end_date` is treated as unbounded. Data times are in `US/Eastern`.

<!-- TODO: explain how policy time_spans differ from zone validity -->

# Response envelope

Every successful response includes:

| Field | Example | Meaning |
| ----- | ------- | ------- |
| `version` | `1.0` | CDS Curbs spec version |
| `time_zone` | `US/Eastern` | Time zone of the data |
| `last_updated` | `1767565837844` | Last data update (epoch ms) |
| `currency` | `USD` | Currency for rates |
| `author` | `City of Boston` | Publisher |
| `data` | | The payload |


# Errors

Errors use FastAPI's `{"detail": ...}` shape.

| Status | When |
| ------ | ---- |
| 400 | Incomplete bounding box or radius parameters |
| 422 | A parameter fails validation (e.g. malformed UUID) |
| 500 | Unknown zone or policy ID (known issue; should be 404) |

<!-- TODO: update once the 404 fix lands -->