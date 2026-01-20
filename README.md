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

### Discogs API

Discogs provides authenticated API access that allows users to programmatically retrieve data related to their collection, wantlist, artists, releases, and related metadata. This API serves as the raw data source for the pipeline and supports automated, repeatable extraction.

---

### Python (Extraction & Transformation)

Python is used to:
- Authenticate and interact with the Discogs API
- Handle pagination and rate limits
- Normalize nested JSON responses into tabular structures
- Perform initial data cleaning and transformations prior to storage

Separating extraction and transformation logic from visualization ensures reproducibility and makes the pipeline easier to test, extend, and maintain.

---

### SQL Server (Data Storage)

SQL Server is used as the persistent storage layer for transformed Discogs data.

Although Power BI is technically capable of making direct API calls, this approach is discouraged for several reasons:
- API-driven dashboards expose raw data structures
- Transformations become opaque and harder to audit
- Shared or published dashboards may unintentionally expose sensitive or unnecessary data

By storing transformed data in SQL Server:
- Business logic is centralized and transparent
- Data models remain stable for downstream reporting
- Power BI consumes only curated, analytics-ready tables

---

### Power BI (Analytics & Visualization)

Power BI is used to:
- Define metrics and measures
- Build interactive dashboards
- Explore trends across collection attributes (e.g., genres, formats, acquisition timelines)

Because Power BI connects directly to SQL Server, visualizations remain decoupled from data extraction logic, supporting cleaner governance and easier iteration.

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
4. Configure Discogs API credentials
5. Run ingestion scripts to populate the SQL database
6. Connect Power BI to SQL Server for visualization

## Data Scope & Assumptions

- This pipeline is designed for personal Discogs accounts
- Discogs metadata is user-generated and may contain inconsistencies
- Data reflects the state of the collection at the time of extraction
- All data ingested belongs solely to the authenticated Discogs user
