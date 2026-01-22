/*
Purpose:
--------
Sanity-check query for the Discogs → SQL Server ETL pipeline.

Run this after the ingestion script completes to confirm that collection items,
releases, artists, and genres were loaded and can be joined as expected.
*/

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
