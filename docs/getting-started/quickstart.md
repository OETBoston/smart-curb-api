# Quickstart

Fetch zones inside a bounding box, without geometry:

```bash
curl "$BASE_URL/curbs/zones?min_lng=-71.0524&min_lat=42.3395&max_lng=-71.0470&max_lat=42.3416&include_geometry=false"
```

Fetch a single zone and its policy:

```bash
curl "$BASE_URL/curbs/zones/a5378455-baae-57e4-a76a-6e17925c52bb"
curl "$BASE_URL/curbs/policies/0076db6b-7ff1-5aa8-98e0-b36548ace1ca"
```

<!-- TODO: replace example IDs with ones from production data; confirm BASE_URL -->
