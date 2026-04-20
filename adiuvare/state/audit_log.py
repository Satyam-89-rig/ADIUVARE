import json
import sqlite3
from pathlib import Path

from ..core.models import AdiuvareEvent


class AuditLog:
    def __init__(self, db_path: str | Path) -> None:
        self._db_path = str(db_path)
        self._init_db()

    def _init_db(self) -> None:
        schema = Path(__file__).with_name("schema.sql").read_text()
        with sqlite3.connect(self._db_path) as conn:
            conn.executescript(schema)

    def write(self, event: AdiuvareEvent) -> None:
        row = (
            event.identity,
            event.endpoint,
            event.score,
            event.verdict,
            json.dumps(event.breakdown),
            json.dumps(event.detail),
        )
        with sqlite3.connect(self._db_path) as conn:
            conn.execute(
                """
                insert into audit_events (
                    identity,
                    endpoint,
                    score,
                    verdict,
                    breakdown_json,
                    detail_json
                ) values (?, ?, ?, ?, ?, ?)
                """,
                row,
            )
            conn.commit()

    def recent(self, limit: int = 20) -> list[dict]:
        with sqlite3.connect(self._db_path) as conn:
            rows = conn.execute(
                """
                select identity, endpoint, verdict, breakdown_json, detail_json
                from audit_events
                order by id desc
                limit ?
                """,
                (limit,),
            ).fetchall()

        return [
            {
                "identity": row[0],
                "endpoint": row[1],
                "verdict": row[2],
                "breakdown": json.loads(row[3]),
                "detail": json.loads(row[4]),
            }
            for row in rows
        ]

    def by_identity(self, identity: str, limit: int = 20) -> list[dict]:
        with sqlite3.connect(self._db_path) as conn:
            rows = conn.execute(
                """
                select identity, endpoint, verdict, breakdown_json, detail_json
                from audit_events
                where identity = ?
                order by id desc
                limit ?
                """,
                (identity, limit),
            ).fetchall()

        return [
            {
                "identity": row[0],
                "endpoint": row[1],
                "verdict": row[2],
                "breakdown": json.loads(row[3]),
                "detail": json.loads(row[4]),
            }
            for row in rows
        ]

    def write_patch(self, kind: str, patch: dict) -> None:
        with sqlite3.connect(self._db_path) as conn:
            conn.execute(
                """
                insert into config_history (kind, patch_json)
                values (?, ?)
                """,
                (kind, json.dumps(patch)),
            )
            conn.commit()
