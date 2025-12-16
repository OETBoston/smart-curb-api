# Curb Data Specification: Curbs API

This document defines the database specification implemented to support the Curbs API
as implemented for the City of Boston SMART Grant. This database is designed to be
extensible and generic, minimizing any dependency on Boston-specific datasets or
implementation details.

The database is intended to be implemented in PostGIS, which allows for querying
data using a bounding box or point and radius as required by the CDS API.

## Database Tables

### curb_zones

| Column Name             | Type                  | Spec Required |
| ----------------------- | --------------------- | ------------- |
| curb_zone_id            | UUID (PRIMARY KEY)    | Y             |
| geometry                | GEOGRAPHY(LINESTRING) | Y             |
| published_date          | TIMESTAMP             | Y             |
| last_updated_date       | TIMESTAMP             | Y             |
| start_date              | TIMESTAMP             | Y             |
| end_date                | TIMESTAMP             | N             |
| name                    | VARCHAR               | N             |
| description             | TEXT                  | N             |
| jurisdiction_type       | VARCHAR               | N             |
| owner_name              | VARCHAR               | N             |
| user_zone_id            | VARCHAR               | N             |
| street_name             | VARCHAR               | N             |
| address_number          | VARCHAR               | N             |
| cross_street_start_name | VARCHAR               | N             |
| length                  | INTEGER               | N             |
| available               | BOOLEAN               | N             |
| available_space_lengths | INTEGER[]             | N             |
| availability_time       | TIMESTAMP             | N             |
| width                   | INTEGER               | N             |
| parking_angle           | VARCHAR               | N             |
| num_spaces              | INTEGER               | N             |
| street_side             | VARCHAR               | N             |
| median                  | BOOLEAN               | N             |
| entire_roadway          | BOOLEAN               | N             |

### curb_policies

| Column Name     | Type               | Spec Required |
| --------------- | ------------------ | ------------- |
| curb_policy_id  | UUID (PRIMARY KEY) | Y             |
| name            | VARCHAR            | N             |
| description     | TEXT               | N             |
| published_date  | TIMESTAMP          | Y             |
| priority        | INTEGER            | Y             |
| policy_color_id | UUID (FOREIGN KEY) | N             |

### curb_zone_policies

| Column Name    | Type | Spec Required |
| -------------- | ---- | ------------- |
| curb_zone_id   | UUID | Y             |
| curb_policy_id | UUID | Y             |

### curb_policy_rules

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
