# Policies and rules

Each zone lists `curb_policy_ids`. Resolve them with `GET /curbs/policies?ids=a,b` or `GET /curbs/policies/{id}`. A policy carries `rules`, `time_spans`, `rates`, a `priority` and a `policy_color`.

See the [CDS Curbs spec](../CURBS.md) for the meaning of rule fields.

<!-- TODO: worked example resolving "can I park here at 3pm Tuesday?" -->
