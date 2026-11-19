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

!!! note
    `last_updated` is currently a hardcoded value, not the real refresh time.
