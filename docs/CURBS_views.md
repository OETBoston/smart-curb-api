# Database Views: Curbs API

The PostgreSQL database converts curb data into a two views that are designed to support
an API allowing viewing of CURB data. Two options are presented, one performing more JSON
conversion in the database, the other requiring JSON conversion to happen in the API.

## View: vw_curb_zones

| Column Name             | Data Type             | Notes                            |
| ----------------------- | --------------------- | -------------------------------- |
| curb_zone_id            | UUID (PRIMARY KEY)    |                                  |
| geometry                | GEOGRAPHY(LineString) |                                  |
| curb_policy_ids         | UUID[]                | Filled from `curb_zone_policies` |
| published_date          | TIMESTAMP             |                                  |
| last_updated_date       | TIMESTAMP             |                                  |
| start_date              | TIMESTAMP             |                                  |
| end_date                | TIMESTAMP             |                                  |
| name                    | VARCHAR               |                                  |
| description             | TEXT                  |                                  |
| jurisdiction_type       | VARCHAR               |                                  |
| owner_name              | VARCHAR               |                                  |
| user_zone_id            | VARCHAR               |                                  |
| street_name             | VARCHAR               |                                  |
| address_number          | VARCHAR               |                                  |
| cross_street_start_name | VARCHAR               |                                  |
| length                  | INTEGER               |                                  |
| available               | BOOLEAN               |                                  |
| available_space_lengths | INTEGER[]             |                                  |
| availability_time       | TIMESTAMP             |                                  |
| width                   | INTEGER               |                                  |
| parking_angle           | VARCHAR               |                                  |
| num_spaces              | INTEGER               |                                  |
| street_side             | VARCHAR               |                                  |
| median                  | BOOLEAN               |                                  |
| entire_roadway          | BOOLEAN               |                                  |

### Alternate Approach

An alternate approach is to minimize the table data in the view, with each record containing
relevant information already packaged into json format. Such a table would be structured
as follows.

| Column Name  | Data Type             | Notes                                                          |
| ------------ | --------------------- | -------------------------------------------------------------- |
| curb_zone_id | UUID (PRIMARY KEY)    |                                                                |
| geometry     | GEOGRAPHY(LineString) | Included to facilitate lookups and duplicated in `curb_object` |
| curb_object  | JSONB                 | Contains the json data to be returned via the API              |

## View: vw_curb_policies

| Column Name    | Data Type          | Notes                                          |
| -------------- | ------------------ | ---------------------------------------------- |
| curb_policy_id | UUID (PRIMARY KEY) |                                                |
| name           | VARCHAR            |                                                |
| description    | VARCHAR            |                                                |
| published_date | TIMESTAMP          |                                                |
| priority       | INTEGER            |                                                |
| rules          | JSONB              | Filled from the `curb_policy_rules` table      |
| time_spans     | JSONB              | Filled from the `curb_policy_time_spans` table |
| policy_color   | JSONB              | Filled from the `curb_policy_colors` table     |

### Alternate Approach

An alternate approach is to minimize the table data in the view, with each record containing
relevant information already packaged into json format. Such a table would be structured
as follows.

| Column Name    | Data Type          | Notes                                              |
| -------------- | ------------------ | -------------------------------------------------- |
| curb_policy_id | UUID (PRIMARY KEY) |                                                    |
| policy_object  | JSONB              | Contains the json data to be returned via the API. |
