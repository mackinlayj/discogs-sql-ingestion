# Discogs Dashboarding Documentation 

## Overview

Discogs provides a built-in web interface for exploring collection and wantlist data; however, its analytical and customization capabilities are limited. While basic metrics (e.g., collection size or high-level categorizations) are available, users have little control over how data is transformed, combined, or visualized.

This repository documents an end-to-end pipeline for extracting personal Discogs data via the Discogs API, performing structured transformations, storing the cleaned data in a relational database, and creating custom, shareable visualizations in Power BI. The goal is to enable flexible, reproducible, and privacy-conscious analytics beyond what the native Discogs interface supports.

---

## Architecture Overview

The data pipeline follows a simple and intentional design:

Discogs API → Python → SQL Server → Power BI


Each component plays a specific role in ensuring data quality, transparency, and analytical flexibility.

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

Separating extraction and transformation logic from visualization ensures reproducibility and makes the pipeline easier to test, extend, and maintain.

### 3. SQL Server (Data Storage)

SQL Server is used as the persistent storage layer for transformed Discogs data.

Although Power BI is technically capable of making direct API calls, this approach is discouraged for several reasons:
- API-driven dashboards expose raw data structures
- Transformations become opaque and harder to audit
- Shared or published dashboards may unintentionally expose sensitive or unnecessary data

By storing transformed data in SQL Server:
- Business logic is centralized and transparent
- Data models remain stable for downstream reporting
- Power BI consumes only curated, analytics-ready tables

### 4. Power BI (Analytics & Visualization)

Power BI is used to:
- Define metrics and measures
- Build interactive dashboards
- Explore trends across collection attributes (e.g., genres, formats, acquisition timelines)

Because Power BI connects directly to SQL Server, visualizations remain decoupled from data extraction logic, supporting cleaner governance and easier iteration.

---

## Configuration of Environment Variables (.env)

This project uses environment variables to manage API credentials and database connection details. Secrets are **never committed** to the repo. 

At the root of the repository, you will find a file named: .env.template
- This file documents all required environment variables but contains no sensitive values. It serves as a starting point for local configuration.

Setup:
1. Copy the template file
     ```bash
     cp .env.template .env
     ```
2. Populate the .env with:
     - Your Discogs personal access token
     - Your Discogs username
     - SQL Server connection details
3. Do not commit .env:
     - The .env file is intentionally ignored via .gitignore
     - This ensures credentials remain local and private

The ETL script automatically loads configuration from the repository root. If an .env file is present, it is used by default; otherwise, the script will attempt to load the values from .env.template. If required variables are missing, the script fails fast with a clear error message.

---

## Getting Started

### Prerequisites
- Python 3.9+
- SQL Server Express
- Power BI Desktop
- Discogs API personal access token  
- A Discogs account (a lovingly curated vinyl collection helps)

### Setup (High-Level)
1. Clone the repository
2. Create and activate a Python virtual environment
3. Install required Python dependencies
4. Configure Discogs API credentials via environment variables
5. Run ingestion scripts to populate the SQL database
6. Connect Power BI to SQL Server for visualization

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

That said, users who prefer a lighter-weight approach may choose to skip the database layer entirely and make API calls directly from Power Query within Power BI. While this can be suitable for quick exploration or one-off dashboards, it comes with trade-offs around long-term scalability.

This repository is designed to demonstrate a robust, extensible pattern that prioritizes clean data modeling and separation of concerns, while still allowing flexibility for alternative workflows.

