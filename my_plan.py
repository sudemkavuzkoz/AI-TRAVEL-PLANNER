import sqlite3
import numpy as np
from sentence_transformers import SentenceTransformer
from model import generate_response

def get_db_connection():
    conn = sqlite3.connect("travel_rag.db")
    conn.row_factory = sqlite3.Row
    return conn

def main():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM countries WHERE name = 'country_turkey'")
    country_row = cursor.fetchone()
    if not country_row:
        print("Hata: Türkiye veritabanında bulunamadı!")
        return
    country_id = country_row["id"]
    
    user_query = "Veri setindeki bilgileri kullanarak Türkiye için bir tatil ve rota planı yap. Planı yaparken hangi bölgelerde nelerin güzel olduğunu ('şurada bu güzeldir' gibi) özellikle belirt ve detaylandır."
    
    embedding_model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2", device='cpu')
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
    top_chunks = scored_chunks[:20] # Daha kapsamlı bilgi için chunk sayısını 5'ten 20'ye çıkardık
    
    context_str = "\n".join([c[1] for c in top_chunks])
    
    system_prompt = (
        "Sen profesyonel ve son derece detaycı bir seyahat asistanısın. Sağlanan 'Context' (Bağlam) bilgilerini kullanarak kullanıcıya GÜN GÜN veya BÖLGE BÖLGE ayrılmış, ÇOK KAPSAMLI ve UZUN bir tatil/rota planı oluştur. "
        "Kullanıcıya rota planı yaparken 'şurada bu güzeldir', 'buranın şu yemeği meşhurdur' şeklinde veri setinden aldığın bilgileri kullanarak bolca öneride bulun. "
        "Sadece Context'te olan bilgileri kullan, dışarıdan bilgi uydurma. Ancak bulduğun tüm detayları (mekanlar, plajlar, tarihi yerler) yanıtına ekle. "
        "LÜTFEN YANITINI TAMAMEN TÜRKÇE (TURKISH) DİLİNDE VER."
    )
    user_prompt = f"Context:\n{context_str}\n\nQuestion:\n{user_query}"
    
    print("Yanıt üretiliyor...")
    response = generate_response(user_prompt, system_prompt=system_prompt, history=[])
    print("\n--- ÜRETİLEN PLAN ---")
    print(response)

if __name__ == "__main__":
    main()
