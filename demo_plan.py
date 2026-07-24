import sqlite3
import numpy as np
from sentence_transformers import SentenceTransformer
from model import generate_response_stream

def get_db_connection():
    conn = sqlite3.connect("travel_rag.db")
    conn.row_factory = sqlite3.Row
    return conn

def main():
    print("AI Travel Planner Testi Başlıyor (Phi-4 Mini + RAG)...")
    
    # Türkiye'nin ID'sini bul
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM countries WHERE name = 'country_turkey'")
    country_row = cursor.fetchone()
    if not country_row:
        print("Hata: Türkiye veritabanında bulunamadı!")
        return
    country_id = country_row["id"]
    
    user_query = "Bana Türkiye'de 3 günlük detaylı bir tatil planı yap. Kazıdığın yöresel yemekleri (Adana Kebap, Baklava vs.) ve tarihi yerleri (Göbeklitepe vb.) mutlaka ekle."
    print(f"\nSoru: {user_query}")
    print("Embedding Modeli yükleniyor...")
    embedding_model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2", device='cpu')
    
    print("RAG: Vektör araması yapılıyor...")
    query_vector = embedding_model.encode(user_query, normalize_embeddings=True).astype(np.float32)
    
    cursor.execute("SELECT chunk_text, embedding, source FROM document_chunks WHERE country_id = ?", (country_id,))
    rows = cursor.fetchall()
    
    scored_chunks = []
    for row in rows:
        vector = np.frombuffer(row["embedding"], dtype=np.float32)
        similarity = float(np.dot(vector, query_vector))
        if similarity >= 0.05:
            scored_chunks.append((similarity, row["chunk_text"], row["source"]))
            
    conn.close()
    
    scored_chunks.sort(key=lambda x: x[0], reverse=True)
    top_chunks = scored_chunks[:3] # En iyi 3 context'i al
    
    context_str = "\n".join([c[1] for c in top_chunks])
    print("\n--- BULUNAN RAG VERİLERİ (CONTEXT) ---")
    print(context_str[:500] + "...\n(Devamı var)\n")
    
    system_prompt = (
        "You are a travel assistant. Create engaging itineraries strictly using the provided 'Context'. "
        "If context lacks info, say 'Veri setimde yok.' Include [📍 Name](https://www.google.com/maps/search/?api=1&query=Name) for places."
    )
    user_prompt = f"Context:\n{context_str}\n\nQuestion:\n{user_query}"
    
    print("Phi-4 Mini (CPU) Yanıt Üretiyor (Lütfen bekleyin, CPU üzerinde çalıştığı için yavaş olabilir)...\n")
    print("="*50)
    
    # Yanıtı stream olarak yazdır
    stream = generate_response_stream(user_prompt, system_prompt, history=[])
    for chunk in stream:
        print(chunk, end="", flush=True)
        
    print("\n" + "="*50)
    print("\nTest Tamamlandı!")

if __name__ == "__main__":
    main()
