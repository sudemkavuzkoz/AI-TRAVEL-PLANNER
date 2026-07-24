import os
import glob
import json
import sqlite3
from pathlib import Path

from embedding import create_embeddings
from database import init_db, insert_document

CHUNK_SIZE = 700


def chunk_text(text, chunk_size=CHUNK_SIZE):
    if not text:
        return []
    chunks = []
    start = 0
    while start < len(text):
        chunk = text[start:start + chunk_size]
        if not chunk.strip():
            break
        chunks.append(chunk)
        start += chunk_size
    return chunks


def read_country_file(filepath):
    with open(filepath, "r", encoding="utf-8") as handle:
        content = handle.read()
    parts = content.split("----------------", 1)
    if len(parts) == 2:
        metadata_block = parts[0]
        text = parts[1].strip()
        source_url = os.path.basename(filepath)
        for line in metadata_block.split("\n"):
            if line.strip().startswith("SOURCE_URL:"):
                source_url = line.split("SOURCE_URL:", 1)[1].strip()
                break
    else:
        text = content.strip()
        source_url = os.path.basename(filepath)
    return source_url, text


def import_chunked_country_files(folder="travel_data", limit=None):
    files = sorted(glob.glob(os.path.join(folder, "country_*.txt")))
    if limit:
        files = files[:limit]
    if not files:
        print("Hiç ülke dosyası bulunamadı.")
        return 0

    conn = init_db()
    all_rows = []
    for filepath in files:
        source_url, text = read_country_file(filepath)
        if not text:
            continue
        for chunk in chunk_text(text):
            all_rows.append((source_url, chunk))

    if not all_rows:
        conn.close()
        return 0

    texts = [chunk for _, chunk in all_rows]
    embeddings = create_embeddings(texts)
    for (source_url, chunk), emb in zip(all_rows, embeddings):
        insert_document(conn, source_url, chunk, emb)

    conn.commit()
    conn.close()
    print(f"{len(all_rows)} chunk eklendi.")
    return len(all_rows)


if __name__ == "__main__":
    import_chunked_country_files(folder="travel_data")
