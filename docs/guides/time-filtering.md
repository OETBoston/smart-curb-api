# Time filtering

`time` is milliseconds since the Unix epoch. Only zones whose `start_date`/`end_date` window contains that instant are returned; a null `start_date` or `end_date` is treated as unbounded. Data times are in `US/Eastern`.

<!-- TODO: explain how policy time_spans differ from zone validity -->
