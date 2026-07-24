import sqlite3
import requests
from bs4 import BeautifulSoup
# pyrefly: ignore [missing-import]
from sentence_transformers import SentenceTransformer
import numpy as np

# ---------------------------------------------------------
# CONFIGURATION (AYARLAR)
# ---------------------------------------------------------
DB_NAME = "travel_rag.db"
MODEL_NAME = "paraphrase-multilingual-MiniLM-L12-v2"

print("Embedding modeli yükleniyor... (İlk seferde birkaç dakika sürebilir)")
model = SentenceTransformer(MODEL_NAME)
print("Model başarıyla yüklendi!\n")


# ---------------------------------------------------------
# 1. VERİTABANI İLKLENDİRME
# ---------------------------------------------------------
def init_db():
    """Gerekli SQLite tablosunu yoksa oluşturur."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS document_chunks(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        source TEXT,
        chunk TEXT,
        embedding BLOB
    )
    """)

    conn.commit()
    conn.close()
    print("[Veritabanı] SQLite veritabanı hazırlandı.")


# ---------------------------------------------------------
# 2. WIKIPEDIA KAZIMA (SCRAPING)
# ---------------------------------------------------------
def scrape_wikipedia(url):
    """Wikipedia sayfasındaki başlık, paragraf ve listeleri temiz bir metin haline getirir."""
    # Güvenlik duvarına takılmamak için tarayıcı taklidi yapıyoruz
    headers = {
        "User-Agent": "AITravelPlanner/1.0 (iletisim@tasarimcinindomaini.com)"
    }

    print(f"[Scraper] Sayfa indiriliyor: {url}")
    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        raise Exception(f"Sayfa indirilemedi! HTTP Hata Kodu: {response.status_code}")

    soup = BeautifulSoup(response.text, "html.parser")
    article = soup.find("div", class_="mw-parser-output")

    if article is None:
        raise Exception("Makale içeriği ('mw-parser-output') bulunamadı!")

    text = []
    
    # Sayfanın ana başlığını ekleyelim
    main_title = soup.find("h1", id="firstHeading")
    if main_title:
        text.append(f"Konu: {main_title.get_text(strip=True)}\n")

    # h2, h3, p ve li etiketlerini sırayla okuyoruz
    all_elements = article.find_all(["h2", "h3", "p", "li"])
    
    for tag in all_elements:
        # Başlıkları yakala ve temizle
        if tag.name in ["h2", "h3"]:
            title = tag.get_text(" ", strip=True)
            if "[değiştir" in title:
                title = title.split("[")[0].strip()
            if title and not title.lower() in ["kaynakça", "dış bağlantılar", "notlar"]:
                text.append(f"\n--- {title} ---\n")

        # Paragrafları yakala (Karakter sınırını 15 yaptık ki kısa önemli cümleler kaçmasın)
        elif tag.name == "p":
            paragraph = tag.get_text(" ", strip=True)
            if len(paragraph) > 15:
                text.append(paragraph)

        # Liste elemanlarını yakala (Önemli müze detayları, açılış saatleri genelde listedir)
        elif tag.name == "li":
            li_text = tag.get_text(" ", strip=True)
            # Dipnot yönlendirmelerini (^[1] gibi) ve çok kısa menü elemanlarını eliyoruz
            if len(li_text) > 15 and not li_text.startswith("^"):
                text.append(f"- {li_text}")

    return "\n".join(text)


# ---------------------------------------------------------
# 3. METNİ CHUNKLARA BÖLME
# ---------------------------------------------------------
def chunk_text(text, chunk_size=450):
    """Metni belirlenen karakter boyutunda parçalara (chunk) böler."""
    if not text:
        return []
    
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start = end
    return chunks


# ---------------------------------------------------------
# 4. EMBEDDING (VEKTÖR) ÜRETME
# ---------------------------------------------------------
def create_embeddings(chunks):
    """Her bir metin parçası için vektör üretir."""
    if not chunks:
        return []
    print(f"[Embedding] {len(chunks)} adet parça için vektör hesaplanıyor...")
    embeddings = model.encode(chunks)
    return embeddings


# ---------------------------------------------------------
# 5. VERİTABANINA KAYDETME
# ---------------------------------------------------------
def save_to_db(source, chunks, embeddings):
    """Metin parçalarını ve vektörlerini SQLite veritabanına kaydeder."""
    if not chunks:
        print("[Hata] Kaydedilecek veri bulunamadı!")
        return

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    for chunk, emb in zip(chunks, embeddings):
        # Vektörü SQLite'ta saklamak için float32 byte formatına çeviriyoruz
        emb_bytes = np.array(emb, dtype=np.float32).tobytes()
        
        cursor.execute("""
        INSERT INTO document_chunks(source, chunk, embedding)
        VALUES (?, ?, ?)
        """, (source, chunk, emb_bytes))

    conn.commit()
    conn.close()
    print(f"[Veritabanı] {len(chunks)} adet kayıt başarıyla SQLite'a yazıldı.")


# ---------------------------------------------------------
# 6. ANA AKIŞ (PIPELINE)
# ---------------------------------------------------------
def add_wikipedia_page(url):
    print("\n" + "="*40)
    print("=== WIKIPEDIA RAG YÜKLEME BAŞLADI ===")
    print("="*40)
    
    try:
        # Step 1: Web kazıma
        text = scrape_wikipedia(url)
        print(f"[Başarılı] Web kazıma tamamlandı. Toplam Karakter: {len(text)}")
        
        if len(text) == 0:
            print("[Hata] Sayfadan anlamlı hiçbir metin çekilemedi!")
            return

        # Step 2: Chunking (Parçalama)
        chunks = chunk_text(text)
        print(f"[Başarılı] Metin parçalandı. Toplam Chunk Sayısı: {len(chunks)}")

        # Step 3: Vektör oluşturma
        embeddings = create_embeddings(chunks)

        # Step 4: Veritabanına yazma
        save_to_db(url, chunks, embeddings)
        print("\n=== TÜM SÜREÇ BAŞARIYLA TAMAMLANDI ===\n")
        
    except Exception as e:
        print(f"\n[HATA] İşlem sırasında bir hata oluştu: {str(e)}\n")


# ---------------------------------------------------------
# ÇALIŞTIRMA
# ---------------------------------------------------------
if __name__ == "__main__":
    # Veritabanını hazırla
    init_db()

    # Örnek Hedef URL (Picasso Müzesi Paris)
    target_url ="https://tr.wikipedia.org/wiki/Picasso_M%C3%BCzesi_(Paris)"
       target url= "https://tr.wikipedia.org/wiki/Carnavalet_M%C3%BCzesi",
       "https://tr.wikipedia.org/wiki/Picasso_M%C3%BCzesi_(Paris)"
       "https://tr.wikipedia.org/wiki/Louvre_M%C3%BCzesi"
       "https://tr.wikipedia.org/wiki/Paris",
       "https://tr.wikipedia.org/wiki/Fransa",
       "https://tr.wikipedia.org/wiki/Notre_Dame_Katedrali",
       "https://tr.wikipedia.org/wiki/Champs-%C3%89lys%C3%A9es",
       "https://tr.wikipedia.org/wiki/Eyfel_Kulesi",
       "https://tr.wikipedia.org/wiki/Marsilya",
       "https://gezipgordum.com/marsilya-gezilecek-yerler/",
       "https://nasilgezdim.net/2018/11/23/toulouse-gezi-rehberi-ve-toulouse-gezilecek-yerler/",
       "https://www.enuygun.com/bilgi/en-guzel-fransa-sehirleri/",
       "https://www.tripadvisor.com.tr/Restaurants-g187147-Paris_Ile_de_France.html",
       "https://www.tripadvisor.com.tr/Restaurants-g187253-Marseille_Bouches_du_Rhone_Provence_Alpes_Cote_d_Azur.html",
       "https://www.tripadvisor.com.tr/Attractions-g187265-Activities-Lyon_Rhone_Auvergne_Rhone_Alpes.html",
       "https://www.tripadvisor.com.tr/Restaurants-g187265-Lyon_Rhone_Auvergne_Rhone_Alpes.html",
       "https://www.tripadvisor.com.tr/Restaurants-g187175-Toulouse_Haute_Garonne_Occitanie.html",
       "https://www.tripadvisor.com.tr/Attractions-g187234-Activities-Nice_French_Riviera_Cote_d_Azur_Provence_Alpes_Cote_d_Azur.html",
       "https://www.tripadvisor.com.tr/Restaurants-g187234-Nice_French_Riviera_Cote_d_Azur_Provence_Alpes_Cote_d_Azur.html",
       "https://www.tripadvisor.com.tr/Attractions-g187198-Activities-Nantes_Loire_Atlantique_Pays_de_la_Loire.html",
       "https://www.tripadvisor.com.tr/Restaurants-g187198-Nantes_Loire_Atlantique_Pays_de_la_Loire.html",
       "https://www.tripadvisor.com.tr/Attractions-g187075-Activities-Strasbourg_Bas_Rhin_Grand_Est.html",
       "https://www.tripadvisor.com.tr/Restaurants-g187075-Strasbourg_Bas_Rhin_Grand_Est.html",
       "https://www.tripadvisor.com.tr/Attractions-g187153-Activities-Montpellier_Herault_Occitanie.html",
       "https://www.tripadvisor.com.tr/Restaurants-g187153-Montpellier_Herault_Occitanie.html",
       "https://www.tripadvisor.com.tr/Tourism-g187079-Bordeaux_Gironde_Nouvelle_Aquitaine-Vacations.html",
       "https://www.tripadvisor.com.tr/Restaurants-g187079-Bordeaux_Gironde_Nouvelle_Aquitaine.html",
       "https://www.tripadvisor.com.tr/Attractions-g187221-Activities-Cannes_French_Riviera_Cote_d_Azur_Provence_Alpes_Cote_d_Azur.html",
       "https://www.tripadvisor.com.tr/Restaurants-g187221-Cannes_French_Riviera_Cote_d_Azur_Provence_Alpes_Cote_d_Azur.html",
       "https://www.tripadvisor.com.tr/Attractions-g187178-Activities-Lille_Nord_Hauts_de_France.html",
       "https://www.tripadvisor.com.tr/Restaurants-g187178-Lille_Nord_Hauts_de_France.html",
       "https://www.tripadvisor.com.tr/Attractions-g187103-Activities-Rennes_Ille_et_Vilaine_Brittany.html",
       "https://www.tripadvisor.com.tr/Restaurants-g187103-Rennes_Ille_et_Vilaine_Brittany.html",
       "https://www.tripadvisor.com.tr/Attractions-g187137-Activities-Reims_Marne_Grand_Est.html",
       "https://www.tripadvisor.com.tr/Restaurants-g187137-Reims_Marne_Grand_Est.html",
       "https://www.tripadvisor.com.tr/Attractions-g187269-Activities-Saint_Etienne_Loire_Auvergne_Rhone_Alpes.html",
       "https://www.tripadvisor.com.tr/Restaurants-g187269-Saint_Etienne_Loire_Auvergne_Rhone_Alpes.html",
       "https://www.tripadvisor.com.tr/Attractions-g187190-Activities-Le_Havre_Seine_Maritime_Haute_Normandie_Normandy.html",
       "https://www.tripadvisor.com.tr/Restaurants-g187190-Le_Havre_Seine_Maritime_Haute_Normandie_Normandy.html",
       "https://www.tripadvisor.com.tr/Attractions-g187257-Activities-Toulon_Var_Provence_Alpes_Cote_d_Azur.html",
       "https://www.tripadvisor.com.tr/Restaurants-g187257-Toulon_Var_Provence_Alpes_Cote_d_Azur.html",
       "https://www.tripadvisor.com.tr/Attractions-g187264-Activities-Grenoble_Isere_Auvergne_Rhone_Alpes.html",
       "https://www.tripadvisor.com.tr/Restaurants-g187264-Grenoble_Isere_Auvergne_Rhone_Alpes.html",
       "https://www.tripadvisor.com.tr/Attractions-g187111-Activities-Dijon_Cote_d_Or_Bourgogne_Franche_Comte.html","https://www.tripadvisor.com.tr/Restaurants-g187111-Dijon_Cote_d_Or_Bourgogne_Franche_Comte.html","https://www.tripadvisor.com.tr/Attractions-g187197-Activities-Angers_Maine_et_Loire_Pays_de_la_Loire.html","https://www.tripadvisor.com.tr/Restaurants-g187197-Angers_Maine_et_Loire_Pays_de_la_Loire.html","https://www.tripadvisor.com.tr/Attractions-g187154-Activities-Nimes_Gard_Occitanie.html","https://www.tripadvisor.com.tr/Restaurants-g187154-Nimes_Gard_Occitanie.html","https://www.tripadvisor.com.tr/Attractions-g187091-Activities-Clermont_Ferrand_Puy_de_Dome_Auvergne_Rhone_Alpes.html","https://www.tripadvisor.com.tr/Restaurants-g187091-Clermont_Ferrand_Puy_de_Dome_Auvergne_Rhone_Alpes.html","https://www.tripadvisor.com.tr/Attractions-g187195-Activities-Le_Mans_City_Le_Mans_Sarthe_Pays_de_la_Loire.html","https://www.tripadvisor.com.tr/Restaurants-g187195-Le_Mans_City_Le_Mans_Sarthe_Pays_de_la_Loire.html","https://www.tripadvisor.com.tr/Attractions-g187209-Activities-Aix_en_Provence_Bouches_du_Rhone_Provence_Alpes_Cote_d_Azur.html","https://www.tripadvisor.com.tr/Restaurants-g187209-Aix_en_Provence_Bouches_du_Rhone_Provence_Alpes_Cote_d_Azur.html","https://www.tripadvisor.com.tr/Tourism-g187095-Brest_Finistere_Brittany-Vacations.html","https://www.tripadvisor.com.tr/Restaurants-g187095-Brest_Finistere_Brittany.html","https://www.tripadvisor.com.tr/Attractions-g187159-Activities-Limoges_Haute_Vienne_Nouvelle_Aquitaine.html","https://www.tripadvisor.com.tr/Restaurants-g187159-Limoges_Haute_Vienne_Nouvelle_Aquitaine.html","https://www.tripadvisor.com.tr/Attractions-g187130-Activities-Tours_Indre_et_Loire_Centre_Val_de_Loire.html","https://www.tripadvisor.com.tr/Restaurants-g187130-Tours_Indre_et_Loire_Centre_Val_de_Loire.html","https://www.tripadvisor.com.tr/Attractions-g196657-Activities-Amiens_Somme_Hauts_de_France.html","https://www.tripadvisor.com.tr/Restaurants-g196657-Amiens_Somme_Hauts_de_France.html","https://www.tripadvisor.com.tr/Attractions-g187164-Activities-Metz_Moselle_Grand_Est.html","https://www.tripadvisor.com.tr/Restaurants-g187164-Metz_Moselle_Grand_Est.html","https://www.tripadvisor.com.tr/Attractions-g187143-Activities-Besancon_Doubs_Bourgogne_Franche_Comte.html","https://www.tripadvisor.com.tr/Restaurants-g187143-Besancon_Doubs_Bourgogne_Franche_Comte.html","https://www.tripadvisor.com.tr/Restaurants-g187156-Perpignan_Pyrenees_Orientales_Occitanie.html","https://www.tripadvisor.com.tr/Attractions-g187156-Activities-Perpignan_Pyrenees_Orientales_Occitanie.html","https://www.tripadvisor.com.tr/Tourism-g293969-Turkiye-Vacations.html","https://www.tripadvisor.com.tr/Attractions-g293969-Activities-Turkiye.html","https://www.tripadvisor.com.tr/Restaurants-g293969-Turkiye.html","https://www.tripadvisor.com.tr/Restaurants-g297962-Antalya_Turkish_Mediterranean_Coast.html","https://www.tripadvisor.com.tr/Attractions-g297962-Activities-Antalya_Turkish_Mediterranean_Coast.html","https://www.tripadvisor.com.tr/Attractions-g2557813-Activities-Ist_Zadar_County_Dalmatia.html","https://www.tripadvisor.com.tr/Restaurants-g2557813-Ist_Zadar_County_Dalmatia.html","https://www.tripadvisor.com.tr/Tourism-g298006-Izmir_Izmir_Province_Turkish_Aegean_Coast-Vacations.html","https://www.tripadvisor.com.tr/Attractions-g298006-Activities-Izmir_Izmir_Province_Turkish_Aegean_Coast.html","https://www.tripadvisor.com.tr/Restaurants-g298006-Izmir_Izmir_Province_Turkish_Aegean_Coast.html","https://www.tripadvisor.com.tr/Attractions-g298656-Activities-Ankara.html","https://www.tripadvisor.com.tr/Restaurants-g298656-Ankara.html","https://www.tripadvisor.com.tr/Attractions-g297977-Activities-Bursa.html","https://www.tripadvisor.com.tr/Restaurants-g297977-Bursa.html","https://www.tripadvisor.com.tr/Attractions-g298039-Activities-Trabzon_Ortahisar_Turkish_Black_Sea_Coast.html","https://www.tripadvisor.com.tr/Restaurants-g298039-Trabzon_Ortahisar_Turkish_Black_Sea_Coast.html","https://www.tripadvisor.com.tr/Attractions-g1221512-Activities-Mugla_Mugla_Province_Turkish_Aegean_Coast.html","https://www.tripadvisor.com.tr/Restaurants-g1221512-Mugla_Mugla_Province_Turkish_Aegean_Coast.html"
       "https://www.tripadvisor.com.tr/Attractions-g297986-Activities-Nevsehir_Nevsehir_Province_Cappadocia.html",
       "https://www.tripadvisor.com.tr/Restaurants-g297986-Nevsehir_Nevsehir_Province_Cappadocia.html",
       "https://www.tripadvisor.com.tr/Attractions-g672951-Activities-Mardin_Mardin_Province.html",
       "https://www.tripadvisor.com.tr/Restaurants-g672951-Mardin_Mardin_Province.html",
       "https://www.tripadvisor.com.tr/Attractions-g319806-Activities-Eskisehir_Eskisehir_Province.html",
       "https://www.tripadvisor.com.tr/Restaurants-g319806-Eskisehir_Eskisehir_Province.html",
       "https://www.tripadvisor.com.tr/Attractions-g297979-Activities-Canakkale_Canakkale_Province_Turkish_Aegean_Coast.html",
       "https://www.tripadvisor.com.tr/Restaurants-g297979-Canakkale_Canakkale_Province_Turkish_Aegean_Coast.html",
       "https://www.tripadvisor.com.tr/Attractions-g298031-Activities-Fethiye_Mugla_Province_Turkish_Aegean_Coast.html"
       "https://tr.wikipedia.org/wiki/%C4%B0spanya",
       "https://tr.wikipedia.org/wiki/Romanya",


    
       
       ]
    
       
    # Süreci başlat
    add_wikipedia_page(target_url)