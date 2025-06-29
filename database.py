import sqlite3
from typing import List, Dict, Any

DB_NAME = "labnotebook.db"


def init_db():
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS projects(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS experiments(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            date TEXT,
            custom_fields TEXT,
            FOREIGN KEY(project_id) REFERENCES projects(id)
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS data_files(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            experiment_id INTEGER NOT NULL,
            file_path TEXT NOT NULL,
            file_type TEXT,
            FOREIGN KEY(experiment_id) REFERENCES experiments(id)
        )
        """
    )
    conn.commit()
    conn.close()


def execute(query: str, params: tuple = ()):  # helper for non-select queries
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute(query, params)
    conn.commit()
    conn.close()


def fetchall(query: str, params: tuple = ()) -> List[tuple]:
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute(query, params)
    rows = cur.fetchall()
    conn.close()
    return rows
