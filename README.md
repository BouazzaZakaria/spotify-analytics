# Spotify Analytics Pipeline

A Python ETL project that cleans Spotify track data, enriches it with listening and audio-analysis metrics, and publishes analytics-ready tables as CSV files or to PostgreSQL. The resulting tables are designed to be explored in Power BI Desktop.

## Project Overview

The pipeline reads a Spotify tracks CSV, standardizes and deduplicates records, handles missing values, derives report-friendly metrics, and creates a track table plus two supporting analytical tables. The load target is selected through environment configuration: CSV for a lightweight local workflow, or PostgreSQL for a database-backed workflow.

```mermaid
flowchart LR
    A[spotify_tracks.csv] --> B[run_pipeline.py]
    B --> C[transform.py<br/>clean, deduplicate, enrich]
    C --> D{load target}
    D -->|CSV| E[output/*.csv]
    D -->|PostgreSQL| F[(tracks_clean)]
    D -->|PostgreSQL| G[(artist_bridge)]
    D -->|PostgreSQL| H[(genre_summary)]
    E --> I[Power BI Desktop]
    F --> I
    G --> I
    H --> I
```

## Features

- Removes extraneous index columns and normalizes column names.
- Deduplicates tracks by `track_id`, retaining the most popular record.
- Drops rows missing essential identifiers, track names, or tempo; imputes missing audio metrics with their column medians.
- Derives `mood_score`, `duration_min`, popularity tiers, readable musical key and mode names, and energy-valence mood quadrants.
- Creates an artist bridge table by splitting semicolon-separated artist names.
- Produces genre-level aggregates for track counts and average audio/popularity metrics.
- Loads results to local CSV files or PostgreSQL.

## Repository Contents

| File | Purpose |
| --- | --- |
| `run_pipeline.py` | Runs the transformation and loads the three output tables. |
| `transform.py` | Cleans tracks and creates the artist bridge and genre summary dataframes. |
| `load.py` | Switches between CSV and PostgreSQL load targets. |
| `extract.py` | Contains Spotify API extraction helper functions. |
| `requirements.txt` | Python dependencies for the project. |
| `.env.example` | Safe template for local environment variables. |

The source dataset, generated CSV outputs, Power BI report files, credentials, and local Python environments are intentionally excluded from Git. `app.py` is currently an unused placeholder; the dashboard is intended to be built in Power BI Desktop.

## Requirements

- Python 3.10 or newer
- PostgreSQL for database loading (optional if using CSV output)
- Power BI Desktop for report development (optional)
- A Spotify Developer application only when using the extraction helpers

## Setup

Run these commands from the project directory in PowerShell:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
Copy-Item .env.example .env
```

Edit `.env` locally with your settings. Never commit `.env` or paste real credentials into the README, source files, or issue reports.

### Input data

Place `spotify_tracks.csv` in the project root. The transformation expects Spotify track fields including `track_id`, `track_name`, `artists`, `track_genre`, `popularity`, `duration_ms`, `key`, `mode`, and the audio feature columns used in `transform.py`. The supplied dataset is not included in this repository; obtain it from a source you are permitted to use.

## Run the Pipeline

### CSV output

Set `USE_POSTGRES=false` in `.env`, then run:

```powershell
python run_pipeline.py
```

The loader writes `tracks_clean.csv`, `artist_bridge.csv`, and `genre_summary.csv` to the `output/` directory.

### PostgreSQL output

Create a PostgreSQL database (for example, `spotify_analytics`), ensure the server is running, then configure `.env`:

```env
USE_POSTGRES=true
DATABASE_URL=postgresql+psycopg2://postgres:YOUR_PASSWORD@localhost:5432/spotify_analytics
```

Replace the example username, password, host, port, and database with your own values. Then run:

```powershell
python run_pipeline.py
```

The loader creates/replaces the `tracks_clean`, `artist_bridge`, and `genre_summary` tables. Because the current load strategy replaces each table, rerunning the pipeline overwrites its prior contents.

## Power BI Desktop

1. Run the pipeline with PostgreSQL enabled, or choose the CSV load mode.
2. In Power BI Desktop, select **Get data** and connect to PostgreSQL or import the CSV outputs.
3. For PostgreSQL, provide the server (commonly `localhost:5432`), database name, and database credentials. Select **Import** for a simple local report.
4. Load `tracks_clean`, `artist_bridge`, and optionally `genre_summary`.
5. In Model view, relate `tracks_clean[track_id]` one-to-many to `artist_bridge[track_id]`. Use `tracks_clean` for track-level visuals and slicers.
6. Build measures and visuals such as track count, average popularity, popularity by genre, and energy versus valence. Save the report as a `.pbix` file; report files are excluded from this code repository by default.

Refresh the Power BI model after rerunning the pipeline to load updated data. Scheduled refresh against a PostgreSQL server running on a personal computer requires an appropriately configured on-premises data gateway when publishing to Power BI Service.

## Spotify API Extraction Notes

`extract.py` contains helper functions for playlist tracks, top artists, and recently played tracks. The current `run_pipeline.py` does not call those helpers; it reads the local `spotify_tracks.csv` input directly. The helpers also require Spotify credentials and appropriate OAuth scopes for user-specific endpoints. Verify current Spotify API access and authorization requirements before relying on those functions in an automated extraction workflow.

## Data and Security

- Never commit `.env`; it is ignored by Git. `.env.example` contains placeholders only.
- `spotify_tracks.csv` and generated `*.csv` files are ignored because they can be large, are reproducible, and may have separate redistribution terms.
- Virtual environments, caches, and `.pbix`/`.pbit` report files are local artifacts and are ignored.
- Review `git status` and the staged file list before pushing to GitHub. If a credential was ever committed or shared, revoke or rotate it; deleting it in a later commit does not remove it from Git history.

## Current Limitations

- The pipeline expects the source CSV to be present locally; extraction is not yet wired into the pipeline run.
- PostgreSQL loading uses table replacement rather than incremental or append-only loading.
- `loaded_at` is generated at transformation time, so its value changes on each run.
- The Power BI report is built separately in Power BI Desktop and is not generated by the Python code.