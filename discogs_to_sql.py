"""
Discogs -> SQL Server ETL Pipeline

This script:
1. Loads configuration from a .env file
2. Connects to the Discogs API using a personal access token
3. Pulls a user's full Discogs collection (with pagination)
4. Normalizes the nested JSON responses into relational tables
5. Upserts (insert/update) the data into SQL Server using MERGE

Designed for:
- SQL Server (Windows Authentication)
- Power BI
- Reruns (safe to run multiple times)

Author: Jacob MacKinlay
"""

import os     # Read environment variables                                       
import time   # Sleep between API requests
import json   # Serialize Discogs "notes" safely for SQL
from dataclasses import dataclass
from typing import Any, Dict, Iterable, Optional, Tuple
from pathlib import Path   # Reliable file path handling

import requests
from dotenv import load_dotenv
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

# -----------------------------------------------------------------
# Environment variable loading
# -----------------------------------------------------------------

# Always laod the .env file that sits next to this script
# This avoids issues where VS Code / Powershell run from a different directory

load_dotenv(dotenv_path=Path(__file__).with_name(".env"))

# -----------------------------------------------------------------
# Configuration
# -----------------------------------------------------------------

@dataclass(frozen=True)
class Config:
    # Fails fast if something is missing
    discogs_token: str
    discogs_user_agent: str
    discogs_username: str

    sql_server: str
    sql_database: str
    sql_driver: str

    # Sleep times between API calls to avoid rate limiting
    request_sleep_seconds: float = 1.0


def get_config() -> Config:
    # If any required variable is missing, the script fails immediately with a clear error msg
    missing = []

    def env(name: str) -> str:
        v = os.getenv(name)
        if not v:
            missing.append(name)
            return ""
        return v

    cfg = Config(
        discogs_token=env("DISCOGS_TOKEN"),
        discogs_user_agent=env("DISCOGS_USER_AGENT"),
        discogs_username=env("DISCOGS_USERNAME"),
        sql_server=env("SQL_SERVER"),
        sql_database=env("SQL_DATABASE"),
        sql_driver=env("SQL_DRIVER"),
    )

    if missing:
        raise RuntimeError(f"Missing required environment variables: {', '.join(missing)}")

    return cfg


# -----------------------------------------------------------------
# Discogs API client
# -----------------------------------------------------------------

class DiscogsClient:
    # Responsibilities: authentication, pagination, rate limiing, retries
    def __init__(self, cfg: Config):
        self.cfg = cfg
        self.base_url = "https://api.discogs.com"
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Discogs token={cfg.discogs_token}",
            "User-Agent": cfg.discogs_user_agent,
            "Accept": "application/vnd.discogs.v2+json",
        })

    @retry(
        reraise=True,
        stop=stop_after_attempt(6),
        wait=wait_exponential(multiplier=1, min=1, max=30),
        retry=retry_if_exception_type(requests.RequestException),
    )
    def get(self, path: str, params: Optional[dict] = None) -> Dict[str, Any]:
        #Perform a GET request with retries for transient errors
        #Retries on: rate limits (429) and temporary server errors (5xx)
        url = f"{self.base_url}{path}"
        resp = self.session.get(url, params=params, timeout=30)

        if resp.status_code in (429, 500, 502, 503, 504):
            raise requests.RequestException(f"Temporary error {resp.status_code}: {resp.text[:200]}")

        resp.raise_for_status()
        time.sleep(self.cfg.request_sleep_seconds)
        return resp.json()

    def paginate(self, path: str, params: Optional[dict] = None) -> Iterable[Dict[str, Any]]:
        # Generator that yeilds all items across paginated Discogs endpoints
        page = 1
        params = dict(params or {})
        params.setdefault("per_page", 100)

        while True:
            params["page"] = page
            data = self.get(path, params=params)

            items = data.get("releases") or data.get("results") or []
            for item in items:
                yield item

            pagination = data.get("pagination", {})
            pages = pagination.get("pages", page)
            if page >= pages:
                break
            page += 1


# -----------------------------------------------------------------
# SQL helpers (SQL Server)
# -----------------------------------------------------------------

def make_engine(cfg: Config) -> Engine:
    # Create a SQLAlchemy engine using Windows Authentication
    # Notes: no username/password required; ODBC Driver name must match what is installed
    driver = cfg.sql_driver.replace(" ", "+")
    conn_str = (
        f"mssql+pyodbc://@{cfg.sql_server}/{cfg.sql_database}"
        f"?driver={driver}&Trusted_Connection=yes"
        f"&TrustServerCertificate=yes"
    )
    return create_engine(conn_str, fast_executemany=True, future=True)


def init_schema(engine: Engine) -> None:
    # Create all required tables if they do not already exist
    # This allows: first time setiup and safe reruns without dropping data
    ddl = """
    IF OBJECT_ID('dbo.discogs_release', 'U') IS NULL
    CREATE TABLE dbo.discogs_release (
        release_id INT NOT NULL PRIMARY KEY,
        title NVARCHAR(512) NULL,
        year INT NULL,
        country NVARCHAR(128) NULL,
        released NVARCHAR(64) NULL,
        thumb_url NVARCHAR(1024) NULL,
        cover_url NVARCHAR(1024) NULL,
        resource_url NVARCHAR(1024) NULL,
        last_updated_utc DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME()
    );

    IF OBJECT_ID('dbo.discogs_collection_item', 'U') IS NULL
    CREATE TABLE dbo.discogs_collection_item (
        collection_instance_id INT NOT NULL PRIMARY KEY,
        folder_id INT NULL,
        release_id INT NOT NULL,
        date_added NVARCHAR(64) NULL,
        rating INT NULL,
        notes NVARCHAR(MAX) NULL,
        last_updated_utc DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME()
    );

    IF OBJECT_ID('dbo.discogs_artist', 'U') IS NULL
    CREATE TABLE dbo.discogs_artist (
        artist_id INT NOT NULL PRIMARY KEY,
        name NVARCHAR(512) NULL
    );

    IF OBJECT_ID('dbo.discogs_release_artist', 'U') IS NULL
    CREATE TABLE dbo.discogs_release_artist (
        release_id INT NOT NULL,
        artist_id INT NOT NULL,
        role NVARCHAR(256) NOT NULL DEFAULT(''),
        join_text NVARCHAR(64) NULL,
        anv NVARCHAR(512) NOT NULL DEFAULT(''),
        PRIMARY KEY (release_id, artist_id, role, anv)
    );

    IF OBJECT_ID('dbo.discogs_genre', 'U') IS NULL
    CREATE TABLE dbo.discogs_genre (
        genre_name NVARCHAR(128) NOT NULL PRIMARY KEY
    );

    IF OBJECT_ID('dbo.discogs_style', 'U') IS NULL
    CREATE TABLE dbo.discogs_style (
        style_name NVARCHAR(128) NOT NULL PRIMARY KEY
    );

    IF OBJECT_ID('dbo.discogs_release_genre', 'U') IS NULL
    CREATE TABLE dbo.discogs_release_genre (
        release_id INT NOT NULL,
        genre_name NVARCHAR(128) NOT NULL,
        PRIMARY KEY (release_id, genre_name)
    );

    IF OBJECT_ID('dbo.discogs_release_style', 'U') IS NULL
    CREATE TABLE dbo.discogs_release_style (
        release_id INT NOT NULL,
        style_name NVARCHAR(128) NOT NULL,
        PRIMARY KEY (release_id, style_name)
    );
    """
    with engine.begin() as conn:
        conn.execute(text(ddl))


def upsert_release(engine: Engine, row: Dict[str, Any]) -> None:
    sql = """
    MERGE dbo.discogs_release AS target
    USING (SELECT
        :release_id AS release_id,
        :title AS title,
        :year AS year,
        :country AS country,
        :released AS released,
        :thumb_url AS thumb_url,
        :cover_url AS cover_url,
        :resource_url AS resource_url
    ) AS src
    ON target.release_id = src.release_id
    WHEN MATCHED THEN UPDATE SET
        title = src.title,
        year = src.year,
        country = src.country,
        released = src.released,
        thumb_url = src.thumb_url,
        cover_url = src.cover_url,
        resource_url = src.resource_url,
        last_updated_utc = SYSUTCDATETIME()
    WHEN NOT MATCHED THEN
        INSERT (release_id, title, year, country, released, thumb_url, cover_url, resource_url)
        VALUES (src.release_id, src.title, src.year, src.country, src.released, src.thumb_url, src.cover_url, src.resource_url);
    """
    with engine.begin() as conn:
        conn.execute(text(sql), row)


def upsert_collection_item(engine: Engine, row: Dict[str, Any]) -> None:
    sql = """
    MERGE dbo.discogs_collection_item AS target
    USING (SELECT
        :collection_instance_id AS collection_instance_id,
        :folder_id AS folder_id,
        :release_id AS release_id,
        :date_added AS date_added,
        :rating AS rating,
        :notes AS notes
    ) AS src
    ON target.collection_instance_id = src.collection_instance_id
    WHEN MATCHED THEN UPDATE SET
        folder_id = src.folder_id,
        release_id = src.release_id,
        date_added = src.date_added,
        rating = src.rating,
        notes = src.notes,
        last_updated_utc = SYSUTCDATETIME()
    WHEN NOT MATCHED THEN
        INSERT (collection_instance_id, folder_id, release_id, date_added, rating, notes)
        VALUES (src.collection_instance_id, src.folder_id, src.release_id, src.date_added, src.rating, src.notes);
    """
    with engine.begin() as conn:
        conn.execute(text(sql), row)


def upsert_artist(engine: Engine, artist_id: int, name: str) -> None:
    sql = """
    MERGE dbo.discogs_artist AS target
    USING (SELECT :artist_id AS artist_id, :name AS name) AS src
    ON target.artist_id = src.artist_id
    WHEN MATCHED THEN UPDATE SET name = src.name
    WHEN NOT MATCHED THEN INSERT (artist_id, name) VALUES (src.artist_id, src.name);
    """
    with engine.begin() as conn:
        conn.execute(text(sql), {"artist_id": artist_id, "name": name})


def upsert_release_artist(engine: Engine, release_id: int, artist_id: int, role: str, join_text: str, anv: str) -> None:
    sql = """
    MERGE dbo.discogs_release_artist AS target
    USING (SELECT
        :release_id AS release_id,
        :artist_id AS artist_id,
        :role AS role,
        :join_text AS join_text,
        :anv AS anv
    ) AS src
    ON target.release_id = src.release_id
       AND target.artist_id = src.artist_id
       AND ISNULL(target.role,'') = ISNULL(src.role,'')
       AND ISNULL(target.anv,'') = ISNULL(src.anv,'')
    WHEN MATCHED THEN UPDATE SET
        join_text = src.join_text
    WHEN NOT MATCHED THEN
        INSERT (release_id, artist_id, role, join_text, anv)
        VALUES (src.release_id, src.artist_id, src.role, src.join_text, src.anv);
    """
    with engine.begin() as conn:
        conn.execute(text(sql), {
            "release_id": release_id,
            "artist_id": artist_id,
            "role": role,
            "join_text": join_text,
            "anv": anv,
        })


def upsert_dim_value(engine: Engine, table: str, col: str, value: str) -> None:
    sql = f"""
    MERGE dbo.{table} AS target
    USING (SELECT :value AS {col}) AS src
    ON target.{col} = src.{col}
    WHEN NOT MATCHED THEN INSERT ({col}) VALUES (src.{col});
    """
    with engine.begin() as conn:
        conn.execute(text(sql), {"value": value})


def upsert_bridge(engine: Engine, table: str, release_id: int, col: str, value: str) -> None:
    sql = f"""
    MERGE dbo.{table} AS target
    USING (SELECT :release_id AS release_id, :value AS {col}) AS src
    ON target.release_id = src.release_id AND target.{col} = src.{col}
    WHEN NOT MATCHED THEN INSERT (release_id, {col}) VALUES (src.release_id, src.{col});
    """
    with engine.begin() as conn:
        conn.execute(text(sql), {"release_id": release_id, "value": value})


# -----------------------------------------------------------------
# Transformations
# -----------------------------------------------------------------

def normalize_release_from_collection_item(item: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    # Convert a single Discogs collection item (nested JSON) into two flat relational rows: 
    # 1) discogs_release, and 2) discogs_collection_item
    # This is the key transformation step in the pipeline
    basic = item.get("basic_information", {}) or {}

    release_id = int(basic.get("id"))
    title = basic.get("title")
    year = basic.get("year")
    country = basic.get("country")
    released = basic.get("released")
    resource_url = basic.get("resource_url")

    thumb_url = basic.get("thumb")
    cover_url = basic.get("cover_image")

    release_row = {
        "release_id": release_id,
        "title": title,
        "year": int(year) if isinstance(year, int) else (int(year) if str(year).isdigit() else None),
        "country": country,
        "released": released,
        "thumb_url": thumb_url,
        "cover_url": cover_url,
        "resource_url": resource_url,
    }

    # Convert notes (list/dict) into JSON string to avoid pyodbc TVP error
    raw_notes = item.get("notes")
    notes_json = json.dumps(raw_notes, ensure_ascii=False) if raw_notes is not None else None

    collection_row = {
        "collection_instance_id": int(item.get("id")),
        "folder_id": int(item.get("folder_id")) if item.get("folder_id") is not None else None,
        "release_id": release_id,
        "date_added": item.get("date_added"),
        "rating": item.get("rating"),
        "notes": notes_json,
    }

    return release_row, collection_row


# -----------------------------------------------------------------
# Load pipeline
# -----------------------------------------------------------------

def ingest_collection(cfg: Config) -> None:
    # Orchestrates the full ETL process: 1) connect to API, 2) connect to SQL server, 
    # 3) ensure schema exists, 4) pull Discogs collection, and 5) upsert all related entities
    print(f"Loaded SQL_SERVER: {cfg.sql_server}")

    client = DiscogsClient(cfg)
    engine = make_engine(cfg)
    init_schema(engine)

    path = f"/users/{cfg.discogs_username}/collection/folders/0/releases"

    count = 0
    for item in client.paginate(path):
        release_row, collection_row = normalize_release_from_collection_item(item)

        upsert_release(engine, release_row)
        upsert_collection_item(engine, collection_row)

        basic = item.get("basic_information", {}) or {}
        release_id = release_row["release_id"]

        for a in (basic.get("artists") or []):
            artist_id = a.get("id")
            name = a.get("name")
            if artist_id is None:
                continue

            upsert_artist(engine, int(artist_id), name or "")
            upsert_release_artist(
                engine,
                release_id=release_id,
                artist_id=int(artist_id),
                role=(a.get("role") or ""),
                join_text=(a.get("join") or ""),
                anv=(a.get("anv") or ""),
            )

        for g in (basic.get("genres") or []):
            if not g:
                continue
            upsert_dim_value(engine, "discogs_genre", "genre_name", g)
            upsert_bridge(engine, "discogs_release_genre", release_id, "genre_name", g)

        for s in (basic.get("styles") or []):
            if not s:
                continue
            upsert_dim_value(engine, "discogs_style", "style_name", s)
            upsert_bridge(engine, "discogs_release_style", release_id, "style_name", s)

        count += 1
        if count % 100 == 0:
            print(f"Ingested {count} collection items...")

    print(f"Done. Total collection items ingested: {count}")


def main():
    cfg = get_config()
    ingest_collection(cfg)


if __name__ == "__main__":
    main()
