import os
import pandas as pd
from dotenv import load_dotenv

load_dotenv()


# =======================================================
# VERSION 1 — CSV  (use for v1 / Power BI quick start)
# =======================================================
def load_to_csv(df: pd.DataFrame, name: str, outdir: str = "output"):
    """Write dataframe to output/{name}.csv — the v1 target for Power BI."""
    os.makedirs(outdir, exist_ok=True)
    path = os.path.join(outdir, f"{name}.csv")
    df.to_csv(path, index=False)
    print(f"  💾 Saved {len(df):,} rows → {path}")


# =======================================================
# VERSION 2 — PostgreSQL  (the "scale-up" story)
# =======================================================
def load_to_postgres(df: pd.DataFrame, table_name: str):
    """
    Write dataframe to Postgres. Requires DATABASE_URL in .env, e.g.:
    DATABASE_URL=postgresql://user:password@host:5432/dbname
    """
    from sqlalchemy import create_engine
    engine = create_engine(os.getenv("DATABASE_URL"))
    with engine.begin() as conn:
        df.to_sql(table_name, conn, if_exists="replace", index=False)
    print(f"  💾 Loaded {len(df):,} rows → postgres:{table_name}")


# =======================================================
# Switchboard — flip one flag to change backends
# =======================================================
USE_POSTGRES = os.getenv("USE_POSTGRES", "false").lower() == "true"

def load(df: pd.DataFrame, name: str):
    if USE_POSTGRES:
        load_to_postgres(df, name)
    else:
        load_to_csv(df, name)