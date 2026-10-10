import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "niches.db"


def get_connection() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS niches (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            niche TEXT NOT NULL,
            anomaly_score INTEGER,
            avg_views INTEGER,
            growth_rate REAL,
            competition_level TEXT,
            source_video TEXT,
            channel TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS anomalies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            video_id TEXT UNIQUE,
            title TEXT,
            channel_id TEXT,
            channel_title TEXT,
            views INTEGER,
            z_score REAL,
            views_per_day REAL,
            engagement_ratio REAL,
            anomaly_score INTEGER,
            is_viral BOOLEAN,
            is_fast_growth BOOLEAN,
            is_low_competition BOOLEAN,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS keywords (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            keyword TEXT UNIQUE,
            frequency INTEGER,
            weight REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    conn.commit()
    conn.close()


def save_niches(niches: list[dict]):
    conn = get_connection()
    conn.executemany(
        """INSERT INTO niches (niche, anomaly_score, avg_views, growth_rate, competition_level, source_video, channel)
           VALUES (:niche, :anomaly_score, :avg_views, :growth_rate, :competition_level, :source_video, :channel)""",
        niches,
    )
    conn.commit()
    conn.close()


def save_anomalies(anomalies: list[dict]):
    conn = get_connection()
    for a in anomalies:
        conn.execute(
            """INSERT OR REPLACE INTO anomalies
               (video_id, title, channel_id, channel_title, views, z_score, views_per_day,
                engagement_ratio, anomaly_score, is_viral, is_fast_growth, is_low_competition)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                a["video_id"], a["title"], a["channel_id"], a["channel_title"],
                a["views"], a["z_score"], a["views_per_day"], a["engagement_ratio"],
                a["anomaly_score"], a["is_viral"], a["is_fast_growth"], a["is_low_competition"],
            ),
        )
    conn.commit()
    conn.close()


def save_keywords(keywords: list[dict]):
    conn = get_connection()
    for k in keywords:
        conn.execute(
            "INSERT OR REPLACE INTO keywords (keyword, frequency, weight) VALUES (?, ?, ?)",
            (k["keyword"], k["frequency"], k["weight"]),
        )
    conn.commit()
    conn.close()


def get_niches(limit: int = 20) -> list[dict]:
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM niches ORDER BY anomaly_score DESC, avg_views DESC LIMIT ?", (limit,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_anomalies(limit: int = 50) -> list[dict]:
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM anomalies ORDER BY anomaly_score DESC LIMIT ?", (limit,)
    ).fetchall()
    conn.close()
    result = []
    for r in rows:
        d = dict(r)
        d["is_viral"] = bool(d["is_viral"])
        d["is_fast_growth"] = bool(d["is_fast_growth"])
        d["is_low_competition"] = bool(d["is_low_competition"])
        result.append(d)
    return result


def get_keywords(limit: int = 10) -> list[dict]:
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM keywords ORDER BY frequency DESC LIMIT ?", (limit,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]
