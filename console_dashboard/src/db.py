"""DB 커넥션 담당. 쿼리 로직은 여기 두지 않는다 (queries.py 참고)."""

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent.parent / "console_data.db"


def get_connection() -> sqlite3.Connection:
    return sqlite3.connect(DB_PATH)
