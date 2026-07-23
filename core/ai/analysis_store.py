"""
SQLite persistence layer for AI Analysis jobs and agent tasks.
Database at ~/sembako/data/analysis.db
"""
import sqlite3
import json
import uuid
import hashlib
from datetime import datetime
from typing import Optional, Dict, List, Any
import os

DB_DIR = os.path.expanduser("~/sembako/data")
DB_PATH = os.path.join(DB_DIR, "analysis.db")

# Ensure directory exists
os.makedirs(DB_DIR, exist_ok=True)

_store = None


def get_store():
    global _store
    if _store is None:
        _store = AnalysisStore(DB_PATH)
    return _store


def init_db():
    """Initialize database tables. Called at app startup."""
    get_store()
    return True


class AnalysisStore:
    """Manages SQLite database for AI analysis jobs and agent tasks."""

    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self._initialize_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _initialize_db(self):
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # analysis_jobs table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS analysis_jobs (
                    id TEXT PRIMARY KEY,
                    mode TEXT NOT NULL,
                    status TEXT NOT NULL,
                    progress REAL DEFAULT 0.0,
                    data_snapshot_hash TEXT,
                    created_at TEXT NOT NULL,
                    started_at TEXT,
                    finished_at TEXT,
                    duration_ms INTEGER,
                    confidence_score REAL,
                    data_quality_score REAL,
                    providers_used TEXT,
                    summary TEXT,
                    result TEXT,
                    error_message TEXT,
                    idempotency_key TEXT UNIQUE
                )
            """)

            # agent_tasks table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS agent_tasks (
                    id TEXT PRIMARY KEY,
                    job_id TEXT NOT NULL,
                    agent_type TEXT NOT NULL,
                    status TEXT NOT NULL,
                    provider_id TEXT,
                    model_id TEXT,
                    attempt_count INTEGER DEFAULT 0,
                    max_attempts INTEGER DEFAULT 3,
                    progress REAL DEFAULT 0.0,
                    current_step TEXT,
                    started_at TEXT,
                    last_heartbeat_at TEXT,
                    finished_at TEXT,
                    checkpoint TEXT,
                    input_hash TEXT,
                    output TEXT,
                    error_code TEXT,
                    error_message TEXT,
                    next_retry_at TEXT,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (job_id) REFERENCES analysis_jobs(id)
                )
            """)

            # checkpoints table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS checkpoints (
                    id TEXT PRIMARY KEY,
                    job_id TEXT NOT NULL,
                    task_id TEXT NOT NULL,
                    step_name TEXT NOT NULL,
                    input_hash TEXT,
                    output TEXT,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (job_id) REFERENCES analysis_jobs(id),
                    FOREIGN KEY (task_id) REFERENCES agent_tasks(id)
                )
            """)

            # index for faster lookups
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_agent_tasks_job ON agent_tasks(job_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_jobs_status ON analysis_jobs(status)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_checkpoints_job_task ON checkpoints(job_id, task_id)")

            # Migration: add created_at to agent_tasks if missing
            try:
                cursor.execute("ALTER TABLE agent_tasks ADD COLUMN created_at TEXT")
            except sqlite3.OperationalError:
                pass

            # Migration: add router_used + error_code to jobs if missing
            try:
                cursor.execute("ALTER TABLE analysis_jobs ADD COLUMN router_used TEXT")
            except sqlite3.OperationalError:
                pass
            try:
                cursor.execute("ALTER TABLE analysis_jobs ADD COLUMN error_code TEXT")
            except sqlite3.OperationalError:
                pass
            try:
                cursor.execute("ALTER TABLE analysis_jobs ADD COLUMN can_continue INTEGER DEFAULT 0")
            except sqlite3.OperationalError:
                pass

            conn.commit()

    def create_job(self, mode: str, idempotency_key: str = None) -> Dict[str, Any]:
        """Create a new analysis job. Returns the job dict."""
        job_id = str(uuid.uuid4())
        now = datetime.utcnow().isoformat()
        ikey = idempotency_key or f"{mode}:{now}"

        with self._get_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute("""
                    INSERT INTO analysis_jobs (id, mode, status, created_at, idempotency_key)
                    VALUES (?, ?, ?, ?, ?)
                """, (job_id, mode, "DRAFT", now, ikey))
                conn.commit()
            except sqlite3.IntegrityError:
                # Idempotent: return existing
                cursor.execute("SELECT * FROM analysis_jobs WHERE idempotency_key = ?", (ikey,))
                row = cursor.fetchone()
                return dict(row) if row else {}

        return self.get_job(job_id) or {}

    def get_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM analysis_jobs WHERE id = ?", (job_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def update_job(self, job_id: str, **kwargs) -> bool:
        """Update job fields. Returns True if updated."""
        if not kwargs:
            return False

        allowed = {
            "mode", "status", "progress", "data_snapshot_hash", "started_at",
            "finished_at", "duration_ms", "confidence_score", "data_quality_score",
            "providers_used", "summary", "result", "error_message", "router_used",
            "error_code", "can_continue",
        }
        fields = {k: v for k, v in kwargs.items() if k in allowed}
        if not fields:
            return False

        set_clause = ", ".join(f"{k} = ?" for k in fields.keys())
        values = list(fields.values()) + [job_id]

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"UPDATE analysis_jobs SET {set_clause} WHERE id = ?", values)
            conn.commit()
            return cursor.rowcount > 0

    def create_agent_tasks(self, job_id: str, agent_configs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Create agent task rows for a job. Returns list of created tasks."""
        now = datetime.utcnow().isoformat()
        tasks = []

        with self._get_connection() as conn:
            cursor = conn.cursor()
            for cfg in agent_configs:
                task_id = str(uuid.uuid4())
                cursor.execute("""
                    INSERT INTO agent_tasks (id, job_id, agent_type, status, max_attempts, created_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (task_id, job_id, cfg["type"], "PENDING", cfg.get("max_attempts", 3), now))
                tasks.append({
                    "id": task_id,
                    "job_id": job_id,
                    "agent_type": cfg["type"],
                    "status": "PENDING",
                    "max_attempts": cfg.get("max_attempts", 3)
                })
            conn.commit()
        return tasks

    def get_agent_tasks(self, job_id: str) -> List[Dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM agent_tasks WHERE job_id = ? ORDER BY created_at", (job_id,))
            return [dict(row) for row in cursor.fetchall()]

    def get_agent_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM agent_tasks WHERE id = ?", (task_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def update_agent_task(self, task_id: str, **kwargs) -> bool:
        """Update agent task fields."""
        if not kwargs:
            return False

        allowed = {
            "status", "provider_id", "model_id", "attempt_count", "max_attempts",
            "progress", "current_step", "started_at", "last_heartbeat_at",
            "finished_at", "checkpoint", "input_hash", "output", "error_code",
            "error_message", "next_retry_at"
        }
        fields = {k: v for k, v in kwargs.items() if k in allowed}
        if not fields:
            return False

        set_clause = ", ".join(f"{k} = ?" for k in fields.keys())
        values = list(fields.values()) + [task_id]

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"UPDATE agent_tasks SET {set_clause} WHERE id = ?", values)
            conn.commit()
            return cursor.rowcount > 0

    def save_checkpoint(self, job_id: str, task_id: str, step_name: str,
                        output: Any, input_hash: str = "") -> str:
        """Save checkpoint for a task step."""
        checkpoint_id = str(uuid.uuid4())
        now = datetime.utcnow().isoformat()
        output_json = json.dumps(output, default=str) if not isinstance(output, str) else output

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO checkpoints (id, job_id, task_id, step_name, input_hash, output, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (checkpoint_id, job_id, task_id, step_name, input_hash, output_json, now))
            conn.commit()
        return checkpoint_id

    def get_checkpoint(self, job_id: str, task_id: str, step_name: str) -> Optional[Dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM checkpoints
                WHERE job_id = ? AND task_id = ? AND step_name = ?
                ORDER BY created_at DESC LIMIT 1
            """, (job_id, task_id, step_name))
            row = cursor.fetchone()
            return dict(row) if row else None

    def get_active_job(self) -> Optional[Dict[str, Any]]:
        """Get the most recent active (non-terminal) job."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM analysis_jobs
                WHERE status NOT IN ('COMPLETED', 'FAILED', 'CANCELLED')
                ORDER BY created_at DESC LIMIT 1
            """)
            row = cursor.fetchone()
            return dict(row) if row else None

    def get_history(self, limit: int = 30) -> List[Dict[str, Any]]:
        """Get analysis history (newest first)."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, mode, status, progress, created_at, started_at, finished_at,
                       duration_ms, confidence_score, data_quality_score,
                       (SELECT COUNT(*) FROM agent_tasks WHERE job_id = analysis_jobs.id) as agent_total,
                       (SELECT COUNT(*) FROM agent_tasks WHERE job_id = analysis_jobs.id AND status = 'COMPLETED') as agent_completed
                FROM analysis_jobs
                ORDER BY created_at DESC LIMIT ?
            """, (limit,))
            return [dict(row) for row in cursor.fetchall()]

    def cleanup_old_jobs(self, days: int = 30):
        """Delete jobs older than N days (and their tasks/checkpoints)."""
        cutoff = (datetime.utcnow()).strftime("%Y-%m-%dT%H:%M:%S")
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM agent_tasks WHERE job_id IN (SELECT id FROM analysis_jobs WHERE created_at < ?)", (cutoff,))
            cursor.execute("DELETE FROM checkpoints WHERE job_id IN (SELECT id FROM analysis_jobs WHERE created_at < ?)", (cutoff,))
            cursor.execute("DELETE FROM analysis_jobs WHERE created_at < ?", (cutoff,))
            conn.commit()


# Module-level test
if __name__ == "__main__":
    store = get_store()

    # Test DB init
    print("Testing DB initialization...")
    assert store.get_job("non-existent-id") is None

    # Test Job Creation
    mode = "full"
    job_result = store.create_job(mode)
    job_id = job_result['id']
    print(f"Job created: {job_id}")

    # Test Job Retrieval
    retrieved_job = store.get_job(job_id)
    assert retrieved_job is not None and retrieved_job['mode'] == mode

    # Test Agent Task Creation
    tasks = store.create_agent_tasks(job_id, [{"type": "MarketAnalyst", "max_attempts": 3}])
    task_id = tasks[0]['id']
    print(f"Task created: {task_id}")

    # Test Update Job
    success = store.update_job(job_id, status="RUNNING", progress=0.1)
    assert success
    updated_job = store.get_job(job_id)
    assert updated_job['status'] == "RUNNING"

    # Test Checkpoint Saving
    step = "initial_scrape"
    output_data = {"data_points": 50, "source": "api_v1"}
    checkpoint_id = store.save_checkpoint(job_id, task_id, step, output_data, input_hash="abc123xyz")
    print(f"Checkpoint saved with ID: {checkpoint_id}")

    # Test Checkpoint Retrieval
    retrieved_checkpoint = store.get_checkpoint(job_id, task_id, step)
    assert retrieved_checkpoint is not None and retrieved_checkpoint['step_name'] == step

    # Test History
    history = store.get_history(limit=100)
    assert len(history) >= 1

    print("Self-tests passed.")