import os
import sys
import glob
from pathlib import Path

from travel_extractor import collect_gezipgordum_country_files
from embedding import create_embeddings, _get_model
from database import init_db, insert_document


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


def import_country_files(folder="travel_data", limit=None):
    txt_files = sorted(glob.glob(os.path.join(folder, "country_*.txt")))
    if limit:
        txt_files = txt_files[:limit]
    if not txt_files:
        print("Hiç ülke dosyası bulunamadı. Önce collect_gezipgordum_country_files() çalıştırın.")
        return 0

    print(f"Toplam {len(txt_files)} ülke dosyası bulundu. Embedding işlemi başlıyor...")
    _get_model()
    conn = init_db()
    all_chunks = []
    for filepath in txt_files:
        source_url, text = read_file(filepath)
        if not text:
            continue
        chunks = chunk_text(text)
        for chunk in chunks:
            all_chunks.append((source_url, chunk))
    if not all_chunks:
        print("Hiç metin parçası üretilemedi.")
        return 0
    texts = [chunk for _, chunk in all_chunks]
    sources = [src for src, _ in all_chunks]
    embeddings = create_embeddings(texts)
    for source, chunk, emb in zip(sources, texts, embeddings):
        insert_document(conn, source, chunk, emb)
    conn.commit()
    conn.close()
    print(f"{len(all_chunks)} kayıt veritabanına eklendi.")
    return len(all_chunks)


if __name__ == "__main__":
    files = collect_gezipgordum_country_files(output_dir="travel_data", max_results=20)
    print("Oluşturulan dosyalar:", files)
    import_country_files(folder="travel_data")
