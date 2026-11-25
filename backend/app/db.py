"""Pool de conexiones a PostgreSQL (Neon) con psycopg 3."""
from contextlib import contextmanager
from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool
from .config import settings

# open=False: se abre en el lifespan de FastAPI. Neon puede suspender la DB, por eso check de conexión.
pool = ConnectionPool(
    settings.database_url,
    min_size=1,
    max_size=5,
    open=False,
    kwargs={"row_factory": dict_row},
    check=ConnectionPool.check_connection,
)


@contextmanager
def get_cursor():
    """Entrega un cursor con commit automático (rollback si hay excepción)."""
    with pool.connection() as conn:
        with conn.cursor() as cur:
            yield cur


def fetch_all(sql: str, params=None) -> list[dict]:
    with get_cursor() as cur:
        cur.execute(sql, params)
        return cur.fetchall()


def fetch_one(sql: str, params=None) -> dict | None:
    with get_cursor() as cur:
        cur.execute(sql, params)
        return cur.fetchone()
