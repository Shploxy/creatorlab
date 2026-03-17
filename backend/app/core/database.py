from __future__ import annotations

import json
import sqlite3
import threading
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from app.core.config import settings
from app.schemas.job import JobRecord


class JobRepository:
    def __init__(self, database_path: Path) -> None:
        self.database_path = database_path
        self._lock = threading.Lock()

    def initialize(self) -> None:
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS schema_migrations (
                    version INTEGER PRIMARY KEY,
                    name TEXT NOT NULL,
                    applied_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS jobs (
                    id TEXT PRIMARY KEY,
                    user_id TEXT,
                    anon_id TEXT,
                    tool TEXT NOT NULL,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    error TEXT,
                    input_files_json TEXT NOT NULL,
                    outputs_json TEXT NOT NULL,
                    meta_json TEXT NOT NULL,
                    progress INTEGER NOT NULL,
                    eta_seconds INTEGER
                )
                """
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS users (
                    id TEXT PRIMARY KEY,
                    email TEXT NOT NULL UNIQUE,
                    password_hash TEXT NOT NULL,
                    full_name TEXT,
                    plan_key TEXT NOT NULL,
                    email_verified INTEGER NOT NULL DEFAULT 0,
                    email_verified_at TEXT,
                    is_active INTEGER NOT NULL DEFAULT 1,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS sessions (
                    id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    token_hash TEXT NOT NULL UNIQUE,
                    created_at TEXT NOT NULL,
                    expires_at TEXT NOT NULL
                )
                """
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS subscriptions (
                    id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    plan_key TEXT NOT NULL,
                    status TEXT NOT NULL,
                    billing_provider TEXT,
                    external_subscription_id TEXT,
                    current_period_end TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS auth_tokens (
                    id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    token_hash TEXT NOT NULL UNIQUE,
                    token_type TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    expires_at TEXT NOT NULL,
                    consumed_at TEXT,
                    meta_json TEXT NOT NULL
                )
                """
            )
            columns = {row["name"] for row in connection.execute("PRAGMA table_info(jobs)").fetchall()}
            if "user_id" not in columns:
                connection.execute("ALTER TABLE jobs ADD COLUMN user_id TEXT")
            if "anon_id" not in columns:
                connection.execute("ALTER TABLE jobs ADD COLUMN anon_id TEXT")
            user_columns = {row["name"] for row in connection.execute("PRAGMA table_info(users)").fetchall()}
            if "email_verified" not in user_columns:
                connection.execute("ALTER TABLE users ADD COLUMN email_verified INTEGER NOT NULL DEFAULT 0")
            if "email_verified_at" not in user_columns:
                connection.execute("ALTER TABLE users ADD COLUMN email_verified_at TEXT")
            if "email_verified" not in user_columns or "email_verified_at" not in user_columns:
                now = datetime.now(timezone.utc).isoformat()
                connection.execute(
                    """
                    UPDATE users
                    SET email_verified = 1,
                        email_verified_at = COALESCE(email_verified_at, ?)
                    WHERE email_verified = 0
                    """,
                    (now,),
                )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_jobs_status_created_at ON jobs(status, created_at DESC)"
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_jobs_tool_created_at ON jobs(tool, created_at DESC)"
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_jobs_user_created_at ON jobs(user_id, created_at DESC)"
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_jobs_anon_created_at ON jobs(anon_id, created_at DESC)"
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_sessions_token_hash ON sessions(token_hash)"
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)"
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_auth_tokens_hash ON auth_tokens(token_hash)"
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_auth_tokens_user_type ON auth_tokens(user_id, token_type, created_at DESC)"
            )
            connection.execute(
                "INSERT OR IGNORE INTO schema_migrations(version, name) VALUES (1, 'initial_jobs_schema')"
            )
            connection.execute(
                "INSERT OR IGNORE INTO schema_migrations(version, name) VALUES (2, 'users_sessions_subscriptions')"
            )
            connection.execute(
                "INSERT OR IGNORE INTO schema_migrations(version, name) VALUES (3, 'auth_tokens_and_email_verification')"
            )
            connection.execute(
                "INSERT OR IGNORE INTO schema_migrations(version, name) VALUES (4, 'anonymous_visitor_jobs')"
            )
            connection.commit()

    def upsert_job(self, job: JobRecord) -> None:
        payload = (
            job.id,
            job.user_id,
            job.anon_id,
            job.tool,
            job.status,
            job.created_at.isoformat(),
            job.updated_at.isoformat(),
            job.error,
            json.dumps(job.input_files),
            json.dumps([output.model_dump() for output in job.outputs]),
            json.dumps(job.meta),
            job.progress,
            job.eta_seconds,
        )
        with self._lock, self._connect() as connection:
            connection.execute(
                """
                INSERT INTO jobs (
                    id, user_id, anon_id, tool, status, created_at, updated_at, error,
                    input_files_json, outputs_json, meta_json, progress, eta_seconds
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    user_id = excluded.user_id,
                    anon_id = excluded.anon_id,
                    tool = excluded.tool,
                    status = excluded.status,
                    created_at = excluded.created_at,
                    updated_at = excluded.updated_at,
                    error = excluded.error,
                    input_files_json = excluded.input_files_json,
                    outputs_json = excluded.outputs_json,
                    meta_json = excluded.meta_json,
                    progress = excluded.progress,
                    eta_seconds = excluded.eta_seconds
                """,
                payload,
            )
            connection.commit()

    def load_jobs(self) -> list[JobRecord]:
        with self._connect() as connection:
            rows = connection.execute("SELECT * FROM jobs ORDER BY datetime(created_at) DESC").fetchall()
        return [self._row_to_job(row) for row in rows]

    def get_job_by_id(self, job_id: str) -> JobRecord | None:
        with self._connect() as connection:
            row = connection.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)).fetchone()
        return self._row_to_job(row) if row else None

    def get_job_by_output_file_id(self, file_id: str) -> JobRecord | None:
        search_value = f'%\"file_id\": \"{file_id}\"%'
        with self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM jobs WHERE outputs_json LIKE ? ORDER BY datetime(created_at) DESC LIMIT 1",
                (search_value,),
            ).fetchone()
        return self._row_to_job(row) if row else None

    def query_jobs(
        self,
        *,
        limit: int,
        offset: int,
        status: str | None = None,
        tool: str | None = None,
        search: str | None = None,
        user_id: str | None = None,
        anon_id: str | None = None,
    ) -> tuple[list[JobRecord], int]:
        where_clauses: list[str] = []
        values: list[object] = []

        if user_id:
            where_clauses.append("user_id = ?")
            values.append(user_id)
        elif anon_id:
            where_clauses.append("anon_id = ?")
            values.append(anon_id)
        if status:
            where_clauses.append("status = ?")
            values.append(status)
        if tool:
            where_clauses.append("tool = ?")
            values.append(tool)
        if search:
            where_clauses.append("(id LIKE ? OR input_files_json LIKE ?)")
            search_value = f"%{search}%"
            values.extend([search_value, search_value])

        where_sql = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""
        with self._connect() as connection:
            total = connection.execute(f"SELECT COUNT(*) FROM jobs {where_sql}", values).fetchone()[0]
            rows = connection.execute(
                f"""
                SELECT * FROM jobs
                {where_sql}
                ORDER BY datetime(created_at) DESC
                LIMIT ? OFFSET ?
                """,
                [*values, limit, offset],
            ).fetchall()
        return [self._row_to_job(row) for row in rows], int(total)

    def create_user(
        self,
        email: str,
        password_hash: str,
        full_name: str | None,
        plan_key: str,
        *,
        email_verified: bool = False,
        email_verified_at: str | None = None,
    ) -> dict[str, object]:
        user_id = uuid4().hex
        now = datetime.now(timezone.utc).isoformat()
        payload = (
            user_id,
            email.lower(),
            password_hash,
            full_name,
            plan_key,
            int(email_verified),
            email_verified_at,
            1,
            now,
            now,
        )
        with self._lock, self._connect() as connection:
            connection.execute(
                """
                INSERT INTO users(
                    id, email, password_hash, full_name, plan_key,
                    email_verified, email_verified_at, is_active, created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                payload,
            )
            connection.commit()
        return self.get_user_by_id(user_id)  # type: ignore[return-value]

    def get_user_by_email(self, email: str) -> dict[str, object] | None:
        with self._connect() as connection:
            row = connection.execute("SELECT * FROM users WHERE email = ?", (email.lower(),)).fetchone()
        return self._row_to_user(row) if row else None

    def get_user_by_id(self, user_id: str) -> dict[str, object] | None:
        with self._connect() as connection:
            row = connection.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
        return self._row_to_user(row) if row else None

    def create_session(self, user_id: str, token_hash: str, expires_at: str) -> None:
        now = datetime.now(timezone.utc).isoformat()
        with self._lock, self._connect() as connection:
            connection.execute(
                """
                INSERT INTO sessions(id, user_id, token_hash, created_at, expires_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (uuid4().hex, user_id, token_hash, now, expires_at),
            )
            connection.commit()

    def delete_sessions_for_user(self, user_id: str) -> None:
        with self._lock, self._connect() as connection:
            connection.execute("DELETE FROM sessions WHERE user_id = ?", (user_id,))
            connection.commit()

    def delete_session(self, token_hash: str) -> None:
        with self._lock, self._connect() as connection:
            connection.execute("DELETE FROM sessions WHERE token_hash = ?", (token_hash,))
            connection.commit()

    def get_user_by_session_token(self, token_hash: str) -> dict[str, object] | None:
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT users.*
                FROM sessions
                JOIN users ON users.id = sessions.user_id
                WHERE sessions.token_hash = ? AND datetime(sessions.expires_at) > datetime('now')
                """,
                (token_hash,),
            ).fetchone()
        return self._row_to_user(row) if row else None

    def get_monthly_usage(self, user_id: str, month_start_iso: str) -> int:
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT COUNT(*) AS count
                FROM jobs
                WHERE user_id = ? AND datetime(created_at) >= datetime(?)
                """,
                (user_id, month_start_iso),
            ).fetchone()
        return int(row["count"]) if row else 0

    def get_anonymous_monthly_usage(self, anon_id: str, month_start_iso: str) -> int:
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT COUNT(*) AS count
                FROM jobs
                WHERE anon_id = ? AND datetime(created_at) >= datetime(?)
                """,
                (anon_id, month_start_iso),
            ).fetchone()
        return int(row["count"]) if row else 0

    def cleanup_expired_sessions(self) -> int:
        with self._lock, self._connect() as connection:
            cursor = connection.execute(
                "DELETE FROM sessions WHERE datetime(expires_at) <= datetime('now')"
            )
            connection.commit()
        return int(cursor.rowcount or 0)

    def count_active_sessions(self) -> int:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT COUNT(*) AS count FROM sessions WHERE datetime(expires_at) > datetime('now')"
            ).fetchone()
        return int(row["count"]) if row else 0

    def cleanup_expired_auth_tokens(self) -> int:
        with self._lock, self._connect() as connection:
            cursor = connection.execute(
                """
                DELETE FROM auth_tokens
                WHERE datetime(expires_at) <= datetime('now')
                   OR consumed_at IS NOT NULL
                """
            )
            connection.commit()
        return int(cursor.rowcount or 0)

    def count_pending_auth_tokens(self) -> dict[str, int]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT token_type, COUNT(*) AS count
                FROM auth_tokens
                WHERE consumed_at IS NULL AND datetime(expires_at) > datetime('now')
                GROUP BY token_type
                """
            ).fetchall()
        counts = {str(row["token_type"]): int(row["count"]) for row in rows}
        return {
            "email_verification": counts.get("email_verification", 0),
            "password_reset": counts.get("password_reset", 0),
        }

    def create_auth_token(self, user_id: str, token_hash: str, token_type: str, expires_at: str, meta: dict | None = None) -> None:
        now = datetime.now(timezone.utc).isoformat()
        with self._lock, self._connect() as connection:
            connection.execute(
                """
                UPDATE auth_tokens
                SET consumed_at = ?
                WHERE user_id = ? AND token_type = ? AND consumed_at IS NULL
                """,
                (now, user_id, token_type),
            )
            connection.execute(
                """
                INSERT INTO auth_tokens(id, user_id, token_hash, token_type, created_at, expires_at, consumed_at, meta_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    uuid4().hex,
                    user_id,
                    token_hash,
                    token_type,
                    now,
                    expires_at,
                    None,
                    json.dumps(meta or {}),
                ),
            )
            connection.commit()

    def get_auth_token(self, token_hash: str, token_type: str) -> dict[str, object] | None:
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT
                    auth_tokens.id AS auth_token_id,
                    auth_tokens.user_id AS auth_user_id,
                    auth_tokens.token_type AS auth_token_type,
                    auth_tokens.created_at AS auth_created_at,
                    auth_tokens.expires_at AS auth_expires_at,
                    auth_tokens.meta_json AS auth_meta_json,
                    users.*
                FROM auth_tokens
                JOIN users ON users.id = auth_tokens.user_id
                WHERE auth_tokens.token_hash = ?
                  AND auth_tokens.token_type = ?
                  AND auth_tokens.consumed_at IS NULL
                  AND datetime(auth_tokens.expires_at) > datetime('now')
                """,
                (token_hash, token_type),
            ).fetchone()
        return self._row_to_auth_token(row) if row else None

    def consume_auth_token(self, token_id: str) -> None:
        now = datetime.now(timezone.utc).isoformat()
        with self._lock, self._connect() as connection:
            connection.execute(
                "UPDATE auth_tokens SET consumed_at = ? WHERE id = ?",
                (now, token_id),
            )
            connection.commit()

    def mark_user_email_verified(self, user_id: str, verified_at: str) -> dict[str, object] | None:
        with self._lock, self._connect() as connection:
            connection.execute(
                """
                UPDATE users
                SET email_verified = 1, email_verified_at = ?, updated_at = ?
                WHERE id = ?
                """,
                (verified_at, verified_at, user_id),
            )
            connection.commit()
        return self.get_user_by_id(user_id)

    def update_user_password(self, user_id: str, password_hash: str) -> dict[str, object] | None:
        now = datetime.now(timezone.utc).isoformat()
        with self._lock, self._connect() as connection:
            connection.execute(
                """
                UPDATE users
                SET password_hash = ?, updated_at = ?
                WHERE id = ?
                """,
                (password_hash, now, user_id),
            )
            connection.commit()
        return self.get_user_by_id(user_id)

    def mark_incomplete_jobs_failed(self) -> None:
        with self._lock, self._connect() as connection:
            rows = connection.execute(
                "SELECT * FROM jobs WHERE status IN ('queued', 'processing')"
            ).fetchall()
            for row in rows:
                meta = json.loads(row["meta_json"])
                meta.update(
                    {
                        "queue_position": 0,
                        "interrupted": True,
                    }
                )
                now = datetime.now(timezone.utc).isoformat()
                connection.execute(
                    """
                    UPDATE jobs
                    SET status = ?, error = ?, progress = ?, eta_seconds = ?, updated_at = ?, meta_json = ?
                    WHERE id = ?
                    """,
                    (
                        "failed",
                        "Server restarted before the job could finish.",
                        100,
                        0,
                        now,
                        json.dumps(meta),
                        row["id"],
                    ),
                )
            connection.commit()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database_path)
        connection.row_factory = sqlite3.Row
        return connection

    def _row_to_job(self, row: sqlite3.Row) -> JobRecord:
        return JobRecord.model_validate(
            {
                "id": row["id"],
                "user_id": row["user_id"],
                "anon_id": row["anon_id"],
                "tool": row["tool"],
                "status": row["status"],
                "created_at": row["created_at"],
                "updated_at": row["updated_at"],
                "error": row["error"],
                "input_files": json.loads(row["input_files_json"]),
                "outputs": json.loads(row["outputs_json"]),
                "meta": json.loads(row["meta_json"]),
                "progress": row["progress"],
                "eta_seconds": row["eta_seconds"],
            }
        )

    def _row_to_user(self, row: sqlite3.Row) -> dict[str, object]:
        return {
            "id": row["id"],
            "email": row["email"],
            "password_hash": row["password_hash"],
            "full_name": row["full_name"],
            "plan_key": row["plan_key"],
            "email_verified": bool(row["email_verified"]),
            "email_verified_at": row["email_verified_at"],
            "is_active": bool(row["is_active"]),
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
        }

    def _row_to_auth_token(self, row: sqlite3.Row) -> dict[str, object]:
        payload = self._row_to_user(row)
        payload.update(
            {
                "auth_token_id": row["auth_token_id"],
                "auth_user_id": row["auth_user_id"],
                "token_type": row["auth_token_type"],
                "token_expires_at": row["auth_expires_at"],
                "token_created_at": row["auth_created_at"],
                "token_meta": json.loads(row["auth_meta_json"]),
            }
        )
        return payload


job_repository = JobRepository(settings.database_path)
