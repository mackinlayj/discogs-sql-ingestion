# Power BI
This folder contains Power BI assets related to the Discogs dashboarding project, including .pbix files, supporting notes, and exported screenshots for documentation or sharing.

The Power BI layer is intentionally kept separate from data extraction and transformation logic. All data consumed by Power BI is sourced from SQL Server tables created by the ETL pipeline. 

## Recommended Workflow 
1. Run the ETL pipeline
    - Execute the Python ingestion script to populate or refresh the SQL Server database.
2. Verify the data
    - Before opening or refreshing Power BI reports, run the sanity check query located at:
    ```bash 
    /sql/sanity-check-collection.sql
    ```
    - Confirm that releases, artists, genres, and dates are populated as expected
3. Connect Power BI to SQL Server
    - Use SQL Server as the data source (Import or DirectQuery, depending on preference)
    - Connect to the database created by the ETL rather than querying the Discogs API directly. The ETL pipeline was intentional to ensure (especially if report is made public), that no private data is accidentally shared.
4. Build and refresh visuals
    - Define measures, calcualted coloumns, and relationships in Power BI
    - Refresh visuals after each successful ETL run
        - OPTIONAL: can automate this process.
