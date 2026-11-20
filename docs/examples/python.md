# Python examples

```python
import requests

r = requests.get(f"{BASE_URL}/v1/curbs/zones", params={"lat": 42.341, "lng": -71.0505, "radius": 3500})
zones = r.json()["data"]["zones"]
```

<!-- TODO: pagination loop, GeoPandas -->
