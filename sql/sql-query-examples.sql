/*
Purpose: Sanity-check queries for the Discogs → SQL Server ETL pipeline.

Run at least one of these after the ingestion script completes to confirm that collection items,
releases, artists, and genres were loaded and can be joined as expected. 
Below are also some basic, exploratory SQL queries. 
Happy analysis!
*/

-- Helpful query: produces a clean, flattened view of your Discogs collection
SELECT TOP 100
    r.title,
    r.year,
    artists.artists,
    genres.genres,
    CONVERT(date, c.date_added) AS date_added
FROM dbo.discogs_collection_item c
JOIN dbo.discogs_release r
    ON c.release_id = r.release_id

-- Pre-aggregate artists (one row per release_id)
LEFT JOIN (
    SELECT
        ra.release_id,
        STRING_AGG(a.name, ', ') AS artists
    FROM dbo.discogs_release_artist ra
    JOIN dbo.discogs_artist a
        ON ra.artist_id = a.artist_id
    GROUP BY ra.release_id
) artists
    ON r.release_id = artists.release_id

-- Pre-aggregate genres (one row per release_id)
LEFT JOIN (
    SELECT
        rg.release_id,
        STRING_AGG(rg.genre_name, ', ') AS genres
    FROM dbo.discogs_release_genre rg
    GROUP BY rg.release_id
) genres
    ON r.release_id = genres.release_id

ORDER BY date_added DESC;

-- Which artists appear most frequently across all collection items
SELECT
    a.name AS artist,
    COUNT(DISTINCT ra.release_id) AS release_count
FROM dbo.discogs_release_artist ra
JOIN dbo.discogs_artist a
    ON ra.artist_id = a.artist_id
GROUP BY a.name
ORDER BY release_count DESC;

-- Count of many releases fall under each genre in collection
SELECT
    rg.genre_name,
    COUNT(DISTINCT rg.release_id) AS release_count
FROM dbo.discogs_release_genre rg
GROUP BY rg.genre_name
ORDER BY release_count DESC;

-- Rich query: combining releases, artists, and genres for recent additions.
SELECT TOP 50
    r.title,
    r.year,
    STRING_AGG(DISTINCT a.name, ', ') AS artists,
    STRING_AGG(DISTINCT rg.genre_name, ', ') AS genres,
    CONVERT(date, c.date_added) AS date_added
FROM dbo.discogs_collection_item c
JOIN dbo.discogs_release r
    ON c.release_id = r.release_id
LEFT JOIN dbo.discogs_release_artist ra
    ON r.release_id = ra.release_id
LEFT JOIN dbo.discogs_artist a
    ON ra.artist_id = a.artist_id
LEFT JOIN dbo.discogs_release_genre rg
    ON r.release_id = rg.release_id
GROUP BY
    r.title,
    r.year,
    c.date_added
ORDER BY date_added DESC;
