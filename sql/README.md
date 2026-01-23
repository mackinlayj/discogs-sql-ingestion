# SQL Utilities & Validation

This folder contains a SQL query used to validate, explore, and support the Discogs data after it has been ingested into SQL Server.

This basic script is intended for:
- Sanity checks after ETL runs
- Quick data exploration
- Supporting downstream analytics (e.g., Power BI)
This script is easily adaptable and can modified to include additional or omit fields as needed.

---

## Included Script

### `sanity-check-collection.sql`

A lightweight validation query that joins key tables to confirm that the ETL process completed successfully.

This query:
- Verifies that releases were ingested
- Confirms artist and genre relationships
- Displays recent collection activity
- Formats fields for easy human inspection

Recommended usage:
- Run immediately after an ETL run
- Run before refreshing Power BI datasets

---

## Usage

Run scripts directly in:
- SQL Server Management Studio (SSMS)
- Azure Data Studio
- VS Code SQL extensions

All scripts assume:
- Tables exist in the `dbo` schema
- The database was created and populated by the ETL pipeline in `src/`

---

## Available Data & Customization

The SQL tables in this project are populated directly from the Discogs API and are designed to expose the majority of the metadata that Discogs provides for a user's collection. The included query (e.g., the sanity check script) are intentionally conservative and meant only as an example. 

Users are encouraged to modify or extend these queries to surface any attributes relevant to their own analysis/curiosity. 

---

## Core Tables & Columns

Below is a high-level overview of the main tables and example columns available for querying. This is not an exhaustive list, but highlight the most commonly used fields (you can view the SQL tables directly from the Management Studio Application for easy lookup).

`dbo.discogs_release`
Represents unique Discogs releases.

Common columns include:
- release_id
- title
- year
- country
- released (release date as provided by Discogs)
- thumb_url
- cover_url
- resource_url
- last_updated_utc

`dbo.discogs_collection_item`
Represents items in the authenticated user's collection.

Common columns include:
- collection_instance_id
- release_id
- folder_id
- date_added
- rating
- notes (stored as JSON text)
- last_updated_utc

`dbo.discogs_artist`
Represents artists associated with releases.

Common columns include:
- artist_id
- name

`dbo.discogs_release_artist`
Bridge table linking releases and artists, includintg role metadata.

Common columns include:
- artist_id
- release_id
- role (e.g., main artist, remix, producer)
- join_text
- anv (artist name variation)

Genre & Style Tables
Genres and styles are modeled as normalized dimensions.
- `dbo.discogs_genre`
- `dbo.discogs_style`
- `dbo.discogs_release_genre`
- `dbo.discogs_release_style`

These tables allow releases to be associated with multiple genres and styles.

---

## Customizing Queries

The SQL script in this folder is intended to be a starting point, not fixed outputs.

You can easily:
- Add or remove columns from `SELECT` statements
- Join additional tables to enrich results
- Aggregate data differently (e.g., counts by genre, artists per year)\
- Create views to simplify Power BI models

For example:
- Want artist roles? Join discogs_release_artist
- Want acquisition trends? Use date_added
- Want genre distributions? Join discogs_release_genre

Because the ETL process normalizes Discogs' nested API responses into relational tables, most analyses can be accomplished using straightforward SQL joins.

## Notes & Assumptions

- Discogs metadata is user-generated and may contain inconsistencies or missing values.
- Not all releases will have complete information for every column.
- Column availability ultimately depends on what Discogs returns for a given release.
