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

## Notes

- Script is read-only and do not modify data.
- Additional views or helper queries may be added over time to simplify reporting.
