"""Aplica sql/schema.sql en Neon. ATENCIÓN: recrea el schema public (borra datos)."""
import sys
from pathlib import Path
import psycopg

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from app.config import settings  # noqa: E402

sql = (Path(__file__).resolve().parent.parent / "sql" / "schema.sql").read_text(encoding="utf-8")
with psycopg.connect(settings.database_url, autocommit=True) as conn:
    conn.execute(sql)
    n = conn.execute("SELECT count(*) FROM information_schema.tables WHERE table_schema='public'").fetchone()[0]
print(f"Esquema creado: {n} tablas")
