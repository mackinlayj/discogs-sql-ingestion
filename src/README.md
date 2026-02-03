# Source Code (ETL)

This folder contains the Python source code responsible for extracting data from the Discogs API, transforming it into relational structures, and loading it into SQL Server.

---

## Main Script

### discogs_to_sql.py

This script performs the full end-to-end ETL process:

1. Loads configuration from environment variables (`.env`)
2. Authenticates with the Discogs API
3. Retrieves the authenticated user’s full collection with pagination
4. Normalizes nested Discogs JSON into relational entities
5. Creates SQL Server tables if they do not already exist
6. Upserts (MERGE) data into fact and dimension tables

The script is safe to run multiple times and will update existing records without creating duplicates.

---

## Configuration

All configuration is handled via environment variables.  
See .env.template in the ./src folder for required values and documentation.

No credentials or secrets should be committed to source control.

---

## Execution

```bash
python src/discogs_to_sql.py
