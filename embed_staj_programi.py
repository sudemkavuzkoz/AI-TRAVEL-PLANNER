import os
import sqlite3
import numpy as np
import json
from sentence_transformers import SentenceTransformer

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(BASE_DIR, "travel_rag.db")
DATA_FILE = os.path.join(BASE_DIR, "travel_data", "microsoft_staj_programi.txt")

print("Yükleniyor...")
embedding_model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")

def chunk_text(text, chunk_size=500):
    if not text:
        return []
    chunks = []
    start = 0
    while start < len(text):
        chunks.append(text[start:start + chunk_size])
        start += chunk_size
    return chunks

def run():
    print("Veri dosyası okunuyor...")
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        content = f.read()
    
    chunks = chunk_text(content)
    if not chunks:
        print("İçerik bulunamadı.")
        return
        
    print(f"{len(chunks)} parça için embedding oluşturuluyor...")
    chunk_embeddings = embedding_model.encode(chunks, normalize_embeddings=True, convert_to_numpy=True).astype(np.float32)
    
    print(f"SQLite veritabanına bağlanılıyor: {DB_FILE}...")
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    # 1. document_chunks tablosuna ekle (app.py için)
    country_name = "Microsoft Staj Programı"
    try:
        cursor.execute("SELECT id FROM countries WHERE name = ?", (country_name,))
        row = cursor.fetchone()
        if not row:
            cursor.execute("INSERT INTO countries (name, code, lat, lon) VALUES (?, ?, ?, ?)", (country_name, "MSP", 0.0, 0.0))
            country_id = cursor.lastrowid
        else:
            country_id = row[0]
            
        print(f"Ülke/Proje ID: {country_id}")
        
        cursor.execute("DELETE FROM document_chunks WHERE country_id = ? AND source = ?", (country_id, "microsoft_staj_programi.txt"))
        
        for idx, (chunk, vector) in enumerate(zip(chunks, chunk_embeddings)):
            cursor.execute("""
                INSERT INTO document_chunks (country_id, source, chunk_index, chunk_text, embedding)
                VALUES (?, ?, ?, ?, ?)
            """, (country_id, "microsoft_staj_programi.txt", idx, chunk, vector.tobytes()))
            
        print("document_chunks tablosu güncellendi.")
    except sqlite3.Error as e:
        print(f"document_chunks güncellenirken hata oluştu: {e}")

    # 2. documents tablosuna ekle (database.py / eski yapı için)
    try:
        cursor.execute("DELETE FROM documents WHERE source = ?", ("microsoft_staj_programi.txt",))
        for chunk, vector in zip(chunks, chunk_embeddings):
            embedding_list = vector.tolist()
            cursor.execute("""
                INSERT INTO documents (source, text, embedding)
                VALUES (?, ?, ?)
            """, ("microsoft_staj_programi.txt", chunk, json.dumps(embedding_list)))
        print("documents tablosu güncellendi.")
    except sqlite3.Error as e:
        print(f"documents güncellenirken hata oluştu (tablo olmayabilir): {e}")

    conn.commit()
    conn.close()
    print("Veritabanı başarıyla güncellendi!")

if __name__ == "__main__":
    run()
