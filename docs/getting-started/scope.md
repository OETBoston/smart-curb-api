# Scope and Data Coverage

## Current dataset

The first dataset in the Curbs API contains **street sweeping regulations for the City of Boston**, formatted according to the [Curb Data Specification (CDS)](https://github.com/openmobilityfoundation/curb-data-specification). Each record describes a restriction a street sign communicates, including:

- **Days of the week** when the restriction applies
- **Time windows** within those days
- **Months** of the year in effect
- **Seasonal periods**, where a restriction applies only during part of the year

Records are derived from the regulations posted on signs. They don’t include restrictions that aren’t signed.

## Geographic coverage
Coverage is limited to **City-managed streets**, as defined in the [City of Boston Managed Streets dataset](https://data.boston.gov/dataset/city-of-boston-managed-streets). Coverage does not include:

- **Privately owned rights-of-way**, such as private roads, driveways, and private parking lots
- **State roads and highways**, which are under state jurisdiction

A location outside this coverage returns no records. **No records does not mean there are no restrictions**. Applications should not treat an empty response as permission to park, stop, or otherwise use a space. Check signage on site, and make clear to users when a location is outside coverage.

## Planned additions
The City plans to expand coverage over the coming months to include:

- **Parking meter locations and rates**
- **Resident parking zones**
- **Snow emergency zones**

These additions will be released citywide and may add new curb zones to the existing dataset. Announcements will be made through the Curb Lab newsletter.

## Known limitations
Data quality varies by use case and location. Records may be incomplete, out of date, or incorrect. See **Data quality and feedback** for how to report issues.
