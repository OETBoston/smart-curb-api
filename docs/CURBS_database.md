# Database Specification: Curbs API

This document defines the database specification implemented to support the Curbs API
as implemented for the City of Boston SMART Grant. This database is designed to be
extensible and generic, minimizing dependency on Boston-specific datasets or
implementation details.

The database is intended to be implemented in PostGIS, which allows for querying
data using a bounding box or point and radius as required by the CDS API.

## Database Tables

### curb_zones

This table defines the physical properties of each zone. Associated policies are defined in a subsequent table.

Only a few of the fields will be populated during initial database development under the SMART grant. Fields
listed as not being populated will be included in the database, but will not yetr include any data.
This will allow future addition of data to theise fields.

| Column Name             | Type                  | Spec Required | Populated |
| ----------------------- | --------------------- | ------------- | --------- |
| curb_zone_id            | UUID (PRIMARY KEY)    | Y             | Y         |
| geometry                | GEOGRAPHY(LINESTRING) | Y             | Y         |
| published_date          | TIMESTAMP             | Y             | Y         |
| last_updated_date       | TIMESTAMP             | Y             | Y         |
| start_date              | TIMESTAMP             | Y             | Y         |
| end_date                | TIMESTAMP             | N             | Y         |
| name                    | VARCHAR               | N             | N         |
| description             | TEXT                  | N             | N         |
| jurisdiction_type       | VARCHAR               | N             | N         |
| owner_name              | VARCHAR               | N             | N         |
| user_zone_id            | VARCHAR               | N             | N         |
| street_name             | VARCHAR               | N             | N         |
| address_number          | VARCHAR               | N             | N         |
| cross_street_start_name | VARCHAR               | N             | N         |
| length                  | INTEGER               | N             | N         |
| available               | BOOLEAN               | N             | N         |
| available_space_lengths | INTEGER[]             | N             | N         |
| availability_time       | TIMESTAMP             | N             | N         |
| width                   | INTEGER               | N             | N         |
| parking_angle           | VARCHAR               | N             | N         |
| num_spaces              | INTEGER               | N             | N         |
| street_side             | VARCHAR               | N             | N         |
| median                  | BOOLEAN               | N             | N         |
| entire_roadway          | BOOLEAN               | N             | N         |

### curb_policies

This table defines each policy and is referenced by the `curb_zones` table.

| Column Name     | Type               | Spec Required | Populated |
| --------------- | ------------------ | ------------- | --------- |
| curb_policy_id  | UUID (PRIMARY KEY) | Y             | Y         |
| name            | VARCHAR            | N             | Y         |
| description     | TEXT               | N             | Y         |
| published_date  | TIMESTAMP          | Y             | Y         |
| priority        | INTEGER            | Y             | Y         |
| policy_color_id | UUID (FOREIGN KEY) | N             | N         |

### curb_zone_policies

This join table links curb zones and policies.

| Column Name    | Type | Spec Required |
| -------------- | ---- | ------------- |
| curb_zone_id   | UUID | Y             |
| curb_policy_id | UUID | Y             |

### curb_policy_rules

This table lists each rule associated with each policy. Although all fields
are populated, some will be left blank except in cases where the sign reader identifies
relevant information.

| Column Name         | Type               | Spec Required |
| ------------------- | ------------------ | ------------- |
| rule_id             | UUID (PRIMARY KEY) | Y             |
| curb_policy_id      | UUID (FOREIGN KEY) | Y             |
| name                | VARCHAR            | N             |
| description         | TEXT               | N             |
| activity            | VARCHAR            | N             |
| max_stay            | INTEGER            | N             |
| no_return           | INTEGER            | N             |
| no_return_unit      | VARCHAR            | N             |
| user_classes        | TEXT[]             | N             |
| user_classes_except | TEXT[]             | N             |
| purposes            | TEXT[]             | N             |

### curb_policy_time_spans

This table lists each timespan associated with each policy.

| Column Name              | Type               | Spec Required |
| ------------------------ | ------------------ | ------------- |
| time_span_id             | UUID (PRIMARY KEY) | Y             |
| curb_policy_id           | UUID (FOREIGN KEY) | Y             |
| start_date               | TIMESTAMP          | N             |
| end_date                 | TIMESTAMP          | N             |
| days_of_week             | VARCHAR[]          | N             |
| days_of_month            | INTEGER[]          | N             |
| weeks_of_month           | INTEGER[]          | N             |
| months                   | INTEGER[]          | N             |
| time_of_day_start        | VARCHAR            | N             |
| time_of_day_end          | VARCHAR            | N             |
| designated_period        | VARCHAR            | N             |
| designated_period_except | BOOLEAN            | N             |
