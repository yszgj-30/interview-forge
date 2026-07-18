from __future__ import annotations

import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path


class Storage:
    def __init__(self, db_path: str | Path = "data/interview_forge.db") -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.db_path)
        connection.row_factory = sqlite3.Row
        return connection

    def _initialize(self) -> None:
        with self._connect() as db:
            db.executescript(
                """
                CREATE TABLE IF NOT EXISTS profiles (
                    id TEXT PRIMARY KEY, name TEXT NOT NULL, resume_text TEXT NOT NULL,
                    jd_text TEXT NOT NULL, created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS questions (
                    id TEXT PRIMARY KEY, profile_id TEXT, source TEXT NOT NULL,
                    question TEXT NOT NULL, answer TEXT NOT NULL, score INTEGER NOT NULL,
                    level TEXT NOT NULL, feedback TEXT NOT NULL, improved_answer TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS reviews (
                    id TEXT PRIMARY KEY, profile_id TEXT, title TEXT NOT NULL,
                    transcript TEXT NOT NULL, summary TEXT NOT NULL, audio_path TEXT,
                    created_at TEXT NOT NULL
                );
                """
            )

    def save_profile(self, name: str, resume_text: str, jd_text: str) -> str:
        profile_id = uuid.uuid4().hex
        with self._connect() as db:
            db.execute(
                "INSERT INTO profiles VALUES (?, ?, ?, ?, ?)",
                (profile_id, name, resume_text, jd_text, _now()),
            )
        return profile_id

    def list_profiles(self) -> list[dict]:
        with self._connect() as db:
            rows = db.execute("SELECT * FROM profiles ORDER BY created_at DESC").fetchall()
        return [dict(row) for row in rows]

    def save_question(
        self, profile_id: str | None, source: str, question: str, answer: str,
        score: int, level: str, feedback: str, improved_answer: str,
    ) -> str:
        item_id = uuid.uuid4().hex
        with self._connect() as db:
            db.execute(
                "INSERT INTO questions VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (item_id, profile_id, source, question, answer, score, level, feedback, improved_answer, _now()),
            )
        return item_id

    def list_questions(self, level: str | None = None) -> list[dict]:
        query = "SELECT * FROM questions"
        params: tuple[str, ...] = ()
        if level:
            query += " WHERE level = ?"
            params = (level,)
        query += " ORDER BY created_at DESC"
        with self._connect() as db:
            rows = db.execute(query, params).fetchall()
        return [dict(row) for row in rows]

    def search_questions(
        self, query: str = "", level: str | None = None, source: str | None = None,
    ) -> list[dict]:
        clauses: list[str] = []
        params: list[str] = []
        if query.strip():
            clauses.append("(question LIKE ? OR answer LIKE ? OR feedback LIKE ?)")
            term = f"%{query.strip()}%"
            params.extend([term, term, term])
        if level:
            clauses.append("level = ?")
            params.append(level)
        if source:
            clauses.append("source = ?")
            params.append(source)
        sql = "SELECT * FROM questions"
        if clauses:
            sql += " WHERE " + " AND ".join(clauses)
        sql += " ORDER BY created_at DESC"
        with self._connect() as db:
            rows = db.execute(sql, params).fetchall()
        return [dict(row) for row in rows]

    def list_weak_questions(self, profile_id: str, limit: int = 5) -> list[str]:
        with self._connect() as db:
            rows = db.execute(
                """
                SELECT question FROM questions
                WHERE profile_id = ? AND level IN ('红色', '黄色')
                ORDER BY CASE level WHEN '红色' THEN 0 ELSE 1 END, created_at DESC
                LIMIT ?
                """,
                (profile_id, limit),
            ).fetchall()
        return [str(row["question"]) for row in rows]

    def save_review(
        self, profile_id: str | None, title: str, transcript: str,
        summary: str, audio_path: str | None,
    ) -> str:
        review_id = uuid.uuid4().hex
        with self._connect() as db:
            db.execute(
                "INSERT INTO reviews VALUES (?, ?, ?, ?, ?, ?, ?)",
                (review_id, profile_id, title, transcript, summary, audio_path, _now()),
            )
        return review_id

    def count(self, table: str) -> int:
        if table not in {"profiles", "questions", "reviews"}:
            raise ValueError("Unsupported table")
        with self._connect() as db:
            return int(db.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0])

    def save_audio(self, content: bytes, suffix: str = ".wav") -> str:
        audio_dir = self.db_path.parent / "audio"
        audio_dir.mkdir(parents=True, exist_ok=True)
        path = audio_dir / f"{uuid.uuid4().hex}{suffix}"
        path.write_bytes(content)
        return str(path)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()
