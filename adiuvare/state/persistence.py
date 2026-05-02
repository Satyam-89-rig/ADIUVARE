import sqlite3
import asyncio
from pathlib import Path

from .identity_store import IdentityStore
from .whitelist import WhitelistStore


def init_state_db(db_path: str | Path) -> None:
    schema = Path(__file__).with_name("schema.sql").read_text()
    with sqlite3.connect(db_path) as conn:
        conn.executescript(schema)


def save_identity_state(db_path: str | Path, id_store: IdentityStore) -> None:
    with sqlite3.connect(db_path) as conn:
        for identity, win in id_store.items():
            conn.execute(
                """
                insert or replace into identity_state (
                    identity,
                    seen,
                    score_ewma,
                    blocked_until
                ) values (?, ?, ?, ?)
                """,
                (identity, win.seen, win.score_ewma, win.blocked_until),
            )
        conn.commit()


def save_whitelist_state(db_path: str | Path, wl: WhitelistStore) -> None:
    with sqlite3.connect(db_path) as conn:
        conn.execute("delete from whitelist_state")
        conn.execute("delete from banned_ip_state")
        for identity in sorted(wl.identities()):
            conn.execute(
                "insert into whitelist_state (identity) values (?)",
                (identity,),
            )
        for ip in sorted(wl.banned_ips()):
            conn.execute(
                "insert into banned_ip_state (ip) values (?)",
                (ip,),
            )
        conn.commit()


def load_identity_state(db_path: str | Path, id_store: IdentityStore) -> None:
    db_path = Path(db_path)
    if not db_path.exists():
        return

    with sqlite3.connect(db_path) as conn:
        rows = conn.execute(
            "select identity, seen, score_ewma, blocked_until from identity_state"
        ).fetchall()

    for identity, seen, score_ewma, blocked_until in rows:
        win = id_store.get(identity)
        win.seen = seen
        win.score_ewma = score_ewma
        win.blocked_until = blocked_until
        id_store.update(identity, win)


def load_whitelist_state(db_path: str | Path, wl: WhitelistStore) -> None:
    db_path = Path(db_path)
    if not db_path.exists():
        return

    with sqlite3.connect(db_path) as conn:
        ids = conn.execute("select identity from whitelist_state").fetchall()
        ips = conn.execute("select ip from banned_ip_state").fetchall()

    for (identity,) in ids:
        wl.add(identity)
    for (ip,) in ips:
        wl.ban_ip(ip)


def checkpoint_state(
    db_path: str | Path,
    id_store: IdentityStore,
    wl: WhitelistStore | None = None,
) -> None:
    init_state_db(db_path)
    save_identity_state(db_path, id_store)
    if wl is not None:
        save_whitelist_state(db_path, wl)


async def start_checkpoint_loop(
    db_path: str | Path,
    id_store: IdentityStore,
    wl: WhitelistStore | None = None,
    interval_secs: int = 60,
) -> None:
    while True:
        await asyncio.sleep(interval_secs)
        checkpoint_state(db_path, id_store, wl)
