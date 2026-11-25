import os
from contextlib import contextmanager
import psycopg
from psycopg.rows import dict_row

URL = os.environ.get("DATABASE_URL", "postgresql://crawler:prueba@localhost:5432/crawler")

@contextmanager
def connection():
    with psycopg.connect(URL, row_factory=dict_row) as db:
        yield db

def init_db():
    with connection() as db:
        db.execute("""CREATE TABLE IF NOT EXISTS contacts (
          id BIGSERIAL PRIMARY KEY, email TEXT UNIQUE NOT NULL,
          escola TEXT NOT NULL, responsavel TEXT NOT NULL DEFAULT '',
          saudacao TEXT NOT NULL, website TEXT NOT NULL,
          fonte TEXT NOT NULL, pesquisa TEXT NOT NULL,
          data_recolha TIMESTAMPTZ NOT NULL DEFAULT NOW(),
          revisto BOOLEAN NOT NULL DEFAULT FALSE
        )""")
        db.execute("""CREATE TABLE IF NOT EXISTS jobs (
          id BIGSERIAL PRIMARY KEY, pesquisa TEXT NOT NULL, profundidade INTEGER NOT NULL,
          limite INTEGER NOT NULL, status TEXT NOT NULL DEFAULT 'em_espera',
          discovered INTEGER NOT NULL DEFAULT 0, saved INTEGER NOT NULL DEFAULT 0,
          error TEXT NOT NULL DEFAULT '', created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
          finished_at TIMESTAMPTZ
        )""")
        db.commit()
