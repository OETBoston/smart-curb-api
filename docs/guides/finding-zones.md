# Finding zones

`GET /curbs/zones` supports two spatial filters:

- **Bounding box**: `min_lat`, `min_lng`, `max_lat`, `max_lng` (all four or none).
- **Radius**: `lat`, `lng`, `radius` (all three or none). `radius` is in **centimeters**.

Partial sets return `400`. A value of `0` is treated as missing. Use `include_geometry=false` for lighter responses.

<!-- TODO: behaviour when both filters are given; zone vs. street-side semantics; map screenshot -->
