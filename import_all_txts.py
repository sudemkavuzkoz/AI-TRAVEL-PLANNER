import os
import glob
import sqlite3
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

def read_txt_file(filepath):
    with open(filepath, "r", encoding="utf-8") as handle:
        content = handle.read()
    
    # Try to parse metadata block if exists
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

def import_all_txt_files(folder="travel_data"):
    files = sorted(glob.glob(os.path.join(folder, "*.txt")))
    if not files:
        print("Hiç .txt dosyası bulunamadı.")
        return 0

    print(f"Toplam {len(files)} adet .txt dosyası bulundu. İşlem başlıyor...")
    
    conn = init_db()
    cursor = conn.cursor()
    
    print("Mevcut veritabanı temizleniyor (Eski kayıtlar siliniyor)...")
    cursor.execute("DELETE FROM documents;")
    conn.commit()

    all_rows = []
    for filepath in files:
        print(f"Okunuyor: {os.path.basename(filepath)}")
        source_url, text = read_txt_file(filepath)
        if not text:
            continue
        for chunk in chunk_text(text):
            all_rows.append((source_url, chunk))

    if not all_rows:
        conn.close()
        print("Hiç metin verisi bulunamadı.")
        return 0

    print(f"Toplam {len(all_rows)} chunk oluşturuldu. Vektörler (embeddings) hesaplanıyor...")
    
    # Vektörleri hesapla (Bu işlem biraz sürebilir)
    embeddings = create_embeddings(texts=[chunk for _, chunk in all_rows])
    
    print("Veritabanına kaydediliyor...")
    for (source_url, chunk), emb in zip(all_rows, embeddings):
        insert_document(conn, source_url, chunk, emb)

    conn.commit()
    conn.close()
    
    print(f"Başarılı! {len(all_rows)} adet veri başarıyla veritabanına kaydedildi.")
    return len(all_rows)

if __name__ == "__main__":
    import_all_txt_files(folder="travel_data")
