# Errors

Errors use FastAPI's `{"detail": ...}` shape.

| Status | When |
| ------ | ---- |
| 400 | Incomplete bounding box or radius parameters |
| 422 | A parameter fails validation (e.g. malformed UUID) |
| 500 | Unknown zone or policy ID (known issue; should be 404) |

<!-- TODO: update once the 404 fix lands -->
