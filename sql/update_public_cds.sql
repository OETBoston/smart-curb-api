
BEGIN;

-- Move public_cds to public_cds_previous
TRUNCATE TABLE IF EXISTS public_cds_previous.curb_policy_rates CASCADE;
TRUNCATE TABLE IF EXISTS public_cds_previous.curb_policy_time_spans CASCADE;
TRUNCATE TABLE IF EXISTS public_cds_previous.curb_policy_rules CASCADE;
TRUNCATE TABLE IF EXISTS public_cds_previous.curb_zone_policies CASCADE;
TRUNCATE TABLE IF EXISTS public_cds_previous.curb_policies CASCADE;
TRUNCATE TABLE IF EXISTS public_cds_previous.curb_policy_colors CASCADE;
TRUNCATE TABLE IF EXISTS public_cds_previous.curb_zones CASCADE;

INSERT INTO public_cds_previous.curb_zones(
    curb_zone_id,
    geometry,
    published_date,
    last_updated_date,
    start_date,
    end_date,
    name,
    description,
    jurisdiction_type,
    owner_name,
    user_zone_id,
    street_name,
    address_number,
    cross_street_start_name,
    length,
    available,
    available_space_lengths,
    availability_time,
    width,
    parking_angle,
    num_spaces,
    street_side,
    median,
    entire_roadway
)
select curb_zone_id,
    geometry,
    published_date,
    last_updated_date,
    start_date,
    end_date,
    name,
    description,
    jurisdiction_type,
    owner_name,
    user_zone_id,
    street_name,
    address_number,
    cross_street_start_name,
    length,
    available,
    available_space_lengths,
    availability_time,
    width,
    parking_angle,
    num_spaces,
    street_side,
    median,
    entire_roadway
from public_cds.curb_zones;

INSERT INTO public_cds_previous.curb_policy_colors(
    color_id,
    primary_color,
    primary_pattern_type,
    primary_border_color,
    primary_border_pattern_type,
    secondary_color,
    secondary_border_color,
    secondary_border_pattern_type
)
select color_id,
    primary_color,
    primary_pattern_type,
    primary_border_color,
    primary_border_pattern_type,
    secondary_color,
    secondary_border_color,
    secondary_border_pattern_type
from public_cds.curb_policy_colors;


INSERT INTO public_cds_previous.curb_policies(
    curb_policy_id,
    name,
    description,
    published_date,
    priority,
    policy_color_id
)
select
    curb_policy_id,
    name,
    description,
    published_date,
    priority,
    policy_color_id
from public_cds.curb_policies;

INSERT INTO public_cds_previous.curb_zone_policies(curb_zone_id, curb_policy_id)
select curb_zone_id, curb_policy_id
from public_cds.curb_zone_policies;

INSERT INTO public_cds_previous.curb_policy_rules(
    rule_id,
    curb_policy_id,
    name,
    description,
    activity,
    max_stay,
    max_stay_unit,
    no_return,
    no_return_unit,
    user_classes,
    user_classes_except,
    purposes
)
select rule_id,
    curb_policy_id,
    name,
    description,
    activity,
    max_stay,
    max_stay_unit,
    no_return,
    no_return_unit,
    user_classes,
    user_classes_except,
    purposes
from public_cds.curb_policy_rules;

INSERT INTO public_cds_previous.curb_policy_time_spans(
    time_span_id,
    curb_policy_id,
    start_date,
    end_date,
    days_of_week,
    days_of_month,
    weeks_of_month,
    months,
    time_of_day_start,
    time_of_day_end,
    designated_period,
    designated_period_except
)
select time_span_id,
    curb_policy_id,
    start_date,
    end_date,
    days_of_week,
    days_of_month,
    weeks_of_month,
    months,
    time_of_day_start,
    time_of_day_end,
    designated_period,
    designated_period_except
from public_cds.curb_policy_time_spans;

INSERT INTO public_cds_previous.curb_policy_rates(
    rate_id,
    curb_policy_id,
    rate_amount,
    rate_unit,
    currency,
    time_span_id
)
select
    rate_id,
    curb_policy_id,
    rate_amount,
    rate_unit,
    currency,
    time_span_id
from public_cds.curb_policy_rates;

TRUNCATE TABLE IF EXISTS public_cds.curb_policy_rates CASCADE;
TRUNCATE TABLE IF EXISTS public_cds.curb_policy_time_spans CASCADE;
TRUNCATE TABLE IF EXISTS public_cds.curb_policy_rules CASCADE;
TRUNCATE TABLE IF EXISTS public_cds.curb_zone_policies CASCADE;
TRUNCATE TABLE IF EXISTS public_cds.curb_policies CASCADE;
TRUNCATE TABLE IF EXISTS public_cds.curb_policy_colors CASCADE;
TRUNCATE TABLE IF EXISTS public_cds.curb_zones CASCADE;

-- Move public_cds_next to public_cds
INSERT INTO public_cds.curb_zones(
    curb_zone_id,
    geometry,
    published_date,
    last_updated_date,
    start_date,
    end_date,
    name,
    description,
    jurisdiction_type,
    owner_name,
    user_zone_id,
    street_name,
    address_number,
    cross_street_start_name,
    length,
    available,
    available_space_lengths,
    availability_time,
    width,
    parking_angle,
    num_spaces,
    street_side,
    median,
    entire_roadway
)
select curb_zone_id,
    geometry,
    published_date,
    last_updated_date,
    start_date,
    end_date,
    name,
    description,
    jurisdiction_type,
    owner_name,
    user_zone_id,
    street_name,
    address_number,
    cross_street_start_name,
    length,
    available,
    available_space_lengths,
    availability_time,
    width,
    parking_angle,
    num_spaces,
    street_side,
    median,
    entire_roadway
from public_cds_next.curb_zones;

INSERT INTO public_cds.curb_policy_colors(
    color_id,
    primary_color,
    primary_pattern_type,
    primary_border_color,
    primary_border_pattern_type,
    secondary_color,
    secondary_border_color,
    secondary_border_pattern_type
)
select color_id,
    primary_color,
    primary_pattern_type,
    primary_border_color,
    primary_border_pattern_type,
    secondary_color,
    secondary_border_color,
    secondary_border_pattern_type
from public_cds_next.curb_policy_colors;


INSERT INTO public_cds.curb_policies(
    curb_policy_id,
    name,
    description,
    published_date,
    priority,
    policy_color_id
)
select
    curb_policy_id,
    name,
    description,
    published_date,
    priority,
    policy_color_id
from public_cds_next.curb_policies;

INSERT INTO public_cds.curb_zone_policies(curb_zone_id, curb_policy_id)
select curb_zone_id, curb_policy_id
from public_cds_next.curb_zone_policies;

INSERT INTO public_cds.curb_policy_rules(
    rule_id,
    curb_policy_id,
    name,
    description,
    activity,
    max_stay,
    max_stay_unit,
    no_return,
    no_return_unit,
    user_classes,
    user_classes_except,
    purposes
)
select rule_id,
    curb_policy_id,
    name,
    description,
    activity,
    max_stay,
    max_stay_unit,
    no_return,
    no_return_unit,
    user_classes,
    user_classes_except,
    purposes
from public_cds_next.curb_policy_rules;

INSERT INTO public_cds.curb_policy_time_spans(
    time_span_id,
    curb_policy_id,
    start_date,
    end_date,
    days_of_week,
    days_of_month,
    weeks_of_month,
    months,
    time_of_day_start,
    time_of_day_end,
    designated_period,
    designated_period_except
)
select time_span_id,
    curb_policy_id,
    start_date,
    end_date,
    days_of_week,
    days_of_month,
    weeks_of_month,
    months,
    time_of_day_start,
    time_of_day_end,
    designated_period,
    designated_period_except
from public_cds_next.curb_policy_time_spans;

INSERT INTO public_cds.curb_policy_rates(
    rate_id,
    curb_policy_id,
    rate_amount,
    rate_unit,
    currency,
    time_span_id
)
select
    rate_id,
    curb_policy_id,
    rate_amount,
    rate_unit,
    currency,
    time_span_id
from public_cds_next.curb_policy_rates;

-- Clear out public_cds_next for next update
TRUNCATE TABLE IF EXISTS public_cds_next.curb_policy_rates CASCADE;
TRUNCATE TABLE IF EXISTS public_cds_next.curb_policy_time_spans CASCADE;
TRUNCATE TABLE IF EXISTS public_cds_next.curb_policy_rules CASCADE;
TRUNCATE TABLE IF EXISTS public_cds_next.curb_zone_policies CASCADE;
TRUNCATE TABLE IF EXISTS public_cds_next.curb_policies CASCADE;
TRUNCATE TABLE IF EXISTS public_cds_next.curb_policy_colors CASCADE;
TRUNCATE TABLE IF EXISTS public_cds_next.curb_zones CASCADE;

COMMIT;