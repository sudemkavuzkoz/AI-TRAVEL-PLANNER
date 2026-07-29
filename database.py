import os
import sqlite3
import json
import numpy as np

DB_NAME = os.path.join(os.path.dirname(os.path.abspath(__file__)), "travel_rag.db")


def _ensure_schema(conn):
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS documents(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        source TEXT,
        text TEXT,
        embedding TEXT
    )
    """)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS favorites(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        country TEXT NOT NULL UNIQUE
    )
    """)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS trip_plans(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        country TEXT NOT NULL,
        days INTEGER NOT NULL,
        request TEXT NOT NULL,
        plan_text TEXT NOT NULL,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
    """)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS favorite_restaurants(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        place_name TEXT NOT NULL,
        address TEXT,
        country TEXT,
        maps_url TEXT,
        place_id TEXT UNIQUE,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
    """)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS visited_countries(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        country TEXT NOT NULL UNIQUE,
        visited_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
    """)
    cursor.execute("PRAGMA table_info(documents)")
    existing_columns = {row[1] for row in cursor.fetchall()}
    required_columns = {"source": "TEXT", "text": "TEXT", "embedding": "TEXT"}

    for column, col_type in required_columns.items():
        if column not in existing_columns:
            cursor.execute(f"ALTER TABLE documents ADD COLUMN {column} {col_type}")
    conn.commit()


def init_db():
    conn = sqlite3.connect(DB_NAME)
    _ensure_schema(conn)
    return conn


def insert_document(conn, source, text, embedding):
    cursor = conn.cursor()
    embedding_str = json.dumps(embedding)
    cursor.execute(
        "INSERT INTO documents (source, text, embedding) VALUES (?, ?, ?)",
        (source, text, embedding_str)
    )
    conn.commit()


def cosine_similarity(v1, v2):
    dot_product = np.dot(v1, v2)
    norm_v1 = np.linalg.norm(v1)
    norm_v2 = np.linalg.norm(v2)
    if norm_v1 == 0 or norm_v2 == 0:
        return 0.0
    return float(dot_product / (norm_v1 * norm_v2))


def search_similar_chunks(conn, query_embedding, top_k=3, threshold=0.0):
    cursor = conn.cursor()
    cursor.execute("SELECT id, source, text, embedding FROM documents")
    rows = cursor.fetchall()

    results = []
    for row in rows:
        doc_id, source, text, emb_str = row
        try:
            embedding = json.loads(emb_str)
            score = cosine_similarity(query_embedding, embedding)
            if score >= threshold:
                results.append({
                    "id": doc_id,
                    "source": source if source else "Bilinmeyen Kaynak",
                    "text": text,
                    "score": score
                })
        except Exception:
            continue

    results.sort(key=lambda x: x["score"], reverse=True)
    return results[:top_k]


def count_documents(conn):
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM documents")
    return cursor.fetchone()[0]


def add_favorite_country(conn, country):
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO favorites (country) VALUES (?)", (country,))
    conn.commit()


def get_favorite_countries(conn):
    cursor = conn.cursor()
    cursor.execute("SELECT country FROM favorites ORDER BY country")
    return [row[0] for row in cursor.fetchall()]


def save_trip_plan(conn, country, days, request, plan_text):
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO trip_plans (country, days, request, plan_text) VALUES (?, ?, ?, ?)",
        (country, days, request, plan_text),
    )
    conn.commit()


def get_trip_plans(conn, limit=10):
    cursor = conn.cursor()
    cursor.execute(
        "SELECT country, days, request, plan_text, created_at FROM trip_plans ORDER BY id DESC LIMIT ?",
        (limit,),
    )
    return cursor.fetchall()


def remove_favorite_country(conn, country):
    cursor = conn.cursor()
    cursor.execute("DELETE FROM favorites WHERE country = ?", (country,))
    conn.commit()


def add_favorite_restaurant(conn, place_name, address, country, maps_url, place_id=None):
    cursor = conn.cursor()
    cursor.execute(
        "INSERT OR IGNORE INTO favorite_restaurants (place_name, address, country, maps_url, place_id) VALUES (?, ?, ?, ?, ?)",
        (place_name, address, country, maps_url, place_id),
    )
    conn.commit()


def get_favorite_restaurants(conn):
    cursor = conn.cursor()
    cursor.execute("SELECT place_name, address, country, maps_url, place_id FROM favorite_restaurants ORDER BY id DESC")
    return cursor.fetchall()


def remove_favorite_restaurant(conn, place_id):
    cursor = conn.cursor()
    cursor.execute("DELETE FROM favorite_restaurants WHERE place_id = ?", (place_id,))
    conn.commit()


def add_visited_country(conn, country):
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO visited_countries (country) VALUES (?)", (country,))
    conn.commit()


def get_visited_countries(conn):
    cursor = conn.cursor()
    cursor.execute("SELECT country FROM visited_countries ORDER BY country")
    return [row[0] for row in cursor.fetchall()]


def remove_visited_country(conn, country):
    cursor = conn.cursor()
    cursor.execute("DELETE FROM visited_countries WHERE country = ?", (country,))
    conn.commit()


def debug_schema_info(conn):
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(documents)")
    columns = [row[1] for row in cursor.fetchall()]
    return {"db_path": DB_NAME, "columns": columns}