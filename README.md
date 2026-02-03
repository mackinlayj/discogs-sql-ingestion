# Discogs Dashboarding Documentation 

## Overview

Discogs provides a built-in web interface for browsing personal collections and wantlists; however, its analytical and customaization capabilities are limited. While basic metrics are available, users have little control over how data is transformed, combined, or reused across projects. 

This repository focuses on building a reproducible Python-based ingestion pipeline that extracts data from the Discogs API, normalizes the nested responses, and persists the results in a relational SQL Server database. The primary goal is to centralize Discogs data in a structured, queryable format that can serve as a reliable foundation for downstream analysis, reporting, or experimentation.

Rather than trying the worflow to a single analytics tool, this project treats SQL Server as the system of record, enabling the data to be reused across multiple contexts (e.g., ad hoc SQL analysis, dashboards, notebooks, etc.)

---

## Architecture Overview

The data pipeline follows a simple and intentional design:

Discogs API → Python → SQL Server 

Each layer has a clearly defined responsibility:
- The Discogs API provides raw, user-scoped metadata
- Python handles extraction, transformation, and normalization
- SQL Server stores curated, analytics-ready tables

While downstream tools such as Power BI can typically connect to the Discogs API, doing so is not considered best practice - especially when dashboards are shared or published.

---

## Components

### 1. Discogs API

Discogs provides authenticated API access that allows users to programmatically retrieve data related to their collection, wantlist, artists, releases, and related metadata. This API serves as the raw data source for the pipeline and supports automated, repeatable extraction.

### 2. Python (Extraction & Transformation)

Python is used to:
- Authenticate and interact with the Discogs API
- Handle pagination and rate limits
- Normalize nested JSON responses into tabular structures
- Perform initial data cleaning and transformations prior to storage

Note: All transformation logic lives in Python.

### 3. SQL Server (Data Storage)

SQL Server is used as the persistent storage layer for transformed Discogs data.

Persisting the data in a relational database provides several benefits:
- Logic is centralized and transparent
- Nested API responses are converted into stable, relational tables
- Data can be queried and reused independently; data models remain stable for downstream reporting

---

## Configuration of Environment Variables (.env)

This project uses environment variables to manage API credentials and database connection details. Secrets are **never committed** to the repo. 

The repository includes a template file located in src/:
- src/.env.template - documents all required environment variables and serves as a starting point for local configuration.

**Note**: Once you have cloned the repo, ensure you add the .env.template file to the .gitignore file. Once this is done, the data you store here will remain locally contained (especially if working with git).

Setup:
1. Copy the template file
     - cp .env.template
2. Populate the .env.template with:
     - Your Discogs personal access token
     - Your Discogs username
     - SQL Server connection details
3. Do not commit .env.template:
     - Add the .env.template file to the .gitignore file (at the repo root) 
     - This ensures credentials remain local and private

The ingestion script automatically loads configuration from the repository root and fails fast with a clear message if required variables are missing.

---

## Getting Started

### Prerequisites
- Python 3.9+
- SQL Server Express
- Discogs API personal access token  
- A Discogs account (a lovingly curated vinyl collection helps)

### Setup (High-Level)
1. Clone the repository
2. Create and activate a Python virtual environment
3. Install required Python dependencies
4. Configure Discogs API credentials via environment variables
5. Run ingestion scripts to populate the SQL database

---

## Using the Data for Downstream Projects

Once ingested, the Discogs data stored in SQL can be reused for a wide range of individual projects, including:
- Ad hoc SQL analysis
- Exploratory notebooks
- Custom applications
- Dashboarding (e.g., Power BI)

### Example - Connecting from Power BI

If you choose to use Power BI for dashboarding efforts:

1. Open Power BI Desktop
2. Select Get Data → SQL Server
3. Enter your SQL Server instance and database
4. Import tables directly or connect to SQL views
5. Refresh data after rerunning the ingestion script

Because Power BI connects to SQL rather than the API, dashboards remain decoupled from extraction logic and benefit from a stable, well-defined schema. This setup also enables refreshes to be automated or scheduled as needed, allowing reports to stay up-to-date as the ingestion pipeline is rerun. For more information on this automated refresh schedules, check out this article by Microsoft: [Data Refresh in Power BI](https://learn.microsoft.com/en-us/power-bi/connect-data/refresh-data).

---

## Data Scope & Assumptions

- This pipeline is designed for personal Discogs accounts
- Discogs metadata is user-generated and may contain inconsistencies
- Data reflects the state of the collection at the time of extraction
- All data ingested belongs solely to the authenticated Discogs user

---

## Additional Context Re: Data Storage

For many personal or small-scale use cases, storing Discogs data in a relational database may seem unnecessary, as the data is largely non-sensitive and could be accessed directly from the Discogs API. This is a fair observation.

However, this project intentionally models the data in SQL Server to reflect best practices in analytics and data engineering, even when working with relatively simple or low-risk datasets. Persisting transformed data provides clear advantages in terms of transparency, reproducibility, and governance, and mirrors how similar pipelines are implemented in production environments.

Users who prefer a lighter-weight workflow may choose to query the Discogs API directly from tools such as Power Query. While suitable for quick exploration, this approach shifts transformation logic into the visualization layer and reduces reuse.

This repository is designed to demonstrate a robust, extensible ingestion pattern that prioritizes clean data modeling while still allowing flexibility for alternative downstream workflows.

