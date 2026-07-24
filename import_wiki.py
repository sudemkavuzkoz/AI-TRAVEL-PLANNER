import os
import glob
import time

from embedding import create_embeddings, _get_model
from database import init_db, insert_document

DATA_DIR = "travel_data"

def chunk_text(text, chunk_size=500):
    if not text:
        return []
    chunks = []
    start = 0
    while start < len(text):
        chunks.append(text[start:start + chunk_size])
        start += chunk_size
    return chunks

def read_file(filepath):
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()

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
    except Exception as e:
        print(f"[Hata] {os.path.basename(filepath)} okunamadi: {e}")
        return None, None

if __name__ == "__main__":
    if not os.path.exists(DATA_DIR):
        print(f"HATA: '{DATA_DIR}' klasoru bulunamadi!")
    else:
        txt_files = glob.glob(os.path.join(DATA_DIR, "*.txt"))
        total = len(txt_files)
        print(f"Toplam {total} dosya bulundu. Embedding islemi basliyor...\n")

        _get_model()

        start_time = time.time()
        conn = init_db()
        
        all_chunks = []
        for i, filepath in enumerate(txt_files, 1):
            source_url, text = read_file(filepath)
            if not text:
                continue
            chunks = chunk_text(text)
            for chunk in chunks:
                all_chunks.append((source_url, chunk))
            print(f"  [{i}/{total}] Okundu: {os.path.basename(filepath)} ({len(chunks)} parca)")

        print(f"\nToplam {len(all_chunks)} metin parcasi var. Embedding uretiliyor...")

        texts = [chunk for _, chunk in all_chunks]
        sources = [src for src, _ in all_chunks]
        embeddings = create_embeddings(texts)

        print("Veritabanina kaydediliyor...")
        for source, chunk, emb in zip(sources, texts, embeddings):
            insert_document(conn, source, chunk, emb)

        conn.commit()
        conn.close()

        elapsed = time.time() - start_time
        print(f"\n=== TAMAMLANDI! {len(all_chunks)} kayit aktarildi. (Sure: {elapsed:.1f} saniye) ===")