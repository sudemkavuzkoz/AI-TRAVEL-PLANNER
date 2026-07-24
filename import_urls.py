import os
import glob
import time
import argparse
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


def import_files_from_folder(folder=DATA_DIR):
    if not os.path.exists(folder):
        print(f"HATA: '{folder}' klasoru bulunamadi!")
        return
    txt_files = glob.glob(os.path.join(folder, "*.txt"))
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


def import_single_url(url):
    print(f"URL işleniyor: {url}")
    # Basit bir URL metin yükleyici. Gerçek üretimde web scraper eklenebilir.
    from urllib.request import Request, urlopen
    request = Request(url, headers={"User-Agent": "Mozilla/5.0"})
    html = urlopen(request).read().decode("utf-8", errors="ignore")
    return html


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="URL ve txt dosyalarını RAG veritabanına aktar")
    parser.add_argument("--url", help="Tek bir URL yüklemek için")
    parser.add_argument("--folder", default=DATA_DIR, help="TXT dosyalarının klasörü")
    args = parser.parse_args()
    if args.url:
        import_single_url(args.url)
    else:
        import_files_from_folder(args.folder)
