# City of Boston Curbs API

The Curbs API is a public API that provides curb regulation data for the City of Boston, formatted to the Open Mobility Foundation’s Curb Data Specification. It currently covers City-wide street sweeping regulations on City-managed streets, and the City plans to expand it to include all curb regulations the City administers.

Read-only access to Boston's curb zones and curb policies, following the
[CDS Curbs API](reference/cds.md) specification.

- **Zones**: sections of curb with a geometry.
- **Policies**: rules, time spans and rates that apply to zones.

Start with the [Quickstart](#quickstart) for a quick glance of available calls, visit the [User guide](usage.md) for a deeper dive, or jump to the [API reference](reference/api.md).

## Quickstart

Fetch zones inside a bounding box, without geometry:

```bash
curl "{{ base_url }}/v1/curbs/zones?min_lng=-71.0524&min_lat=42.3395&max_lng=-71.0470&max_lat=42.3416&include_geometry=false"
```

Fetch a single zone and its policy:

```bash
curl "{{ base_url }}/v1/curbs/zones/a5378455-baae-57e4-a76a-6e17925c52bb"
curl "{{ base_url }}/v1/curbs/policies/0076db6b-7ff1-5aa8-98e0-b36548ace1ca"
```
## Scope and Data Coverage

### Current dataset

The first dataset in the Curbs API contains **street sweeping regulations for the City of Boston**, formatted according to the [Curb Data Specification (CDS)](https://github.com/openmobilityfoundation/curb-data-specification). Each record describes a restriction a street sign communicates, including:

- **Days of the week** when the restriction applies
- **Time windows** within those days
- **Months** of the year in effect
- **Seasonal periods**, where a restriction applies only during part of the year

Records are derived from the regulations posted on signs. They don’t include restrictions that aren’t signed.

### Geographic coverage
Coverage is limited to **City-managed streets**, as defined in the [City of Boston Managed Streets dataset](https://data.boston.gov/dataset/city-of-boston-managed-streets). Coverage does not include:

- **Privately owned rights-of-way**, such as private roads, driveways, and private parking lots
- **State roads and highways**, which are under state jurisdiction

A location outside this coverage returns no records. **No records does not mean there are no restrictions**. Applications should not treat an empty response as permission to park, stop, or otherwise use a space. Check signage on site, and make clear to users when a location is outside coverage.

### Data freshness and update cadence

Curbs data is currently updated monthly. The City plans to increase the update cadence in the future. Changes to the update schedule will be announced through the Curb Lab newsletter at [newsletter link].

### Planned additions
The City plans to expand coverage over the coming months to include:

- **Parking meter locations and rates**
- **Resident parking zones**
- **Snow emergency zones**

These additions will be released citywide and may add new curb zones to the existing dataset. Announcements will be made through the Curb Lab newsletter.

### Known limitations
Data quality varies by use case and location. Records may be incomplete, out of date, or incorrect. See **Data quality and feedback** for how to report issues.


## Rate limits and quotas

If you are using an API (Application Programming Interface) to source information from a digital City service, we ask that you be mindful of excessive usage (which could slow down service for others). Though there is currently no usage limit, we ask that you let us know if you plan to make heavy use of an API featured on a digital City service (just email <oet@boston.gov>)

## Versioning and change management

The Curbs API uses path-based versioning. The current version is v1, and all endpoints are served under /v1/. For example:

```
https://cds-curb-api.boston.gov/v1/curbs/policies
```
The API implements the [Curb Data Specification (CDS)](https://github.com/openmobilityfoundation/curb-data-specification) from the Open Mobility Foundation (OMF). The current implementation uses CDS version [1.0.1]. Changes to the data structure and endpoints are defined by the CDS, so the City follows OMF’s versioning for those changes.

## Announcements

Changes to the API, its version, and its data coverage are announced through the Curb Lab newsletter. Subscribe at [newsletter link].

## Performance and SLAs

The Curbs API is provided as a public service on a best-effort basis. The City does not currently guarantee uptime, response times, or data availability. Performance may vary, and the API may be unavailable during maintenance or unexpected outages.

Developers are asked to:

- Cache responses where possible, since the underlying data changes at most monthly.
- Avoid repeated requests for the same data.
- Follow the usage guidance in Rate limits and quotas, and notify <digital@boston.gov> before running heavy or sustained workloads.

## Data quality and feedback

Check the data against official City sources before relying on it for decisions that affect people, such as enforcement, permitting, or safety.

If you find an error or have an updated record, please send it to <oet@boston.gov>. Include the location, the value you observed, and a source or photo where you can. Submissions are subject to the Massachusetts Public Records Law, so please don’t include personal information or images that show identifiable people or license plates.  The City reviews submissions before updating the data. Review times vary, and the City can’t guarantee that every submission will be used.

We’re working on ways to make feedback easier and more useful. Updates will be shared through the Curb Lab newsletter at [newsletter link].

## Licensing and terms

The Curbs API data is released under the [Open Data Commons Public Domain Dedication and License (PDDL)](https://opendatacommons.org/licenses/pddl/). You may copy, modify, distribute, and use the data for any purpose, including commercial use, without asking permission. Attribution is not required, but credit to the City of Boston is appreciated and helps support the City’s open data efforts.
These terms apply to the Curbs dataset and API. The [Boston.gov Terms of Use and Privacy Policy](https://www.boston.gov/government/cabinets/innovation-and-technology/terms-use-and-privacy-policy-city-boston-digital) govern use of the City’s websites and digital services.

**Use of City names and marks.** Third-party products and services that use Curbs data must not imply City sponsorship or endorsement. They must not use the City seal, and they must not present non-City services as City services.

**Heavy use.** Heavy API use can slow service for others. If your application will make sustained or high-volume requests, please notify <digital@boston.gov>.

**Contributed data.** Corrections and updates submitted through the [feedback channel] are released under the same PDDL license.

**No warranty.** The data is provided as is, without warranty of accuracy, completeness, or fitness for any purpose. The City is not liable for decisions made using the data.
