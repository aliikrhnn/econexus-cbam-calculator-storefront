from __future__ import annotations

import secrets
import sqlite3
from contextlib import contextmanager
from datetime import UTC, datetime, timedelta
from pathlib import Path


class StoreDB:
    def __init__(self, database_path: Path):
        self.database_path = database_path
        self.database_path.parent.mkdir(parents=True, exist_ok=True)

    @contextmanager
    def connect(self):
        conn = sqlite3.connect(self.database_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def init_db(self) -> None:
        with self.connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS orders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    email TEXT NOT NULL,
                    checkout_ref TEXT NOT NULL UNIQUE,
                    payment_status TEXT NOT NULL,
                    token TEXT NOT NULL UNIQUE,
                    token_expires_at TEXT NOT NULL,
                    download_count INTEGER NOT NULL DEFAULT 0,
                    download_limit INTEGER NOT NULL,
                    created_at TEXT NOT NULL,
                    paid_at TEXT,
                    payment_mode TEXT NOT NULL
                )
                """
            )

    def create_order(
        self,
        *,
        email: str,
        checkout_ref: str,
        payment_status: str,
        payment_mode: str,
        token_ttl_hours: int,
        download_limit: int,
    ) -> dict:
        now = datetime.now(UTC)
        token = secrets.token_urlsafe(32)
        expires_at = now + timedelta(hours=token_ttl_hours)

        with self.connect() as conn:
            conn.execute(
                """
                INSERT INTO orders (
                    email, checkout_ref, payment_status, token, token_expires_at,
                    download_count, download_limit, created_at, paid_at, payment_mode
                ) VALUES (?, ?, ?, ?, ?, 0, ?, ?, ?, ?)
                """,
                (
                    email,
                    checkout_ref,
                    payment_status,
                    token,
                    expires_at.isoformat(),
                    download_limit,
                    now.isoformat(),
                    now.isoformat() if payment_status == "paid" else None,
                    payment_mode,
                ),
            )
        return self.get_order_by_checkout_ref(checkout_ref)

    def mark_paid(
        self,
        *,
        checkout_ref: str,
        email: str,
        payment_mode: str,
        token_ttl_hours: int,
        download_limit: int,
    ) -> dict:
        existing = self.get_order_by_checkout_ref(checkout_ref)
        if existing:
            if existing["payment_status"] != "paid":
                with self.connect() as conn:
                    conn.execute(
                        """
                        UPDATE orders
                        SET payment_status = 'paid', paid_at = ?, email = ?
                        WHERE checkout_ref = ?
                        """,
                        (datetime.now(UTC).isoformat(), email, checkout_ref),
                    )
            return self.get_order_by_checkout_ref(checkout_ref)

        return self.create_order(
            email=email,
            checkout_ref=checkout_ref,
            payment_status="paid",
            payment_mode=payment_mode,
            token_ttl_hours=token_ttl_hours,
            download_limit=download_limit,
        )

    def get_order_by_checkout_ref(self, checkout_ref: str) -> dict | None:
        with self.connect() as conn:
            row = conn.execute(
                "SELECT * FROM orders WHERE checkout_ref = ?",
                (checkout_ref,),
            ).fetchone()
        return dict(row) if row else None

    def get_order_by_token(self, token: str) -> dict | None:
        with self.connect() as conn:
            row = conn.execute(
                "SELECT * FROM orders WHERE token = ?",
                (token,),
            ).fetchone()
        return dict(row) if row else None

    def increment_download_count(self, order_id: int) -> None:
        with self.connect() as conn:
            conn.execute(
                """
                UPDATE orders
                SET download_count = download_count + 1
                WHERE id = ?
                """,
                (order_id,),
            )
